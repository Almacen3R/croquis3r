"""Distribución exacta de tramos en módulos; no infiere reglas estructurales."""
from decimal import Decimal

from .domain import InvalidDocument, number

SPAN_CHOICES = ("2", "1.5", "1", "0.5")


def suggest_panels(meters, preferred="2"):
    total = number(meters, "Metros de pared", .5, 200)
    preference = str(preferred)
    if preference not in SPAN_CHOICES:
        raise InvalidDocument("La preferencia debe ser 2, 1,50, 1 o 0,50 m.")
    if total % Decimal("0.5"):
        raise InvalidDocument("Los metros deben ser múltiplos de 0,50 m. No se redondea el largo del cliente.")
    remaining = total
    rows = []
    for length in SPAN_CHOICES[SPAN_CHOICES.index(preference):]:
        size = Decimal(length)
        quantity = int(remaining // size)
        if quantity:
            rows.append({"length": length, "quantity": quantity, "meters": str(size * quantity)})
        remaining -= size * quantity
    return {"meters": str(total), "preferred": preference, "rows": rows,
            "panels": sum(row["quantity"] for row in rows),
            "scope": "Un tramo continuo de pared completa o tapia. Distribuye cada lado por separado; puertas, ventanas y encuentros requieren ajustar los paños."}
