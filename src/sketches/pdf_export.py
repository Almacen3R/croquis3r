"""PDF de una lámina del croquis, sin almacenar archivos ni tocar proyectos."""
from io import BytesIO

from PIL import Image, UnidentifiedImageError
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

from .domain import InvalidDocument

MAX_PNG_BYTES = 8 * 1024 * 1024
MAX_SIDE = 2400


def panel_calculation_rows(calculation):
    """Group the server's recipes into a compact, auditable explanation."""
    return [{'label': f"{row['kind']} - {str(row['length']).replace('.', ',')} m",
             'panels': row['quantity'], 'long_each': row['tp50_each'], 'short_each': row['tp37_each'],
             'long_total': row['tp50'], 'short_total': row['tp37']}
            for row in calculation.get('details', [])]


def other_calculation_rows(calculation):
    """Explain the existing server totals without introducing new rounding rules."""
    from collections import Counter
    from decimal import Decimal
    if calculation.get('block_family') != '12' or 'wall_factor' not in calculation:
        return []
    number = lambda value: format(Decimal(str(value)).quantize(Decimal('.001')).normalize(), 'f').replace('.', ',')
    layers = calculation['beam_layers']
    beam_groups = Counter((Decimal(str(row['length'])), row['pieces']) for row in calculation['beam_details'])
    beam_parts = []
    pieces = 0
    for (length, count), repeats in beam_groups.items():
        text = f"{number(length)} m / 0,40 m = {number(length / Decimal('.40'))} -> {count} piezas"
        if repeats > 1:
            text = f"{repeats} paredes de {number(length)} m: ({text}) x {repeats}"
        beam_parts.append(text)
        pieces += count * repeats
    beam_text = '; '.join(beam_parts) + f". {pieces} x {layers} hilada(s) = {pieces * layers} unidades. Redondeo hacia arriba por pared continua."
    factors = Counter()
    for row in calculation.get('details', []):
        if row['quantity'] and row['steel']:
            factors[Decimal(str(row['steel'])) / row['quantity']] += row['quantity']
    wall_terms = ' + '.join(f'{quantity} x {number(factor)}' for factor, quantity in factors.items()) or '0'
    wall_text = f"{wall_terms} = {number(calculation['wall_factor'])} -> {calculation['wall_steel']} equivalentes. Redondeo del Excel."
    meters = Decimal(str(calculation['meters']))
    beam_steel_text = (f"{number(meters)} m / 6 = {number(meters / 6)} -> {calculation['steel_one']} por hilada; "
                       f"{calculation['steel_one']} x {layers} = {calculation['beam_steel']} equivalentes. Redondeo del Excel.")
    blocks = sum(row['tp50'] + row['tp37'] for row in calculation.get('details', []))
    mortar_text = f"{blocks} bloques / 20 = {number(Decimal(blocks) / 20)} -> {calculation['mortar']} sacos de 40 kg. Redondeo hacia arriba."
    return [('Vigabloques', beam_text), ('Varilla 3/8 - pared', wall_text),
            ('Varilla 3/8 - viga', beam_steel_text), ('Mortero', mortar_text)]


