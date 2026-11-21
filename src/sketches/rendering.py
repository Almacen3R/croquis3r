"""Bounded data-only render jobs. No user scripts, paths, URLs or .blend files."""
import hashlib
import json
import math
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .domain import InvalidDocument, number, validate_presentation3d
from .models import RenderJob, RenderWorker


def fingerprint(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()


def worker_available():
    return settings.RENDER_ENABLED and RenderWorker.objects.filter(
        pk=1, heartbeat__gte=timezone.now()-timedelta(seconds=20)).exists()


def vector(value, low=-110, high=110):
    if not isinstance(value, list) or len(value) != 3:
        raise InvalidDocument('Vector de presentación inválido.')
    return [float(number(v, 'Medida 3D', low, high)) for v in value]


def validate_scene(data):
    if not isinstance(data, dict) or type(data.get('version')) is not int or data.get('version') != 1 or data.get('units') != 'm':
        raise InvalidDocument('Escena 3D incompatible.')
    result = {'version': 1, 'units': 'm', 'boxes': [], 'openings': [], 'details': [], 'floors': [], 'roof': {}}
    def boxes(key, roles, maximum):
        entries = data.get(key, [] if key == 'details' else None)
        if not isinstance(entries, list) or len(entries) > maximum:
            raise InvalidDocument('La presentación tiene demasiadas piezas.')
        for entry in entries:
            if not isinstance(entry, dict) or entry.get('kind' if key == 'openings' else 'role') not in roles:
                raise InvalidDocument('Pieza 3D inválida.')
            role_key = 'kind' if key == 'openings' else 'role'
            position = vector(entry.get('position'))
            size = vector(entry.get('size'), .001, 300)
            if size[1] > 15 or size[2] > 2:
                raise InvalidDocument('Pieza 3D fuera del tamaño permitido.')
            result[key].append({role_key: entry[role_key], 'position': position, 'size': size,
                'rotation': float(number(entry.get('rotation'), 'Giro', -math.tau, math.tau))})
    boxes('boxes', ('wall', 'frame', 'column'), 6000)
    boxes('openings', ('door', 'window'), 300)
    boxes('details', ('frame', 'door', 'metal', 'sill'), 4000)
    if not result['boxes']:
        raise InvalidDocument('La escena debe contener paredes o columnas.')
    floors = data.get('floors')
    if not isinstance(floors, list) or len(floors) > 600:
        raise InvalidDocument('Pisos inválidos.')
    vertices = 0
    for ring in floors:
        if not isinstance(ring, list) or not 3 <= len(ring) <= 1800:
            raise InvalidDocument('Contorno de piso inválido.')
        clean = []
        for point in ring:
            if not isinstance(point, dict):
                raise InvalidDocument('Punto de piso inválido.')
            clean.append({'x': float(number(point.get('x'), 'Piso X', -100, 100)),
                          'y': float(number(point.get('y'), 'Piso Y', -100, 100))})
        result['floors'].append(clean)
        vertices += len(clean)
    roof = data.get('roof', {})
    if not isinstance(roof, dict):
        raise InvalidDocument('Techo inválido.')
    for key in ('surfaces', 'closures'):
        faces = roof.get(key, [])
        if not isinstance(faces, list) or len(faces) > 5000:
            raise InvalidDocument('Techo demasiado complejo.')
        result['roof'][key] = []
        for face in faces:
            if not isinstance(face, list) or not 3 <= len(face) <= 1800:
                raise InvalidDocument('Cara de techo inválida.')
            result['roof'][key].append([vector(p) for p in face])
            vertices += len(face)
    if vertices > 20000:
        raise InvalidDocument('La presentación tiene demasiados vértices.')
    if 'camera' in data:
        camera = data['camera']
        if not isinstance(camera, dict):
            raise InvalidDocument('Cámara de presentación inválida.')
        position, target = vector(camera.get('position'), -2000, 2000), vector(camera.get('target'), -110, 110)
        if math.dist(position, target) < .05:
            raise InvalidDocument('La cámara debe mirar hacia un punto diferente.')
        result['camera'] = {'position': position, 'target': target,
                            'fov': float(number(camera.get('fov'), 'Ángulo de cámara', 15, 100))}
    result['settings'] = validate_presentation3d(data.get('settings', {}))
    return result


def render_path(job):
    # UUID assigned by the server. Never accept an output path from JSON or a URL.
    return settings.RENDER_ROOT / str(job.pk) / 'render.png'


def expire_overdue_jobs(records):
    """A stopped worker must not leave a running job blocking an account forever."""
    from django.db.models import Q
    now = timezone.now()
    cutoff = now - timedelta(seconds=settings.RENDER_TIMEOUT + 60)
    return records.filter(status='running').filter(
        Q(started_at__lt=cutoff) | Q(started_at__isnull=True, created_at__lt=cutoff)
    ).update(status='failed', finished_at=now,
             error='La generación superó el tiempo disponible o se interrumpió. Puedes solicitar una nueva imagen.')


def serialize_job(job):
    return {'id': str(job.pk), 'title': job.title, 'status': job.status,
        'error': job.error, 'created_at': job.created_at.isoformat(),
        'started_at': job.started_at.isoformat() if job.started_at else None,
        'finished_at': job.finished_at.isoformat() if job.finished_at else None,
        'elapsed_seconds': max(0, int(((job.finished_at or timezone.now()) - (job.started_at or job.created_at)).total_seconds())),
        'sketch_revision': job.sketch_revision, 'fingerprint': job.fingerprint[:12],
        'image_url': f'/api/renders/{job.pk}/image/' if job.status == 'ready' else None}
