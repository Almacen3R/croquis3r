from django.core.management.base import BaseCommand
from django.db import transaction
from catalog.models import Article


class Command(BaseCommand):
    help = "Carga artículos ficticios sin duplicar ni sobrescribir cambios."

    @transaction.atomic
    def handle(self, *args, **options):
        for sku, name in [
            ("DEMO-BLOCK", "Block de ejemplo 40 × 20 cm"),
            ("DEMO-MADERA", "Pieza de madera de ejemplo"),
            ("DEMO-PUERTA", "Puerta de ejemplo"),
            ("DEMO-VENTANA", "Ventana de ejemplo"),
        ]:
            Article.objects.get_or_create(sku=sku, defaults={"name": name})
        self.stdout.write(self.style.SUCCESS("Catálogo ficticio listo. Solo para probar Croquis3R."))
