"""Catálogo de asignaciones de ejemplo anteriores. Los precios reales se consultan en sql_prices.py, sin cambiar IDs históricos."""
from .models import Article


class DemoCatalogProvider:
    def articles(self):
        return Article.objects.filter(active=True)


def get_catalog_provider():
    return DemoCatalogProvider()
