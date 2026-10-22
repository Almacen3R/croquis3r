import json
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from catalog.homologation import MAPPINGS, description_matches, normalize
from catalog.pricing import money
from catalog.sql_prices import PriceSourceUnavailable, SqlPriceProvider


class Command(BaseCommand):
    help = 'Verifica los códigos homologados con consultas SELECT; no importa ni modifica artículos.'

    def add_arguments(self, parser):
        parser.add_argument('--reference', help='Instantánea JSON local del rango A1:F19 del archivo Homologacion.')
        parser.add_argument('--output', help='Informe JSON local; no incluir precios de la base en Git.')

    def handle(self, *args, **options):
        reference = {}
        if options['reference']:
            source = json.loads(Path(options['reference']).read_text(encoding='utf-8'))
            for index, row in enumerate(source['data']['values'], 1):
                if len(row) > 5 and str(row[3]).isdigit() and row[5] is not None:
                    reference[str(row[3])] = {'row': index, 'price': Decimal(str(row[5])), 'description': row[4]}
        try:
            response = SqlPriceProvider().fetch({value[0] for value in MAPPINGS.values()}, refresh=True)
        except PriceSourceUnavailable as exc:
            raise CommandError(str(exc)) from None
        rows, failed = [], False
        for key, (sku, _) in MAPPINGS.items():
            article = response['articles'].get(sku, {})
            good = article.get('status') == 'ready' and description_matches(key, article.get('description', ''))
            expected = reference.get(sku)
            matches = money(article['price']) == money(expected['price']) if good and expected else None
            failed |= not good or matches is False
            row = {'key': key, 'sku': sku, 'ready': good,
                   'description': article.get('description'), 'price': article.get('price'),
                   'reference_price': expected['price'] if expected else None, 'price_matches': matches,
                   'reference_description_matches': normalize(expected['description']) == normalize(article.get('description', '')) if expected and good else None}
            rows.append(row)
            self.stdout.write(f'{sku} · {key}: ' + ('OK' if good else 'PENDIENTE') +
                (f" · precio Excel {'coincide' if matches else 'difiere'}" if matches is not None else ''))
        if options['output']:
            Path(options['output']).write_text(json.dumps({'fetched_at': response['fetched_at'], 'rows': rows}, default=str, indent=2), encoding='utf-8')
        if failed:
            raise CommandError('Hay artículos o precios pendientes de revisar; no se cambió la base.')
        self.stdout.write(self.style.SUCCESS(f'{len(rows)} artículos verificados. Solo SELECT; sin cambios en la base comercial.'))
