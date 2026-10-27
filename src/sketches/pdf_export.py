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
