from django.db import models


class Sketch(models.Model):
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
    name = models.CharField(max_length=100)
    specification = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)


class Attention(models.Model):
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
