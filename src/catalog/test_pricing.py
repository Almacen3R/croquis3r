import json
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from .homologation import MAPPINGS
from .pricing import manual_rows, quote, sketch_rows, template_rows
from .sql_prices import PriceSourceUnavailable, SqlPriceProvider
from sketches.house_calculator import HouseCalculatorForm, calculate_house
from sketches.house_templates import TEMPLATES, template_result
from sketches.models import Attention
from sketches.test_house_calculator import entries
from sketches.test_house_templates import original_data
from sketches.test_modulation import doc, opening, wall


CONFIG = dict(THREER_PRICING_ENABLED=True, THREER_SQL_HOST='sql.example.invalid',
    THREER_SQL_PASSWORD='test-only-secret', THREER_SQL_USER='readonly',
    THREER_SQL_DATABASE='catalog_test', THREER_SQL_SCHEMA='catalog_test',
    THREER_SQL_PRICE_LEVEL='GENERAL', THREER_SQL_CURRENCY='L', THREER_SQL_PRICE_INCLUDES_TAX=True)


def article(key='tp50', **changes):
    sku, words = MAPPINGS[key]
    return dict(sku=sku, description=' '.join(words), active='S', sale_unit='UND',
        price=Decimal('113'), tax_rate=Decimal('13'), additional_tax=Decimal('0'), version=1, **changes)


def lookup():
    return {'fetched_at': timezone.now().isoformat(),
            'articles': {sku: {**article(key), 'status': 'ready'} for key, (sku, _) in MAPPINGS.items()}}


def fake_provider():
    provider = Mock()
    provider.fetch.return_value = lookup()
    return provider


class FakeCursor:
    def __init__(self, rows, *, permission=False, currency='CRC'):
        self.rows, self.write_permission, self.currency = rows, permission, currency
        self.queries = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def execute(self, sql, params=None):
        self.queries.append((sql, params))

    def fetchone(self):
        if 'GLOBALES_AS' in self.queries[-1][0]:
            return {'currency': self.currency}
        return dict(sysadmin=0, can_select=1, can_insert=int(self.write_permission),
                    can_update=0, can_delete=0, can_control=0, can_alter=0)

    def fetchmany(self, size):
        return self.rows[:size]


@override_settings(**CONFIG)
class PriceProviderTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def provider(self, rows, **kwargs):
        self.cursor = FakeCursor(rows, **kwargs)
        self.connection = Mock()
        self.connection.cursor.return_value = self.cursor
        self.connect = Mock(return_value=self.connection)
        return SqlPriceProvider(self.connect)

    def test_select_only_parameterized_skus_encrypted_and_read_only(self):
        provider = self.provider([article()])
        result = provider.fetch({'44648'})
        self.assertEqual(result['articles']['44648']['status'], 'ready')
        self.assertTrue(self.connect.call_args.kwargs['read_only'])
        self.assertEqual(self.connect.call_args.kwargs['encryption'], 'require')
        for query, _ in self.cursor.queries:
            self.assertTrue(query.lstrip().startswith('SELECT'))
        sql, parameters = self.cursor.queries[-1]
        self.assertNotIn('44648', sql)
        self.assertEqual(parameters, ('GENERAL', 'L', '44648'))
        self.assertNotIn('PRECIO_BASE_LOCAL', sql)
        self.connection.close.assert_called_once()

    def test_duplicate_current_prices_missing_price_inactive_and_units_are_explicit(self):
        invalids = [[article(), article()], [dict(article(), price=None)],
                    [dict(article(), active='N')], [dict(article(), sale_unit='PAQ')]]
        for rows in invalids:
            with self.subTest(rows=rows):
                result = self.provider(rows).fetch({'44648'}, refresh=True)
                self.assertEqual(result['articles']['44648']['status'], 'unavailable')

    def test_real_zero_is_not_missing_and_missing_sku_is_unavailable(self):
        result = self.provider([dict(article(), price=Decimal(0))]).fetch({'44648','44649'})
        self.assertEqual(result['articles']['44648']['status'], 'ready')
        self.assertEqual(result['articles']['44649']['status'], 'unavailable')

    def test_refuses_account_with_writes_and_unexpected_currency(self):
        with self.assertRaisesRegex(PriceSourceUnavailable, 'solo consulta'):
            self.provider([article()], permission=True).fetch({'44648'})
        with self.assertRaisesRegex(PriceSourceUnavailable, 'moneda local'):
            self.provider([article()], currency='USD').fetch({'44648'})

    def test_arbitrary_skus_and_schema_cannot_be_injected(self):
        provider = self.provider([])
        with self.assertRaises(PriceSourceUnavailable):
            provider.fetch({"44648'); DROP TABLE ARTICULO;--"})
        with self.settings(THREER_SQL_SCHEMA='catalog];DROP TABLE a;--'):
            with self.assertRaises(PriceSourceUnavailable):
                provider.fetch({'44648'})
        self.connect.assert_not_called()

    def test_cache_retains_timestamp_and_refresh_requeries(self):
        provider = self.provider([article()])
        first = provider.fetch({'44648'})
        second = provider.fetch({'44648'})
        self.assertEqual(first['fetched_at'], second['fetched_at'])
        self.assertEqual(self.connect.call_count, 1)
        provider.fetch({'44648'}, refresh=True)
        self.assertEqual(self.connect.call_count, 2)

    def test_driver_failure_cannot_expose_secret_or_sql(self):
        provider = SqlPriceProvider(Mock(side_effect=RuntimeError('test-only-secret; SQL details')))
        with self.assertRaises(PriceSourceUnavailable) as error:
            provider.fetch({'44648'})
        self.assertNotIn('test-only-secret', str(error.exception))
        self.assertNotIn('SQL details', str(error.exception))


