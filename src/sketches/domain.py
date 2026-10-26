"""Geometría en metros y cálculo reproducible; no depende del navegador ni de IA."""
from decimal import Decimal, InvalidOperation, ROUND_CEILING


class InvalidDocument(ValueError):
    pass


def number(value, label, minimum=0, maximum=1000):
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise InvalidDocument(f"{label}: ingrese un número.")
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        raise InvalidDocument(f"{label}: número inválido.") from None
    if not result.is_finite() or not Decimal(str(minimum)) <= result <= Decimal(str(maximum)):
        raise InvalidDocument(f"{label}: debe estar entre {minimum} y {maximum}.")
    return result


def identifier(value):
    if not isinstance(value, str) or not value or len(value) > 80:
        raise InvalidDocument("Identificador de objeto inválido.")
    return value


def positive_int(value, label):
    if type(value) is not int or value < 1:
        raise InvalidDocument(f"{label}: identificador inválido.")
    return value


def validate_document(document, articles):
    if not isinstance(document, dict) or document.get("version") != 1:
        raise InvalidDocument("Formato de croquis no compatible (se requiere versión 1).")
    objects = document.get("objects")
    if not isinstance(objects, list) or len(objects) > 300:
        raise InvalidDocument("El croquis admite hasta 300 objetos.")
    cleaned, seen = [], set()
    for obj in objects:
        if not isinstance(obj, dict):
            raise InvalidDocument("Objeto inválido.")
        oid = identifier(obj.get("id"))
        if oid in seen:
            raise InvalidDocument("Hay identificadores de objeto repetidos.")
        seen.add(oid)
        kind = obj.get("kind")
        if kind not in ("wall", "door", "window"):
            raise InvalidDocument("Tipo de objeto desconocido.")
        label = obj.get("label", "")
        if not isinstance(label, str) or len(label) > 100:
            raise InvalidDocument("El nombre del objeto admite hasta 100 caracteres.")
        item = {"id": oid, "kind": kind, "label": label, "assignments": []}
        if kind == "wall":
            for key in ("x1", "y1", "x2", "y2"):
                item[key] = float(number(obj.get(key), key, -100, 100))
            if wall_length(item) < Decimal("0.1"):
                raise InvalidDocument("Cada pared debe medir al menos 0,10 m.")
            item["height"] = float(number(obj.get("height"), "Altura", 0.1, 10))
            item["thickness"] = float(number(obj.get("thickness"), "Espesor", 0.05, 1))
        else:
            item["wall_id"] = identifier(obj.get("wall_id"))
            if "door_rotation" in obj:
                if kind != "door" or type(obj["door_rotation"]) is not int or obj["door_rotation"] not in range(4):
                    raise InvalidDocument("Orientación de apertura de puerta inválida.")
                item["door_rotation"] = obj["door_rotation"]
            if "panel_type" in obj:
                if obj["panel_type"] not in ("regular", "kitchen", "bath") or kind != "window":
                    raise InvalidDocument("Tipo de paño de ventana desconocido.")
                item["panel_type"] = obj["panel_type"]
            for key, lo, hi in (("offset", 0, 200), ("width", 0.1, 20), ("height", 0.1, 10), ("sill", 0, 10)):
                item[key] = float(number(obj.get(key), key, lo, hi))
            if kind == "door" and item["sill"] != 0:
                raise InvalidDocument("Una puerta debe empezar a nivel del piso.")
        assignments = obj.get("assignments", [])
        if not isinstance(assignments, list) or len(assignments) > 20:
            raise InvalidDocument("Cada objeto admite hasta 20 artículos.")
        article_ids = set()
        for a in assignments:
            if not isinstance(a, dict):
                raise InvalidDocument("Asignación de artículo inválida.")
            aid = positive_int(a.get("article_id"), "Artículo")
            if aid not in articles or aid in article_ids:
                raise InvalidDocument("Artículo inexistente, inactivo o repetido en el mismo objeto.")
            article_ids.add(aid)
            if a.get("basis") not in ("area", "length", "object"):
                raise InvalidDocument("Base de cálculo desconocida.")
            item["assignments"].append({"article_id": aid, "basis": a["basis"],
                "factor": str(number(a.get("factor"), "Cantidad por unidad", 0.0001, 10000)),
                "waste_percent": str(number(a.get("waste_percent", 0), "Desperdicio %", 0, 100))})
        cleaned.append(item)
    walls = {o["id"]: o for o in cleaned if o["kind"] == "wall"}
    openings = [o for o in cleaned if o["kind"] != "wall"]
    for opening in openings:
        wall = walls.get(opening["wall_id"])
        if not wall:
            raise InvalidDocument("Cada puerta o ventana debe pertenecer a una pared existente.")
        if D(opening["offset"]) + D(opening["width"]) > wall_length(wall):
            raise InvalidDocument("Una puerta o ventana se sale del largo de su pared.")
        if D(opening["sill"]) + D(opening["height"]) > D(wall["height"]):
            raise InvalidDocument("Una puerta o ventana supera la altura de su pared.")
    for i, a in enumerate(openings):
        for b in openings[i + 1:]:
            if a["wall_id"] == b["wall_id"] and interval_overlap(a["offset"], a["width"], b["offset"], b["width"]) and interval_overlap(a["sill"], a["height"], b["sill"], b["height"]):
                raise InvalidDocument("Hay puertas o ventanas superpuestas en una pared.")
    wall_list = list(walls.values())
    for i, a in enumerate(wall_list):
        for b in wall_list[i + 1:]:
            dx, dy = D(a["x2"]) - D(a["x1"]), D(a["y2"]) - D(a["y1"])
            if all(dx * (D(b[f"y{n}"]) - D(a["y1"])) == dy * (D(b[f"x{n}"]) - D(a["x1"])) for n in (1, 2)):
                axis = "x" if abs(dx) >= abs(dy) else "y"
                a1, a2 = sorted((D(a[axis + "1"]), D(a[axis + "2"])))
                b1, b2 = sorted((D(b[axis + "1"]), D(b[axis + "2"])))
                if max(a1, b1) < min(a2, b2):
                    raise InvalidDocument("Hay paredes superpuestas. Muévalas para evitar contar material dos veces.")
    result = {"version": 1, "objects": cleaned}
    if "columns" in document:
        columns = document["columns"]
        if not isinstance(columns, list) or len(columns) > 300:
            raise InvalidDocument("El croquis admite hasta 300 columnas dibujadas.")
        result["columns"] = []
        positions = set()
        for column in columns:
            if not isinstance(column, dict):
                raise InvalidDocument("Columna inválida.")
            cid = identifier(column.get("id"))
            if cid in seen:
                raise InvalidDocument("Hay identificadores de objeto repetidos.")
            seen.add(cid)
            if column.get("column_type") not in ("C", "E"):
                raise InvalidDocument("Selecciona columna C lineal o E esquina/cruz.")
            label = column.get("label", "")
            if not isinstance(label, str) or len(label) > 100:
                raise InvalidDocument("El nombre de la columna admite hasta 100 caracteres.")
            x = float(number(column.get("x"), "Columna X", -100, 100))
            y = float(number(column.get("y"), "Columna Y", -100, 100))
            position = (round(x, 5), round(y, 5))
            if position in positions:
                raise InvalidDocument("Hay dos columnas en la misma posición.")
            positions.add(position)
            result["columns"].append({"id": cid, "kind": "column", "label": label,
                                      "x": x, "y": y, "column_type": column["column_type"]})
    if "ticoblock" in document:
        result["ticoblock"] = validate_ticoblock_settings(document["ticoblock"])
    return result


