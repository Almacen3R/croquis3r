from django.contrib import admin
from .models import Article

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["sku", "name", "unit", "is_demo", "active"]
    search_fields = ["sku", "name", "external_id"]