@override_settings(**CONFIG)
class QuotationTests(SimpleTestCase):
    def row(self, key='tp50', quantity=2):
        return {'key': key, 'name': key, 'quantity': quantity, 'unit': 'unidades'}

    def test_included_iva_is_decomposed_and_never_added_twice(self):
        result = quote([self.row()], fake_provider())
        self.assertEqual((result['total'], result['base_with_prices'], result['tax_with_prices']),
                         (Decimal('226'), Decimal('200'), Decimal('26')))

    def test_rounds_line_from_full_source_precision(self):
        provider = fake_provider()
        provider.fetch.return_value['articles']['44648']['price'] = Decimal('9.995')
        result = quote([self.row(quantity=3)], provider)
        self.assertEqual(result['total'], Decimal('29.99'))

    def test_pending_mapping_and_quantity_never_become_zero_or_complete_total(self):
        result = quote([self.row(), self.row('mortar', 3), self.row('column_linear', None)], fake_provider())
        self.assertEqual(result['subtotal_with_prices'], Decimal('226'))
        self.assertIsNone(result['total'])
        self.assertEqual(result['pending_count'], 2)
        self.assertTrue(all(row['amount'] is None for row in result['rows'][1:]))

    def test_source_outage_and_description_change_do_not_invent_price(self):
        provider = fake_provider()
        provider.fetch.side_effect = PriceSourceUnavailable('No disponible')
        result = quote([self.row()], provider)
        self.assertEqual(result['priced_count'], 0)
        self.assertIsNone(result['total'])
        provider.fetch.side_effect = None
        provider.fetch.return_value['articles']['44648']['description'] = 'OTRO PRODUCTO'
        self.assertEqual(quote([self.row()], provider)['priced_count'], 0)

    def test_zero_quantity_and_disabled_pricing_do_not_consult_source(self):
        provider = fake_provider()
        self.assertIsNone(quote([self.row(quantity=0)], provider))
        with self.settings(THREER_PRICING_ENABLED=False):
            self.assertIsNone(quote([self.row()], provider))
        provider.fetch.assert_not_called()

    def test_sql_column_t_means_cross_and_correct_codes_for_long_short_blocks(self):
        result = quote([self.row('tp50'),self.row('tp37'),self.row('column_linear'),self.row('column_cross')],fake_provider())
        self.assertEqual([r['sku'] for r in result['rows']], ['44648','44649','44647','51234'])

    def test_manual_adds_physical_openings_once_and_does_not_replace_panel_recipes(self):
        form = HouseCalculatorForm(entries(panel_18='1',panel_9='2'))
        self.assertTrue(form.is_valid())
        result = calculate_house(form.cleaned_data)
        quoted = quote(manual_rows(result), fake_provider())
        self.assertEqual(next(r['quantity'] for r in quoted['rows'] if r['key']=='door_2'),1)
        self.assertEqual(next(r['quantity'] for r in quoted['rows'] if r['key']=='window_regular_1.5'),2)
        self.assertEqual(result['tp50'],20)

    def test_large_and_small_openings_do_not_reuse_137cm_product_price(self):
        rows = [self.row('window_regular_2'),self.row('window_regular_1'),self.row('door_1.5'),self.row('door_3')]
        result = quote(rows,fake_provider())
        self.assertEqual(result['priced_count'],0)
        self.assertTrue(all(not row['sku'] for row in result['rows']))
        template = TEMPLATES[3]
        rows = template_rows(template_result(template,original_data(template)))
        self.assertEqual(next(r['key'] for r in rows if r['name']=='Ventana 1,875 × 1200'),'window_regular_2')


@override_settings(**CONFIG)
class PricingIntegrationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('seller_prices')
        self.client.force_login(self.user)

    @patch('catalog.pricing.SqlPriceProvider')
    def test_api_prices_computed_on_server_and_unmapped_opening_remains_pending(self, provider):
        provider.return_value = fake_provider()
        data = doc(wall(),opening(width=1,offset=1.5),linear_columns=3,t_columns=2)
        response = self.client.post('/api/ticoblock-estimate/',json.dumps({'document':data,'pricing':{'total':1}}),content_type='application/json')
        self.assertEqual(response.status_code,200)
        pricing = response.json()['pricing']
        self.assertIsNone(pricing['total'])
        self.assertEqual(next(r['status'] for r in pricing['rows'] if r['key']=='window_regular_1'),'pending')
        self.assertNotEqual(pricing['subtotal_with_prices'],'1')

    @patch('catalog.pricing.SqlPriceProvider')
    def test_attention_freezes_price_and_reopen_does_not_refresh_or_overwrite_it(self, provider):
        provider.return_value = fake_provider()
        data = entries(panel_4='1',column_mode='manual',linear_columns='2',t_columns='1',action='save')
        self.assertEqual(self.client.post('/calculador-casas/',data).status_code,302)
        record = Attention.objects.get()
        self.assertEqual(record.result['pricing']['subtotal_with_prices'],'6328.00')
        before = record.result.copy()
        provider.reset_mock()
        self.assertContains(self.client.get(f'/atenciones/{record.pk}/'),'Precios de 3R')
        provider.assert_not_called()
        record.refresh_from_db()
        self.assertEqual(record.result,before)

    @patch('catalog.pricing.SqlPriceProvider')
    def test_template_shows_pending_but_valid_prices_are_available(self, provider):
        provider.return_value = fake_provider()
        response = self.client.get('/calculador-casas/plantillas/modelo-e/')
        self.assertContains(response,'Precios de 3R')
        self.assertContains(response,'IVA incluido')
        self.assertGreater(response.context['result']['pricing']['priced_count'],0)
