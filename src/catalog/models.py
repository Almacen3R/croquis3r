from django.db import models


class Article(models.Model):
    sku = models.CharField(max_length=60, unique=True)
    name = models.CharField(max_length=160)
    unit = models.CharField(max_length=20, default="unidad")
    external_id = models.CharField(max_length=100, blank=True)
    is_demo = models.BooleanField(default=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sku"]

    def __str__(self):
        return f"{self.sku} · {self.name}"
