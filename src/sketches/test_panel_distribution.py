import json
from decimal import Decimal

from .testing import AuthenticatedTestCase as TestCase
from django.test import Client, SimpleTestCase, override_settings

from .domain import InvalidDocument
from .house_calculator import HouseCalculatorForm, RECIPES, calculate_house
from .modulation import calculate_modulation
from .panel_distribution import suggest_panels
from .test_house_calculator import entries
from .test_modulation import doc, wall, opening


class DistributionTests(SimpleTestCase):
    def test_customer_preferences_use_selected_measure_then_smaller_exact_remainder(self):
        expected = {'2': [('2',3),('1.5',1)], '1.5':[('1.5',5)],
                    '1':[('1',7),('0.5',1)], '0.5':[('0.5',15)]}
        for preference, rows in expected.items():
            result = suggest_panels('7.5', preference)
            self.assertEqual([(r['length'],r['quantity']) for r in result['rows']], rows)

    def test_every_half_meter_up_to_limit_is_preserved_for_all_preferences(self):
        for half_meters in range(1,401):
            length = Decimal(half_meters)/2
            for preference in ('2','1.5','1','0.5'):
                result=suggest_panels(str(length),preference)
                self.assertEqual(sum(Decimal(r['length'])*r['quantity'] for r in result['rows']),length)
                self.assertTrue(all(Decimal(r['length'])<=Decimal(preference) for r in result['rows']))

    def test_invalid_lengths_are_not_rounded_into_customer_estimate(self):
        for value in ('7.3','NaN',True,None,-1,201):
            with self.subTest(value=value),self.assertRaises(InvalidDocument):suggest_panels(value)
        with self.assertRaises(InvalidDocument):suggest_panels(7,'3')


class ConfirmedRulesTests(SimpleTestCase):
    def calculate(self, **changes):
        form=HouseCalculatorForm(entries(**changes))
        self.assertTrue(form.is_valid(),form.errors)
        return calculate_house(form.cleaned_data)

    def test_ten_cm_preserves_block_counts_without_reusing_weights_or_auxiliary_factors(self):
        wide=self.calculate(panel_4='2',panel_9='1')
        narrow=self.calculate(panel_4='2',panel_9='1',block_family='10')
        self.assertEqual((wide['tp50'],wide['tp37']),(narrow['tp50'],narrow['tp37']))
        self.assertEqual((narrow['block_long_name'],narrow['block_short_name']),('TP48','TP40'))
        self.assertEqual((narrow['beam'],narrow['beam_steel']),(0,0))
        self.assertIsNone(narrow['weight'])
        self.assertIsNone(narrow['mortar'])
        self.assertIsNone(narrow['wall_steel'])

    def test_ten_cm_rejects_extra_heights_and_second_floor(self):
        for extra in ({'height':'1'},{'height':'2'},{'floor_level':'2'}):
            form=HouseCalculatorForm(entries(block_family='10',**extra))
            self.assertFalse(form.is_valid())
        self.assertEqual(calculate_modulation(doc(wall(thickness=.1)),{})['status'],'ready')
        for data in (doc(wall(thickness=.1,height=2.7)),doc(wall(thickness=.1),floor_level=2)):
            self.assertEqual(calculate_modulation(data,{})['status'],'incomplete')

    def test_second_floor_needs_twelve_cm_and_columns(self):
        form=HouseCalculatorForm(entries(floor_level='2',column_mode='manual',panel_4='1'))
        self.assertFalse(form.is_valid())
        result=self.calculate(floor_level='2',column_mode='manual',linear_columns='2',panel_4='1')
        self.assertEqual(result['floor_level'],2)
        self.assertEqual(calculate_modulation(doc(wall(x2=2),floor_level=2),{})['status'],'incomplete')
        self.assertEqual(calculate_modulation(doc(wall(x2=2),floor_level=2,linear_columns=2),{})['status'],'ready')

    def test_current_doors_are_bath_standard_and_wide_not_one_meter(self):
        for width,name in ((1.5,'Puerta baño'),(2,'Puerta estándar'),(3,'Puerta amplia')):
            result=calculate_modulation(doc(wall(x2=width),opening(kind='door',offset=0,width=width)),{})
            self.assertEqual(result['status'],'ready')
            self.assertEqual(result['segments'][0]['kind'],name)
            self.assertEqual(result['items'][0]['quantity'],0)
            self.assertEqual(result['meters'],width)
        legacy=HouseCalculatorForm(entries(panel_19='1'))
        self.assertFalse(legacy.is_valid())
        self.assertIn('panel_19',legacy.errors)

    def test_all_preferences_apply_to_sketches_and_ten_cm_material_names(self):
        for span,parts in (('2',[2,1.5]),('1.5',[1.5,1.5,.5]),('1',[1,1,1,.5]),('0.5',[.5]*7)):
            result=calculate_modulation(doc(wall(x2=3.5,thickness=.1),max_span=span),{})
            self.assertEqual([s['length'] for s in result['segments']],parts)
            self.assertIn('TP48',result['items'][0]['name'])


@override_settings(DEBUG=True)
class DistributionApiTests(TestCase):
    def test_default_and_conversion_into_manual_recipe_fields(self):
        response=self.client.post('/api/suggest-panels/',json.dumps({'meters':'7.5'}),content_type='application/json')
        self.assertEqual(response.status_code,200)
        data=entries(**{r.key:str(next((row['quantity'] for row in response.json()['rows'] if row['length']==r.length),0))
                        for r in RECIPES if r.kind=='Completo'})
        form=HouseCalculatorForm(data)
        self.assertTrue(form.is_valid())
        self.assertEqual(calculate_house(form.cleaned_data)['meters'],Decimal('7.5'))

    def test_csrf_and_staff_access_are_required(self):
        client=Client(enforce_csrf_checks=True)
        self.assertEqual(client.post('/api/suggest-panels/','{}',content_type='application/json').status_code,403)
        with self.settings(DEBUG=False):
            self.client.logout()
            self.assertEqual(self.client.post('/api/suggest-panels/','{}',content_type='application/json').status_code,403)

    def test_ten_cm_attention_preserves_unknown_quantities_after_save(self):
        from .models import Attention
        response=self.client.post('/calculador-casas/',entries(action='save',block_family='10',panel_4='1'))
        self.assertEqual(response.status_code,302)
        record=Attention.objects.get()
        self.assertEqual(record.inputs['block_family'],'10')
        self.assertIsNone(record.result['weight'])
        self.assertEqual(record.result['items'][0][1],36)
        response=self.client.get(f'/atenciones/{record.pk}/')
        self.assertContains(response,'Pendiente')
        self.assertContains(response,'TP48')

    def test_legacy_attention_result_is_not_changed_when_reopened_for_review(self):
        from .models import Attention
        record=Attention.objects.create(kind='manual',project='Histórico',inputs=entries(panel_19='1'),
            result={'height_label':'2,50 m','panels':1,'meters':'1','columns':2,'items':[['Columna C · lineal',2,'unidades']],'warnings':[]},
            rule_version='ticoblock-manual-2026-10-20-v2')
        original=record.result.copy()
        response=self.client.get(f'/calculador-casas/?attention={record.pk}')
        self.assertEqual(response.status_code,400)
        self.assertContains(response,'módulo antiguo de puerta',status_code=400)
        record.refresh_from_db()
        self.assertEqual(record.result,original)

    def test_templates_identify_ten_cm_without_changing_quantities(self):
        response=self.client.get('/calculador-casas/plantillas/modelo-e/')
        self.assertContains(response,'TP48 · 10 cm')
        self.assertEqual(response.context['result']['blocks'],498)
