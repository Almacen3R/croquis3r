"""Propuesta de modulación geométrica, trazable a las recetas del Excel.

Los largos son referencias modulares dibujadas, sin deducir caras de columnas.
No determina tipologías estructurales ni el ancho libre de vanos.
"""
import math
from decimal import Decimal

from .domain import validate_document, validate_ticoblock_settings
from .house_calculator import RECIPES, calculate_house
from .beams import beam_runs

EPS = 0.000001
KINDS = {"regular": "Ventana regular", "kitchen": "Ventana cocina", "bath": "Ventana baño"}


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def connection_distances(a, b):
    """Distancias desde inicio de a donde b se encuentra con a (incluye T/X)."""
    p, q = (a["x1"], a["y1"]), (b["x1"], b["y1"])
    r = (a["x2"] - p[0], a["y2"] - p[1])
    s = (b["x2"] - q[0], b["y2"] - q[1])
    qp = (q[0] - p[0], q[1] - p[1])
    denominator = cross(r, s)
    length = math.hypot(*r)
    if abs(denominator) > EPS:
        t, u = cross(qp, s) / denominator, cross(qp, r) / denominator
        return [max(0, min(1, t)) * length] if -EPS <= t <= 1 + EPS and -EPS <= u <= 1 + EPS else []
    if abs(cross(qp, r)) > EPS:
        return []
    distances = []
    for n in (1, 2):
        t = ((b[f"x{n}"] - p[0]) * r[0] + (b[f"y{n}"] - p[1]) * r[1]) / length**2
        if -EPS <= t <= 1 + EPS:
            distances.append(max(0, min(1, t)) * length)
    return distances


def modular(value):
    return abs(value * 2 - round(value * 2)) < EPS


