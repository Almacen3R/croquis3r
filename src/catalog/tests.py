from django.core.management import call_command
from django.test import TestCase
from .models import Article


class SeedDemoTests(TestCase):
    def test_seed_is_repeatable_and_preserves_edited_articles(self):
        call_command("seed_demo", verbosity=0)
        article = Article.objects.get(sku="DEMO-BLOCK")
        article.name = "Nombre ajustado para prueba"
        article.save()
        call_command("seed_demo", verbosity=0)
        self.assertEqual(Article.objects.count(), 4)
        article.refresh_from_db()
        self.assertEqual(article.name, "Nombre ajustado para prueba")