def materials_pdf(title, rows, pricing=None, warnings=(), calculation=None):
    """Render recalculated quantities and recipe counts; never trust browser totals."""
    from xml.sax.saxutils import escape
    from django.utils import timezone
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    styles = getSampleStyleSheet()
    body = ParagraphStyle('Compact', parent=styles['Normal'], fontSize=9, leading=12)
    small = ParagraphStyle('Small', parent=body, fontSize=8, leading=10, textColor=colors.HexColor('#555555'))
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=32, leftMargin=32,
                            topMargin=28, bottomMargin=28, title=title, author='Croquis3R')
    para = lambda text: Paragraph(escape(str(text)), body)
    number = lambda value: f'{float(value):g}'.replace('.', ',')
    calculation = calculation or {}
    story = [Paragraph('Croquis3R - Lista de materiales', styles['Title']), para(title),
             para(f"Fecha: {timezone.localtime():%d/%m/%Y %H:%M}"), Spacer(1, 6)]
    if calculation:
        story += [para(f"Altura del cálculo: {calculation.get('height_label', 'Pendiente')} | "
                       f"Espesor: {calculation.get('block_family', '12')} cm"),
                  para(f"Largo total: {number(calculation.get('meters', 0))} m | "
                       f"Paños: {calculation.get('panels', 0)}"), Spacer(1, 10)]
    priced = pricing is not None
    money = lambda value: 'Pendiente' if value is None else f'{value:,.2f}'
    headers = ['Material', 'Unidad', 'Cantidad'] + (['Precio CRC', 'Importe CRC'] if priced else [])
    data = [[para(value) for value in headers]]
    for row in rows:
        values = [row['name'], row['unit'], 'Pendiente' if row['quantity'] is None else row['quantity']]
        if priced:
            values += [money(row.get('unit_price')), money(row.get('amount'))]
        data.append([para(value) for value in values])
    table_style = TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#fff2a8')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6), ('LINEBELOW', (0,0), (-1,-1), .3, colors.lightgrey)])
    table = Table(data, colWidths=[190, 83, 60, 94, 104] if priced else [365, 85, 81], repeatRows=1)
    table.setStyle(table_style)
    story += [table, Spacer(1, 10)]
    if priced:
        label = 'Total de artículos listados' if pricing.get('complete') else 'Subtotal parcial con precio'
        story += [para(f"{label}: CRC {money(pricing.get('subtotal_with_prices'))}"),
                  para('IVA incluido.' if pricing.get('complete') else 'IVA incluido. Artículos pendientes excluidos del subtotal.'),
                  para(f"Consulta de precios: {pricing.get('fetched_display') or 'no disponible'}")]
    details = panel_calculation_rows(calculation)
    if details:
        long_name, short_name = calculation['block_long_name'], calculation['block_short_name']
        story += [Spacer(1, 10), Paragraph('Cómo se calcularon los bloques', styles['Heading2'])]
        detail_data = [[para(value) for value in ['Tipo de paño', 'Paños', 'Bloques por paño y aporte total']]]
        for row in details:
            explanation = (f"{row['panels']} x ({row['long_each']} {long_name} + {row['short_each']} {short_name}) "
                           f"= {row['long_total']} {long_name} + {row['short_total']} {short_name}")
            detail_data.append([para(row['label']), para(row['panels']), para(explanation)])
        detail_table = Table(detail_data, colWidths=[125, 45, 361], repeatRows=1)
        detail_table.setStyle(table_style)
        story.append(detail_table)
    other_rows = other_calculation_rows(calculation)
    if other_rows:
        story += [Spacer(1, 10), Paragraph('Cómo se calcularon los otros materiales', styles['Heading2'])]
        other_data = [[para('Material'), para('Cálculo')]]
        other_data += [[para(label), para(explanation)] for label, explanation in other_rows]
        other_table = Table(other_data, colWidths=[125, 406], repeatRows=1, splitInRow=1)
        other_table.setStyle(table_style)
        story.append(other_table)
    if calculation.get('columns_pending'):
        story += [Spacer(1, 6), para('Columnas pendientes de completar o confirmar.')]
    if calculation.get('block_family') == '10':
        story += [Spacer(1, 6), para('10 cm: mortero y acero pendientes de confirmar; sin vigabloques.')]
    story += [Spacer(1, 10), Paragraph(escape('Estimación de cerramientos. No incluye cimentación, techo ni rellenos. '
               'Varillas: equivalentes del Excel; cortes y traslapes por confirmar.'), small)]
    doc.build(story)
    output.seek(0)
    return output


def drawing_pdf(upload, title):
    if upload is None or not 0 < upload.size <= MAX_PNG_BYTES:
        raise InvalidDocument('La imagen del croquis debe ser PNG y pesar como máximo 8 MB.')
    data = upload.read(MAX_PNG_BYTES + 1)
    try:
        with Image.open(BytesIO(data), formats=['PNG']) as check:
            width, height = check.size
            if not 1 <= width <= MAX_SIDE or not 1 <= height <= MAX_SIDE or getattr(check, 'is_animated', False):
                raise InvalidDocument('La imagen debe ser un PNG estático de hasta 2400 × 2400 píxeles.')
            check.verify()
        with Image.open(BytesIO(data), formats=['PNG']) as decoded:
            decoded.load()
            rgba = decoded.convert('RGBA')
            image = Image.new('RGB', rgba.size, 'white')
            image.paste(rgba, mask=rgba.getchannel('A'))
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError, Image.DecompressionBombError) as exc:
        if isinstance(exc, InvalidDocument):
            raise
        raise InvalidDocument('No se pudo leer la imagen PNG del croquis. Vuelve a intentar la descarga.') from None
    page_width, page_height = landscape(A4) if width > height else A4
    margin = 12 * mm
    scale = min((page_width - 2 * margin) / width, (page_height - 2 * margin) / height)
    drawing_width, drawing_height = width * scale, height * scale
    output = BytesIO()
    pdf = Canvas(output, pagesize=(page_width, page_height), pageCompression=1)
    pdf.setTitle(title)
    pdf.setAuthor('Croquis3R')
    pdf.drawImage(ImageReader(image), (page_width-drawing_width)/2, (page_height-drawing_height)/2,
                  width=drawing_width, height=drawing_height)
    pdf.showPage()
    pdf.save()
    output.seek(0)
    return output
