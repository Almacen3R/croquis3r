"""Listas publicadas en DISEÑOS DE CASAS CON CANTIDAD DE MATERIAL.docx.

Son plantillas de listas, no una descomposición inferida de paños ni un modelo
estructural. None conserva el guion del documento como cantidad no indicada.
"""
from dataclasses import dataclass

from django import forms
from .attention import AttentionFields

SOURCE_URL = "https://drive.google.com/file/d/17Pl4Paa5EPlqT16Z8UQVXnZq-rbxfOmA/view"
SOURCE_NAME = "DISEÑOS DE CASAS CON CANTIDAD DE MATERIAL.docx"
SOURCE_SHA256 = "b33c406448aa6d32add2e1d0156cb38d7738818f15aef0c0d2a1f8fe4b92a224"
VERSION = "disenos-casas-2026-10-21-v2"


@dataclass(frozen=True)
class Material:
    key: str
    name: str
    quantity: int | None


@dataclass(frozen=True)
class HouseTemplate:
    slug: str
    name: str
    area: str
    image: str
    table: int
    materials: tuple
    note: str = ""


def materials(c, e, tp48, tp40, bath, regular=None, kitchen=None, wide=None, wide_kitchen=None):
    result = [Material("column_c", "Columna C · lineal", c), Material("column_e", "Columna E · esquina/cruz", e),
              Material("tp48", "TP48 · 10 cm", tp48), Material("tp40", "TP40 · 10 cm", tp40),
              Material("bath", "Ventana 1,375 × 60 (baño)", bath)]
    # Solo se incluyen renglones presentes en el original; no se infieren faltantes.
    for key, name, value in (("regular", "Ventana 1,375 × 1200", regular),
                             ("kitchen", "Ventana 1,375 × 800 (cocina)", kitchen),
                             ("wide", "Ventana 1,875 × 1200", wide),
                             ("wide_kitchen", "Ventana 1,875 × 800", wide_kitchen)):
        if value is not None:
            result.append(Material(key, name, None if value == "-" else value))
    return tuple(result)


TEMPLATES = (
    HouseTemplate("modelo-e", "Modelo E", "24,75", "croquis/houses/modelo-e.png", 1,
                  materials(12, 7, 316, 182, 1, 2, 1, "-", "-"),
                  "La tabla repite Ventana 1,375 × 1200 con un guion después de indicarla con cantidad 2. "
                  "Se conserva la cantidad 2 una sola vez; la repetición queda pendiente de aclarar."),
    HouseTemplate("modelo-d", "Modelo D", "39", "croquis/houses/modelo-d.png", 2,
                  materials(18, 9, 432, 282, 1, 3, 1)),
    HouseTemplate("promo-a", "Promo A", "45,5", "croquis/houses/promo-a.png", 3,
                  materials(20, 9, 516, 306, 1, 3, 1)),
    HouseTemplate("modelo-estandar", "Modelo estándar", "48,75", "croquis/houses/modelo-estandar.png", 4,
                  materials(20, 10, 482, 307, 1, kitchen=1, wide=3)),
    HouseTemplate("modelo-j", "Modelo J", "48", "croquis/houses/modelo-j.png", 5,
                  materials(23, 10, 508, 344, 1, kitchen="-", wide=4)),
    HouseTemplate("modelo-g", "Modelo G", "54", "croquis/houses/modelo-g.png", 6,
                  materials(23, 11, 580, 362, 1, 4, 1)),
    HouseTemplate("modelo-63", "Modelo 63", "63", "croquis/houses/modelo-63.png", 7,
                  materials(28, 12, 620, 402, 2, 4, 1),
                  "El encabezado del documento dice MODELO 63 m²; se identifica como Modelo 63."),
)
TEMPLATES_BY_SLUG = {template.slug: template for template in TEMPLATES}


class HouseTemplateForm(AttentionFields):
    project = forms.CharField(label="Nombre de tu copia", max_length=160)

    def __init__(self, template, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["project"].initial = f"Mi casa · {template.name}"
        for item in template.materials:
            self.fields[item.key] = forms.IntegerField(label=item.name, required=False,
                min_value=0, max_value=100000, initial=item.quantity,
                widget=forms.NumberInput(attrs={"inputmode": "numeric",
                    "aria-label": f"Cantidad de {item.name}", "placeholder": "Sin indicar"}))
        self.template = template

    def clean(self):
        cleaned = super().clean()
        # Un número presente en la fuente no puede borrarse por accidente. Cero
        # permite eliminarlo explícitamente; blanco solo conserva un dato desconocido.
        for item in self.template.materials:
            if item.quantity is not None and item.key in cleaned and cleaned[item.key] is None:
                self.add_error(item.key, "Indica una cantidad. Usa 0 si deseas quitar este material.")
        return cleaned


def template_result(template, data):
    rows = []
    for item in template.materials:
        quantity = data[item.key]
        changed = quantity != item.quantity
        rows.append({"name": item.name, "original": item.quantity, "quantity": quantity,
                     "changed": changed})
    return {"block_family": "10", "rows": rows, "changed": any(row["changed"] for row in rows),
            "blocks": data["tp48"] + data["tp40"],
            "columns": data["column_c"] + data["column_e"],
            "unknown": sum(row["quantity"] is None for row in rows), "project": data["project"]}
