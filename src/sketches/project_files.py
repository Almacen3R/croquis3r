"""Formato portátil de croquis. Nunca importa propietarios ni IDs de registros."""
import json

from .domain import InvalidDocument, validate_document, validate_door_catalog

MAX_PROJECT_BYTES = 1_048_576


def reject_nonfinite(value):
    raise ValueError(f'Constante JSON inválida: {value}')


def read_project(upload, articles):
    if upload is None:
        raise InvalidDocument('Selecciona un archivo de proyecto .croquis3r.json.')
    if upload.size > MAX_PROJECT_BYTES:
        raise InvalidDocument('El archivo de proyecto admite hasta 1 MB.')
    try:
        data = json.loads(upload.read(MAX_PROJECT_BYTES + 1).decode('utf-8-sig'),
                          parse_constant=reject_nonfinite)
    except (ValueError, UnicodeDecodeError, RecursionError):
        raise InvalidDocument('El archivo no contiene un proyecto JSON válido de Croquis3R.') from None
    if not isinstance(data, dict) or data.get('format') != 'croquis3r-project' or type(data.get('format_version')) is not int or data['format_version'] != 1:
        raise InvalidDocument('Formato de proyecto no compatible. Usa un archivo descargado desde Croquis3R (versión 1).')
    if data.get('units', 'm') != 'm':
        raise InvalidDocument('El proyecto debe estar expresado en metros.')
    name = data.get('name')
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 160:
        raise InvalidDocument('El nombre del proyecto debe tener de 1 a 160 caracteres.')
    doc = data.get('document')
    if not isinstance(doc, dict) or not isinstance(doc.get('objects'), list):
        raise InvalidDocument('El archivo no contiene un croquis válido.')
    # Los IDs del catálogo pueden diferir entre local y producción. Usar SKU.
    references = data.get('articles', [])
    if not isinstance(references, list) or len(references) > 6000:
        raise InvalidDocument('Referencias de artículos inválidas.')
    by_sku = {article.sku: article.id for article in articles.values()}
    mapping = {}
    for ref in references:
        if not isinstance(ref, dict) or type(ref.get('id')) is not int or ref['id'] < 1 or ref['id'] in mapping or not isinstance(ref.get('sku'), str):
            raise InvalidDocument('Referencias de artículos inválidas o repetidas.')
        if ref['sku'] not in by_sku:
            raise InvalidDocument(f'El artículo {ref["sku"][:80]} no existe o está inactivo en este catálogo. No se importó el proyecto.')
        mapping[ref['id']] = by_sku[ref['sku']]
    for obj in doc['objects']:
        if not isinstance(obj, dict) or not isinstance(obj.get('assignments', []), list):
            raise InvalidDocument('Objeto o asignaciones inválidos.')
        for assignment in obj.get('assignments', []):
            if not isinstance(assignment, dict) or type(assignment.get('article_id')) is not int or assignment['article_id'] not in mapping:
                raise InvalidDocument('Falta la referencia SKU de un artículo asignado. No se importó el proyecto.')
            assignment['article_id'] = mapping[assignment['article_id']]
    # Siempre como proyecto independiente del usuario actual, incluso si el
    # archivo procede de una plantilla. Sin restaurar ID/revisión/propietario.
    return name.strip(), validate_door_catalog(validate_document(doc, articles))
