from django.db import models
from django.conf import settings
import uuid


class Sketch(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Propietario")
    name = models.CharField(max_length=160)
    document = models.JSONField(default=dict)
    is_template = models.BooleanField(default=False)
    revision = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.name


class ObjectTemplate(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Propietario")
    name = models.CharField(max_length=100)
    specification = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)


class RenderJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    sketch = models.ForeignKey(Sketch, null=True, blank=True, on_delete=models.SET_NULL)
    sketch_revision = models.PositiveIntegerField(null=True, blank=True)
    title = models.CharField(max_length=160)
    document = models.JSONField()
    scene = models.JSONField()
    fingerprint = models.CharField(max_length=64)
    status = models.CharField(max_length=16, default='queued', db_index=True,
        choices=[('queued', 'En cola'), ('running', 'Generando'), ('ready', 'Lista'), ('failed', 'No completada')])
    error = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True)
    finished_at = models.DateTimeField(null=True)

    class Meta:
        ordering = ['-created_at']


class RenderWorker(models.Model):
    # Heartbeat, not a remote-control endpoint. Only the management command writes it.
    id = models.PositiveSmallIntegerField(primary_key=True, default=1)
    heartbeat = models.DateTimeField()


class Attention(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Propietario")
    kind = models.CharField(max_length=16, choices=(("manual", "Cálculo por paños"), ("template", "Lista de plantilla")))
    template_slug = models.CharField(max_length=80, blank=True)
    project = models.CharField(max_length=160)
    customer = models.CharField(max_length=160, blank=True)
    notes = models.TextField(blank=True)
    inputs = models.JSONField(default=dict)
    result = models.JSONField(default=dict)
    rule_version = models.CharField(max_length=80)
    revision = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-updated_at", "-id"]

    def __str__(self):
        return self.project

    @property
    def review_label(self):
        if self.kind == "manual" and self.result.get("panels") and not self.result.get("columns"):
            return "Columnas pendientes"
        if self.kind == "template" and self.result.get("unknown"):
            return "Cantidades sin confirmar"
        return "Estimación para revisión"