def validate_ticoblock_settings(settings):
    if not isinstance(settings, dict):
        raise InvalidDocument("Configuración TicoBlock inválida.")
    span = str(settings.get("max_span", "1.5"))
    if span not in ("0.5", "1", "1.5", "2"):
        raise InvalidDocument("El largo preferido debe ser 2, 1,50, 1 o 0,50 m.")
    level = settings.get('floor_level', 1)
    if isinstance(level, bool) or str(level) not in ('1','2'):
        raise InvalidDocument('El nivel del proyecto debe ser primera planta o segundo piso.')
    result = {"max_span": span}
    if 'block_family' in settings:
        if str(settings['block_family']) not in ('10','12'):
            raise InvalidDocument('La familia debe ser de 10 o de 12 cm.')
        result['block_family'] = str(settings['block_family'])
    if 'floor_level' in settings:
        result['floor_level'] = int(level)
    for key in ("linear_columns", "t_columns"):
        value = number(settings.get(key, 0), "Columnas", 0, 10000)
        if value != value.to_integral_value():
            raise InvalidDocument("Las columnas deben ser cantidades enteras.")
        result[key] = int(value)
    return result


def D(value):
    return Decimal(str(value))


def wall_length(wall):
    dx, dy = D(wall["x2"]) - D(wall["x1"]), D(wall["y2"]) - D(wall["y1"])
    return (dx * dx + dy * dy).sqrt()


def interval_overlap(start_a, size_a, start_b, size_b):
    return max(D(start_a), D(start_b)) < min(D(start_a) + D(size_a), D(start_b) + D(size_b))


def calculate(document, articles):
    document = validate_document(document, articles)
    totals, details, warnings = {}, [], []
    for obj in document["objects"]:
        if obj["kind"] == "wall":
            length = wall_length(obj)
            area = length * D(obj["height"]) - sum((D(o["width"]) * D(o["height"]) for o in document["objects"] if o.get("wall_id") == obj["id"]), Decimal(0))
        else:
            length, area = D(obj["width"]), D(obj["width"]) * D(obj["height"])
        if not obj["assignments"]:
            warnings.append(f'{obj["label"] or obj["id"]}: sin artículos asignados.')
        for rule in obj["assignments"]:
            base = {"area": area, "length": length, "object": Decimal(1)}[rule["basis"]]
            raw = base * D(rule["factor"]) * (1 + D(rule["waste_percent"]) / 100)
            quantity = int(raw.to_integral_value(rounding=ROUND_CEILING))
            article = articles[rule["article_id"]]
            row = totals.setdefault(article.id, {"article_id": article.id, "sku": article.sku,
                "name": article.name, "unit": article.unit, "quantity": 0, "is_demo": article.is_demo})
            row["quantity"] += quantity
            details.append({"object_id": obj["id"], "label": obj["label"], "article_id": article.id,
                "basis": rule["basis"], "base": str(base), "factor": rule["factor"],
                "waste_percent": rule["waste_percent"], "unrounded": str(raw), "quantity": quantity})
    return {"items": list(totals.values()), "details": details, "warnings": warnings,
            "notice": "Estimación de prototipo. Reglas de ejemplo sin aprobación técnica; no es una cotización ni un plano constructivo."}


def validate_door_catalog(document):
    """Validate before saving; legacy documents remain readable without rewriting them."""
    for obj in document["objects"]:
        if obj["kind"] == "door" and number(obj["width"], "Módulo de puerta") not in {Decimal("0.5"), Decimal("1"), Decimal("1.5"), Decimal("2"), Decimal("3")}:
            raise InvalidDocument(f'{obj.get("label", "Puerta")}: módulo fuera de catálogo. Elija 0,50, 1, 1,50, 2 o 3 m. No se guardaron los cambios.')
    return document
