"""Longitudes continuas para viga: no redondear de nuevo en cada paño o abertura."""
import math
from decimal import Decimal, ROUND_CEILING


def beam_runs(walls):
    groups = {}
    for wall in walls:
        dx, dy = wall['x2'] - wall['x1'], wall['y2'] - wall['y1']
        length = math.hypot(dx, dy)
        sign = 1 if dx > 1e-8 or (abs(dx) <= 1e-8 and dy > 0) else -1
        ux, uy = sign * dx / length, sign * dy / length
        fixed = -uy * wall['x1'] + ux * wall['y1']
        key = (round(ux, 6), round(uy, 6), round(fixed, 6))
        start, end = sorted(ux * wall[f'x{n}'] + uy * wall[f'y{n}'] for n in (1, 2))
        groups.setdefault(key, []).append((start, end))
    lengths = []
    for intervals in groups.values():
        start, end = sorted(intervals)[0]
        for a, b in sorted(intervals)[1:]:
            if a <= end + 1e-6:
                end = max(end, b)
            else:
                lengths.append(Decimal(str(round(end - start, 6))))
                start, end = a, b
        lengths.append(Decimal(str(round(end - start, 6))))
    return lengths


def pieces(length):
    return int((length / Decimal('0.40')).to_integral_value(rounding=ROUND_CEILING))
