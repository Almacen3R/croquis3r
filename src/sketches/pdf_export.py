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


def materials_pdf(title, rows, pricing=None, warnings=()):
    """Render trusted, recalculated quantities; prices never come from the browser."""
    from xml.sax.saxutils import escape
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    styles = getSampleStyleSheet()
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=32, leftMargin=32,
                            topMargin=32, bottomMargin=32, title=title, author='Croquis3R')
    para = lambda text: Paragraph(escape(str(text)), styles['Normal'])
    story = [Paragraph('Croquis3R · Lista de materiales', styles['Title']), para(title), Spacer(1, 12)]
    priced = pricing is not None
    money = lambda value: 'Pendiente' if value is None else f'{value:,.2f}'
    headers = ['Material', 'Unidad', 'Cantidad'] + (['Precio CRC', 'Importe CRC'] if priced else [])
    data = [[para(value) for value in headers]]
    for row in rows:
        description = row['name']
        if priced and row.get('reason'):
            description += ' · ' + row['reason']
        values = [description, row['unit'], 'Pendiente' if row['quantity'] is None else row['quantity']]
        if priced:
            values += [money(row.get('unit_price')), money(row.get('amount'))]
        data.append([para(value) for value in values])
    table = Table(data, colWidths=[190, 83, 70, 88, 100] if priced else [365, 85, 81], repeatRows=1)
    table.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e8efdf')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'), ('BOTTOMPADDING', (0,0), (-1,-1), 9),
        ('TOPPADDING', (0,0), (-1,-1), 9), ('LINEBELOW', (0,0), (-1,-1), .3, colors.lightgrey)]))
    story += [table, Spacer(1, 14)]
    if priced:
        label = 'Total de artículos listados' if pricing.get('complete') else 'Subtotal parcial con precio'
        story += [para(f"{label}: CRC {money(pricing.get('subtotal_with_prices'))}"),
                  para('Importes finales con IVA. Los pendientes no se incluyen en el subtotal.'),
                  para(f"Consulta de precios: {pricing.get('fetched_display') or 'no disponible'}"),
                  para(pricing.get('notice', ''))]
    story += [Spacer(1, 12), para('Estimación de materiales TicoBlock para revisión; no incluye todos los materiales de la casa.')]
    story += [para(warning) for warning in warnings]
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