def calculate_modulation(document, articles):
    document = validate_document(document, articles)
    settings = validate_ticoblock_settings(document.get("ticoblock", {}))
    walls = [o for o in document["objects"] if o["kind"] == "wall"]
    openings = [o for o in document["objects"] if o["kind"] != "wall"]
    drawn_columns = document.get("columns")
    if not walls and not drawn_columns:
        return {"status": "empty", "items": [], "details": [], "segments": [], "column_positions": [],
                "issues": [], "warnings": [], "notice": "Dibuja una pared para comenzar."}
    recipes = {(r.kind, Decimal(r.length)): r for r in RECIPES}
    segments, issues = [], []
    heights = set()
    families = set()

    def issue(obj, message):
        issues.append({"object_id": obj["id"], "label": obj["label"] or obj["id"], "message": message})

    def column_distance(column, wall):
        dx, dy = wall["x2"] - wall["x1"], wall["y2"] - wall["y1"]
        length = math.hypot(dx, dy)
        at = ((column["x"] - wall["x1"]) * dx + (column["y"] - wall["y1"]) * dy) / length
        distance = abs((column["x"] - wall["x1"]) * dy - (column["y"] - wall["y1"]) * dx) / length
        return at if distance < EPS and -EPS <= at <= length + EPS else None

    standalone_columns = [column for column in drawn_columns or []
                          if not any(column_distance(column, wall) is not None for wall in walls)]

    def add(wall, start, size, kind, opening=None):
        recipe = recipes.get((kind, Decimal(str(round(size, 6)))))
        if recipe is None:
            issue(opening or wall, f"No hay receta para {kind.lower()} de {size:g} m.")
            return
        length = math.hypot(wall["x2"] - wall["x1"], wall["y2"] - wall["y1"])
        ux, uy = (wall["x2"] - wall["x1"]) / length, (wall["y2"] - wall["y1"]) / length
        segments.append({"wall_id": wall["id"], "object_id": (opening or wall)["id"],
            "label": wall["label"] or wall["id"], "kind": kind, "length": size, "start": start,
            "row": recipe.row, "source": recipe.source_label, "tp50": recipe.tp50, "tp37": recipe.tp37,
            "x1": round(wall["x1"] + start * ux, 6), "y1": round(wall["y1"] + start * uy, 6),
            "x2": round(wall["x1"] + (start + size) * ux, 6),
            "y2": round(wall["y1"] + (start + size) * uy, 6)})

    for wall in walls:
        length = math.hypot(wall["x2"] - wall["x1"], wall["y2"] - wall["y1"])
        h = round(wall["height"], 6)
        heights.add(h)
        if h not in (2.5, 2.7, 2.9):
            issue(wall, "La receta admite alturas de referencia 2,50, 2,70 o 2,90 m.")
        if abs(wall['thickness']-.12)<EPS:
            families.add('12')
        elif abs(wall['thickness']-.10)<EPS:
            families.add('10')
            if h!=2.5: issue(wall, 'Las paredes de 10 cm solo admiten altura 2,50 m y no usan vigabloques.')
            if settings.get('floor_level',1)==2: issue(wall, 'Segundo piso: usa bloques de 12 cm con columnas.')
        else:
            issue(wall, 'Elige la familia de 12 cm o de 10 cm; no se escala la receta por espesor.')
        if not modular(length):
            issue(wall, f"Largo de {length:.3f} m: debe ser múltiplo de 0,50 m para modular.")
            continue
        own = sorted([o for o in openings if o["wall_id"] == wall["id"]], key=lambda o: o["offset"])
        # Dos aberturas apiladas no tienen una receta combinada aunque no se solapen en altura.
        if any(a["offset"] + a["width"] > b["offset"] + EPS for a, b in zip(own, own[1:])):
            issue(wall, "No hay receta para aberturas superpuestas en el mismo tramo horizontal.")
            continue
        cuts = {0.0, round(length, 6)}
        for column in drawn_columns or []:
            distance = column_distance(column, wall)
            if distance is None:
                continue
            if not modular(distance):
                issue(column, "La columna debe caer en un múltiplo de 0,50 m desde el inicio de la pared.")
            if any(o["offset"] + EPS < distance < o["offset"] + o["width"] - EPS for o in own):
                issue(column, "La columna atraviesa una puerta o ventana. Colócala en un extremo del módulo.")
            cuts.add(round(max(0, min(length, distance)), 6))
        for other in walls:
            if other["id"] == wall["id"]:
                continue
            for distance in connection_distances(wall, other):
                if not modular(distance):
                    issue(wall, "Un encuentro con otra pared no cae en un múltiplo de 0,50 m.")
                if any(o["offset"] + EPS < distance < o["offset"] + o["width"] - EPS for o in own):
                    issue(wall, "Un encuentro de paredes atraviesa un módulo de puerta o ventana.")
                cuts.add(round(distance, 6))
        for opening in own:
            if not modular(opening["offset"]) or not modular(opening["width"]):
                issue(opening, "Posición y largo del módulo deben ser múltiplos de 0,50 m; no son medidas libres del vano.")
            if opening['kind']=='door':
                kind = {.5:'Puerta',1:'Puerta',1.5:'Puerta',2:'Puerta estándar',3:'Puerta amplia'}.get(opening['width'])
                if kind is None:
                    issue(opening, 'Las puertas admiten módulos de 0,50, 1, 1,50, 2 o 3 m. Revisa esta puerta sin cambiarla automáticamente.')
                    continue
            else:
                kind = KINDS[opening.get('panel_type','regular')]
            add(wall, opening["offset"], opening["width"], kind, opening)
            cuts.update((round(opening["offset"], 6), round(opening["offset"] + opening["width"], 6)))
        points = sorted(cuts)
        for start, end in zip(points, points[1:]):
            if any(o["offset"] - EPS <= (start + end) / 2 <= o["offset"] + o["width"] + EPS for o in own):
                continue
            remaining = end - start
            while remaining > EPS:
                size = min(float(settings["max_span"]), round(remaining, 6))
                add(wall, start, size, "Completo")
                start += size
                remaining -= size
    if not walls:
        families.add(settings.get('block_family', '12'))
        if settings.get('floor_level', 1) == 2 and '10' in families:
            issues.append({'object_id':None, 'label':'Segundo piso',
                           'message':'Segundo piso: usa bloques de 12 cm con columnas.'})
    if len(heights) > 1:
        issues.append({"object_id": None, "label": "Proyecto", "message": "Usa una misma altura de referencia en todas las paredes; no hay receta validada para alturas mixtas."})
    if len(families)>1:
        issues.append({'object_id':None,'label':'Proyecto','message':'Usa una misma familia de bloques (12 o 10 cm) en el croquis para obtener un desglose coherente.'})
    if issues:
        return {"status": "incomplete", "items": [], "details": [], "segments": [], "column_positions": [],
                "issues": issues, "warnings": ["No se presenta un total parcial como lista completa. Corrige las medidas señaladas."],
                "notice": "Cálculo pendiente de modulación."}
    counts = {r.key: 0 for r in RECIPES}
    for segment in segments:
        counts[f'panel_{segment["row"]}'] += 1
    layers = {2.5: 0, 2.7: 1, 2.9: 2}.get(next(iter(heights), 2.5), 0)
    if drawn_columns is not None:
        settings["linear_columns"] = sum(c["column_type"] == "C" for c in drawn_columns)
        settings["t_columns"] = sum(c["column_type"] == "E" for c in drawn_columns)
    result = calculate_house({**counts, **settings, "height": layers, "column_mode": "manual", "block_family": next(iter(families), "12")}, beam_lengths=beam_runs(walls))
    nodes = {}
    for segment in segments:
        for n in (1, 2):
            xy = (segment[f"x{n}"], segment[f"y{n}"])
            # Una posición compartida cuenta una vez aunque varias paredes lleguen invertidas.
            key = (round(xy[0], 5), round(xy[1], 5))
            nodes.setdefault(key, {"x": xy[0], "y": xy[1]})
    warnings = list(result["warnings"])
    if standalone_columns:
        warnings.append(f"{len(standalone_columns)} columna(s) independiente(s), fuera de paredes: se incluyen en la cantidad C/E. No dividen paños ni agregan paredes; su ubicación y función deben revisarse en el proyecto.")
    missing_columns = []
    if drawn_columns is not None:
        placed = {(round(c["x"], 5), round(c["y"], 5)) for c in drawn_columns}
        missing_columns = [p for key, p in nodes.items() if key not in placed]
        if missing_columns:
            warnings.append(f"Faltan columnas por colocar en {len(missing_columns)} límites de paño propuestos. Las cantidades C/E corresponden únicamente a las dibujadas.")
        warnings.append("Se cuentan las columnas dibujadas, una vez por posición. No se suman las cantidades manuales de configuración. Confirma la clasificación C/E del proyecto.")
    elif segments:
        warnings.append(f"{len(nodes)} ubicaciones de columna propuestas por esta división; su tipo debe confirmarse e ingresarse manualmente.")
        if result["columns"] and result["columns"] != len(nodes):
            warnings.append("Las columnas ingresadas no coinciden con las ubicaciones propuestas. Revisa la división y los encuentros.")
    if any(segment["length"] == 2 for segment in segments):
        warnings.append("Se usan recetas de 2 m del Excel; confirmar su aplicación al sistema y proyecto.")
    warnings.append("Largos y aberturas se interpretan como referencias modulares dibujadas. No se ha confirmado su equivalencia exacta a ejes de columnas ni a vanos libres.")
    columns_pending = bool(missing_columns) if drawn_columns is not None else bool(segments) and result["columns"] == 0
    if settings.get('floor_level',1)==2 and columns_pending:
        return {'status':'incomplete','items':[],'details':[],'segments':[],'column_positions':[],
                'issues':[{'object_id':None,'label':'Segundo piso','message':'Confirma y completa las columnas del proyecto de segundo piso.'}],
                'warnings':warnings,'notice':'Columnas de segundo piso pendientes.'}
    return {"status": "ready", "columns_pending": columns_pending, "version": result["version"], "segments": segments,
        "block_family": result["block_family"], "block_long_name": result["block_long_name"], "block_short_name": result["block_short_name"],
        "weight_note": "Peso de los productos de 10 cm pendiente de confirmar." if result["block_family"]=="10" else "Peso pendiente de confirmar las cantidades de columnas.",
        "beam_layers": result["beam_layers"], "beam_details": result["beam_details"], "beam_basis": result["beam_basis"],
        "column_mode": "drawn" if drawn_columns is not None else "manual",
        "drawn_column_count": len(drawn_columns or []), "standalone_column_count": len(standalone_columns),
        "missing_column_positions": missing_columns,
        "column_positions": list(nodes.values()), "issues": [], "warnings": warnings,
        "items": [{"sku": "", "name": label, "quantity": None if columns_pending and drawn_columns is None and label.startswith("Columna") else quantity, "unit": unit,
                   "source": "Ficha N-12: 40 cm; aclaración 22-10-2026 y redondeo superior por pared" if label=="Vigabloque" else "Receta del modulador TicoBlock", "is_demo": False}
                  for label, quantity, unit in result["items"]],
        "details": result["details"], "meters": result["meters"], "panels": result["panels"],
        "weight": None if columns_pending else result["weight"],
        "notice": "Bloques según Excel; vigabloques con regla actualizada del 22-10-2026; división de paños propuesta para revisión. Columnas dibujadas o cantidades manuales según el croquis; precios de 3R consultados por separado cuando la conexión está habilitada."}
