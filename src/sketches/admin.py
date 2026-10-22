from django.contrib import admin
from .models import Attention, ObjectTemplate, Sketch


class OwnerAdmin(admin.ModelAdmin):
    list_filter = ['owner']
    search_fields = ['owner__username']

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    has_add_permission = has_view_permission
    has_change_permission = has_view_permission
    has_delete_permission = has_view_permission

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('owner') if request.user.is_superuser else self.model.objects.none()

    def save_model(self, request, obj, form, change):
        if not change and not obj.owner_id:
            obj.owner = request.user
        super().save_model(request, obj, form, change)


@admin.register(Sketch)
class SketchAdmin(OwnerAdmin):
    list_display = ['name', 'owner', 'is_template', 'revision', 'updated_at']
    search_fields = ['name', 'owner__username']
    readonly_fields = ['document', 'revision', 'created_at', 'updated_at']


@admin.register(ObjectTemplate)
class ObjectTemplateAdmin(OwnerAdmin):
    list_display = ['name', 'owner', 'created_at']
    search_fields = ['name', 'owner__username']
    readonly_fields = ['specification', 'created_at']


@admin.register(Attention)
class AttentionAdmin(OwnerAdmin):
    list_display = ['project', 'owner', 'kind', 'updated_at']
    search_fields = ['project', 'customer', 'owner__username']
    readonly_fields = ['inputs', 'result', 'revision', 'rule_version', 'created_at', 'updated_at']
