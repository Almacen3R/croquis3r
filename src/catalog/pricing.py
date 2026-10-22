"""Precios de referencia separados de las recetas de cantidades."""
from collections import Counter
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.utils import timezone

from .homologation import MAPPINGS, VERSION, description_matches
from .sql_prices import PriceSourceUnavailable, SqlPriceProvider

CENT = Decimal('0.01')


def money(value):
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def opening_key(kind, width):
    size = str(Decimal(str(width)).normalize())
    # normalize(2) is '2', never 2.0; estas son medidas MODULARES, no de marco.
    if kind.startswith('Puerta'):
        return f'door_{size}'
    group = {'Ventana regular': 'regular', 'Ventana cocina': 'kitchen', 'Ventana baño': 'bath'}[kind]
    return f'window_{group}_{size}'


def manual_rows(result):
    keys = [result['block_long_name'].lower(), result['block_short_name'].lower(),
            'column_linear', 'column_cross', 'beam', 'mortar', 'steel', 'steel']
    rows = [{'key': key, 'name': name, 'quantity': quantity, 'unit': unit}
            for key, (name, quantity, unit) in zip(keys, result['items'])]
    for detail in result['details']:
        if detail['kind'].startswith(('Puerta', 'Ventana')):
            rows.append({'key': opening_key(detail['kind'], detail['length']),
                'name': f"{detail['kind']} · módulo {detail['length']} m",
                'quantity': detail['quantity'], 'unit': 'unidades'})
    return rows


def sketch_rows(result):
    keys = [result['block_long_name'].lower(), result['block_short_name'].lower(),
            'column_linear', 'column_cross', 'beam', 'mortar', 'steel', 'steel']
    rows = [{'key': key, 'name': row['name'], 'quantity': row['quantity'], 'unit': row['unit']}
            for key, row in zip(keys, result['items'])]
    counts = Counter((segment['kind'], str(Decimal(str(segment['length'])).normalize()))
        for segment in result['segments'] if segment['kind'].startswith(('Puerta', 'Ventana')))
    for (kind, width), quantity in counts.items():
        rows.append({'key': opening_key(kind, width), 'name': f'{kind} · módulo {width} m',
                     'quantity': quantity, 'unit': 'unidades'})
    return rows


def template_rows(result):
    keys = {'Columna C · lineal': 'column_linear', 'Columna E · esquina/cruz': 'column_cross',
            'TP48 · 10 cm': 'tp48', 'TP40 · 10 cm': 'tp40',
            'Ventana 1,375 × 60 (baño)': 'window_bath_1.5',
            'Ventana 1,375 × 1200': 'window_regular_1.5',
            'Ventana 1,375 × 800 (cocina)': 'window_kitchen_1.5',
            'Ventana 1,875 × 1200': 'window_regular_2',
            'Ventana 1,875 × 800': 'window_kitchen_2'}
    return [{'key': keys.get(row['name'], 'unmapped'), 'name': row['name'],
             'quantity': row['quantity'], 'unit': 'unidades'} for row in result['rows']]


def quote(rows, provider=None):
    if not settings.THREER_PRICING_ENABLED:
        return None
    rows = [row for row in rows if row['quantity'] is None or row['quantity'] > 0]
    if not rows:
        return None
    skus = {MAPPINGS[row['key']][0] for row in rows
            if row['key'] in MAPPINGS and row['quantity'] is not None}
    lookup = {'articles': {}, 'fetched_at': None}
    error = ''
    if skus:
        try:
            lookup = (provider or SqlPriceProvider()).fetch(skus)
        except PriceSourceUnavailable as exc:
            error = str(exc)
    priced = []
    total, base, tax = Decimal(0), Decimal(0), Decimal(0)
    count = 0
    for row in rows:
        item = {**row, 'sku': '', 'status': 'pending', 'unit_price': None,
                'amount': None, 'base_amount': None, 'tax_amount': None, 'description': ''}
        mapping = MAPPINGS.get(row['key'])
        if mapping:
            item['sku'] = mapping[0]
        if row['quantity'] is None:
            item['reason'] = 'Cantidad pendiente de confirmar.'
        elif mapping is None:
            item['reason'] = 'Código o correspondencia comercial pendiente.'
        elif error:
            item['reason'] = error
        else:
            article = lookup['articles'].get(mapping[0], {})
            if article.get('status') != 'ready':
                item['reason'] = article.get('reason', 'Precio vigente no disponible.')
            elif not description_matches(row['key'], article['description']):
                item['reason'] = 'La descripción comercial ya no coincide con la homologación.'
            else:
                price = Decimal(article['price'])
                rate = Decimal(article['tax_rate'])
                amount = money(price * Decimal(row['quantity']))
                if settings.THREER_SQL_PRICE_INCLUDES_TAX:
                    line_base = money(amount / (1 + rate / 100))
                    line_tax = amount - line_base
                else:
                    line_base = amount
                    line_tax = money(line_base * rate / 100)
                    amount += line_tax
                item.update(status='ready', unit_price=price, amount=amount,
                    base_amount=line_base, tax_amount=line_tax, tax_rate=rate,
                    description=article['description'], reason='')
                total += amount
                base += line_base
                tax += line_tax
                count += 1
        priced.append(item)
    fetched = lookup['fetched_at']
    display = timezone.localtime(datetime.fromisoformat(fetched)).strftime('%d/%m/%Y %H:%M') if fetched else ''
    missing = len(priced) - count
    return {'version': VERSION, 'status': 'ready' if not missing else 'partial', 'rows': priced,
            'currency': 'CRC', 'price_level': settings.THREER_SQL_PRICE_LEVEL,
            'includes_tax': settings.THREER_SQL_PRICE_INCLUDES_TAX,
            'priced_count': count, 'pending_count': missing, 'complete': not missing,
            'subtotal_with_prices': total, 'base_with_prices': base, 'tax_with_prices': tax,
            'total': total if not missing else None, 'fetched_at': fetched, 'fetched_display': display,
            'error': error,
            'notice': 'Precios de referencia de los artículos listados. El subtotal con precio excluye pendientes; no es el costo total de la casa. Importes calculados con la precisión de la base y redondeados a dos decimales por renglón.'}
