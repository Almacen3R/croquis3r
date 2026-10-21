"""Contrato de consulta: la futura integración real será de solo lectura."""
from .models import Article


class DemoCatalogProvider:
    def articles(self):
        return Article.objects.filter(active=True)


def get_catalog_provider():
    return DemoCatalogProvider()
