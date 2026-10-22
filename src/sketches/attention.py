"""Guardado de entradas y resultado reproducido por el servidor para cada atención."""
import json

from django import forms
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.http import Http404
from django.utils import timezone

from .models import Attention
from .access import visible_to


class AttentionFields(forms.Form):
    customer = forms.CharField(label="Cliente o referencia", max_length=160, required=False,
                               widget=forms.TextInput(attrs={"autocomplete": "off"}))
    notes = forms.CharField(label="Notas para continuar la atención", max_length=2000, required=False,
                           widget=forms.Textarea(attrs={"rows": 3}))
    record_id = forms.IntegerField(min_value=1, required=False, widget=forms.HiddenInput)
    record_revision = forms.IntegerField(min_value=1, required=False, widget=forms.HiddenInput)


def load_attention(request, kind, slug=""):
    raw = request.GET.get("attention")
    if not raw:
        return None
    if not raw.isdecimal() or len(raw) > 18:
        raise Http404("Atención no encontrada.")
    record = visible_to(Attention, request.user).filter(pk=raw, kind=kind, template_slug=slug).first()
    if record is None:
        raise Http404("Atención no encontrada.")
    return record


def saved_inputs(record):
    return {**record.inputs, "record_id": record.pk, "record_revision": record.revision}


def save_attention(form, result, kind, version, slug="", copy=False, *, user):
    data = form.cleaned_data
    inputs = {key: value for key, value in data.items() if key not in ("record_id", "record_revision")}
    # Nunca se acepta un resultado calculado por el navegador como evidencia guardada.
    values = {"project": data.get("project") or "Casa sin nombre", "customer": data.get("customer", ""),
              "notes": data.get("notes", ""), "inputs": inputs,
              "result": json.loads(json.dumps(result, cls=DjangoJSONEncoder)), "rule_version": version}
    pk = data.get("record_id")
    with transaction.atomic():
        if pk:
            current = visible_to(Attention, user).filter(pk=pk, kind=kind, template_slug=slug).first()
            if current is None:
                form.add_error(None, "La atención ya no está disponible para este tipo de cálculo.")
                return None
            if not copy:
                revision = data.get("record_revision")
                changed = visible_to(Attention, user).filter(pk=pk, kind=kind, template_slug=slug, revision=revision).update(
                    **values, revision=(revision or 0) + 1, updated_at=timezone.now())
                if not changed:
                    form.add_error(None, "Otra sesión actualizó esta atención. Usa Guardar copia para conservar tus cambios.")
                    return None
                return Attention.objects.get(pk=pk)
        return Attention.objects.create(owner=user, **values, kind=kind, template_slug=slug)
