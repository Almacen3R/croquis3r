"""Identidades confirmadas; precios consultados en vivo, nunca constantes aquí.

Fuente: Homologacion / Hoja 1, y aclaración del usuario del 22-10-2026.
Las descripciones de TP50/37 del Excel estaban cruzadas; SQL confirma los SKU.
La columna comercial T es cruz; no confundir con la C lineal del croquis.
"""
SOURCE_URL = 'https://docs.google.com/spreadsheets/d/19sEv02yI8LzaI3dB4t2DEVWF3KlATenWDA3I_8E4THA/edit'
VERSION = '3r-homologacion-2026-10-22-v1'

# fragmentos de descripción normalizada + unidad esperada evitan reutilizar un
# código cuyo producto o presentación hayan cambiado en el catálogo comercial.
MAPPINGS = {
    'tp50': ('44648', ('BLOCK', '12X20X50')),
    'tp37': ('44649', ('BLOCK', '12X20X37')),
    'tp48': ('51976', ('BLOCK', '10X20X48')),
    'tp40': ('51975', ('BLOCK', '10X20X40')),
    'column_linear': ('44647', ('COLUMNA', 'TIPOC', '325METROS')),
    'column_cross': ('51234', ('COLUMNA', 'TIPOT', '325METROS')),
    'beam': ('45245', ('VIGA', '12X20X40')),
    'window_bath_1.5': ('49190', ('VENTANA', '137CMX60CM')),
    'window_regular_1.5': ('49192', ('VENTANA', '137CMX120CM')),
    'window_kitchen_1.5': ('49191', ('VENTANA', '137CMX80CM')),
    'door_2': ('53798', ('PUERTA', '187METROSX210METROS')),
}


def normalize(value):
    return ''.join(c for c in value.upper() if c.isalnum())


def description_matches(key, description):
    normalized = normalize(description)
    return all(fragment in normalized for fragment in MAPPINGS[key][1])
