from django.contrib import admin
from .models import ObjectTemplate, Sketch

@admin.register(Sketch)
class SketchAdmin(admin.ModelAdmin):
    list_display = ["name", "is_template", "revision", "updated_at"]
    readonly_fields = ["document", "revision", "created_at", "updated_at"]

admin.site.register(ObjectTemplate)
