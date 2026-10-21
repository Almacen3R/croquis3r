"""Recetas transcritas del modulador manual recibido el 20-10-2026.

Conserva ROUND de Excel (mitades hacia arriba) y no incorpora reglas estructurales.
Actualización 21-10-2026: familias de 10/12 cm y módulos comerciales de puertas
confirmados por el usuario tras su reunión con TicoBlock; ver docs/aclaraciones-ticoblock-2026-10-21.md.
Referencias completas: docs/investigacion-ticoblock-2026-10-20.md, secciones 4 y 5.
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

from django import forms
from .attention import AttentionFields

VERSION = "ticoblock-manual-2026-10-21-v3"


@dataclass(frozen=True)
class Recipe:
    row: int
    kind: str
    length: str
    tp50: int
    tp37: int
    steel: str

    @property
    def source_label(self):
        return f"Excel · fila {self.row}" if self.row <= 20 else "Módulo confirmado 21-10-2026; vano sin bloques según modulador"

    @property
    def key(self):
        return f"panel_{self.row}"

    @property
    def length_label(self):
        return self.length.replace(".", ",")


RECIPES = (
    Recipe(4, "Completo", "2", 36, 12, "1.5"),
    Recipe(5, "Completo", "1.5", 24, 12, "1"),
    Recipe(6, "Completo", "1", 12, 12, "0.5"),
    Recipe(7, "Completo", "0.5", 0, 12, "0"),
    Recipe(8, "Ventana regular", "2", 15, 5, "1.5"),
    Recipe(9, "Ventana regular", "1.5", 10, 5, "1"),
    Recipe(10, "Ventana regular", "1", 5, 5, "0.5"),
    Recipe(11, "Ventana regular", "0.5", 0, 5, "0"),
    Recipe(12, "Ventana cocina", "2", 18, 6, "1.5"),
    Recipe(13, "Ventana cocina", "1.5", 12, 6, "1"),
    Recipe(14, "Ventana cocina", "1", 6, 6, "0.5"),
    Recipe(15, "Ventana cocina", "0.5", 0, 6, "0"),
    Recipe(16, "Ventana baño", "1.5", 20, 10, "1"),
    Recipe(17, "Ventana baño", "1", 10, 10, "0.5"),
    Recipe(18, "Puerta estándar", "2", 0, 0, "0"),
    Recipe(101, "Puerta baño", "1.5", 0, 0, "0"),
    Recipe(102, "Puerta amplia", "3", 0, 0, "0"),
    Recipe(20, "Ventana baño", "0.5", 0, 10, "0"),
)


class HouseCalculatorForm(AttentionFields):
    project = forms.CharField(label="Nombre del cálculo", max_length=160, required=False,
                              initial="Nuevo cálculo")
    block_family = forms.ChoiceField(label="Familia de bloques", required=False, initial="12",
        choices=(("12", "12 cm · TP50 / TP37 · recomendado"), ("10", "10 cm · TP48 / TP40")))
    floor_level = forms.TypedChoiceField(label="Nivel del proyecto", required=False, coerce=int, empty_value=1, initial=1,
        choices=((1, "Primera planta o tapia"), (2, "Segundo piso · requiere 12 cm y columnas")))
    panel_19 = forms.IntegerField(label="Puertas antiguas de módulo 1 m · por revisar", required=False,
                                  min_value=0, max_value=100, initial=0)
    height = forms.TypedChoiceField(label="Altura de referencia", coerce=int, initial=0,
        choices=((0, "2,50 m · base, sin vigabloques adicionales"),
                 (1, "2,70 m · una hilada de vigabloque"),
                 (2, "2,90 m · dos hiladas de vigabloque")))
    column_mode = forms.ChoiceField(label="Cómo contar columnas", initial="manual",
        choices=(("manual", "Ingresar cantidades del proyecto"),
                 ("chain", "Cadena abierta: número de paños + 1")))
    linear_columns = forms.IntegerField(label="C · lineal", min_value=0, max_value=10000, initial=0)
    t_columns = forms.IntegerField(label="E · esquina/cruz", min_value=0, max_value=10000, initial=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for recipe in RECIPES:
            self.fields[recipe.key] = forms.IntegerField(
                label=f"{recipe.kind} · {recipe.length.replace('.', ',')} m",
                min_value=0, max_value=100, initial=0,
                widget=forms.NumberInput(attrs={"inputmode": "numeric",
                    "aria-label": f"Cantidad de paños: {recipe.kind}, {recipe.length} m"}))

    def clean(self):
        data = super().clean()
        data['block_family'] = data.get('block_family') or '12'
        data['floor_level'] = data.get('floor_level') or 1
        if data.get('panel_19'):
            self.add_error('panel_19', 'El módulo antiguo de puerta de 1 m ya no corresponde a la oferta confirmada. Revisa su cantidad, pásala a Baño 1,50 m, Estándar 2 m o Amplia 3 m y deja este campo en cero.')
        if data['block_family']=='10' and data.get('height') not in (None, 0):
            self.add_error('height', 'Las paredes de 10 cm solo admiten 2,50 m; no usan vigabloques.')
        if data['floor_level']==2:
            if data['block_family']!='12':
                self.add_error('block_family', 'Para segundo piso se requieren bloques de 12 cm con columnas.')
            elif data.get('column_mode')=='manual' and not ((data.get('linear_columns') or 0)+(data.get('t_columns') or 0)):
                self.add_error('linear_columns', 'Indica las columnas del proyecto de segundo piso.')
        return data


def excel_round(value):
    return int(value.to_integral_value(rounding=ROUND_HALF_UP))


def calculate_house(data):
    """Recibe exclusivamente cleaned_data del formulario validado."""
    family = data.get('block_family') or '12'
    narrow = family == '10'
    long_name, short_name = ('TP48', 'TP40') if narrow else ('TP50', 'TP37')
    details = []
    for recipe in RECIPES:
        quantity = data[recipe.key]
        if quantity:
            details.append({"kind": recipe.kind, "length": recipe.length, "quantity": quantity,
                "tp50_each": recipe.tp50, "tp37_each": recipe.tp37,
                "tp50": quantity * recipe.tp50, "tp37": quantity * recipe.tp37,
                "meters": quantity * Decimal(recipe.length),
                "steel": quantity * Decimal(recipe.steel), "row": recipe.row, "source": recipe.source_label})
    panels = sum(row["quantity"] for row in details)
    meters = sum((row["meters"] for row in details), Decimal(0))
    tp50 = sum(row["tp50"] for row in details)
    tp37 = sum(row["tp37"] for row in details)
    mortar = int((Decimal(tp50 + tp37) / 20).to_integral_value(rounding=ROUND_CEILING))
    wall_factor = sum((row["steel"] for row in details), Decimal(0))
    wall_steel = excel_round(wall_factor)
    beam_one = excel_round(meters * Decimal("2.5"))
    steel_one = excel_round(meters / 6)
    layers = data["height"]
    chain = data["column_mode"] == "chain"
    # La cadena vacía produce cero en la web; Excel conserva una columna por N+1.
    linear = (panels + 1 if panels else 0) if chain else data["linear_columns"]
    t = 0 if chain else data["t_columns"]
    warnings = ["Estimación del modulador recibido: no incluye cimentación, techo, instalaciones, "
                "rellenos ni todos los materiales de una casa.",
                "Varilla: equivalentes según Excel; largos, cortes, anclajes y traslapes por confirmar."]
    if chain:
        warnings.append("Paños + 1 solo representa una cadena abierta. No resuelve esquinas, "
                        "intersecciones ni casas cerradas; las cantidades manuales se ignoran en este modo.")
        if not panels:
            warnings.append("Sin paños se muestran cero columnas; el Excel manual muestra una por defecto.")
    elif panels and not linear + t:
        warnings.append("Faltan las cantidades de columnas del proyecto.")
    if meters and layers and not steel_one:
        warnings.append("El redondeo del Excel da cero varillas de viga en este tramo. Revisar el refuerzo.")
    if wall_factor and not wall_steel:
        warnings.append("El redondeo del Excel da cero varillas de pared. Revisar el refuerzo.")
    if any(row["kind"].startswith("Puerta") for row in details):
        warnings.append("Las recetas de puertas aportan longitud, pero cero bloques de cerramiento. "
                        "Marcos y refuerzos no se calculan aquí.")
    if narrow:
        warnings.append('10 cm: mismas cantidades de bloques por paño, con TP48/TP40 y solo altura 2,50 m. No se usan vigas de bloques; perling o chorreado y sus refuerzos se presupuestan por separado.')
        warnings.append('Peso, mortero y varilla de pared para 10 cm: pendientes de confirmar; no se trasladan los factores del Excel de 12 cm.')
    if data.get('floor_level') == 2:
        warnings.append('Segundo piso: compatibilidad de materiales de 12 cm con columnas. No dimensiona entrepiso, cimentación ni capacidad de carga; requiere revisión profesional.')
    weight = tp50 * 16 + tp37 * 11 + (linear + t) * 108 + mortar * 40
    if narrow:
        mortar = wall_steel = wall_factor = weight = None
        beam_one = steel_one = layers = 0
    return {"version": VERSION, "block_family": family, "block_long_name": long_name, "block_short_name": short_name,
        "floor_level": data.get('floor_level', 1), "height_label": {0: "2,50 m", 1: "2,70 m", 2: "2,90 m"}[layers],
        "panels": panels, "meters": meters, "details": details,
        "tp50": tp50, "tp37": tp37, "mortar": mortar,
        "linear_columns": linear, "t_columns": t,
        "columns": linear + t, "beam": beam_one * layers,
        "beam_one": beam_one, "beam_two": beam_one * 2,
        "wall_steel": wall_steel, "wall_factor": wall_factor,
        "beam_steel": steel_one * layers, "steel_one": steel_one,
        "steel_two": steel_one * 2, "steel_total": None if narrow else wall_steel + steel_one * layers,
        "weight": weight, "warnings": warnings,
        "items": ((f"Bloque {long_name} · {family} cm", tp50, "unidades"), (f"Bloque {short_name} · {family} cm", tp37, "unidades"),
                  ("Columna C · lineal", linear, "unidades"), ("Columna E · esquina/cruz", t, "unidades"),
                  ("Vigabloque", beam_one * layers, "unidades"),
                  ("Mortero / pegablock", mortar, "sacos de 40 kg"),
                  ("Varilla 3/8 · pared", wall_steel, "equivalentes Excel"),
                  ("Varilla 3/8 · viga", steel_one * layers, "equivalentes Excel"))}
