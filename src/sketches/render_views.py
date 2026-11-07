from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import FileResponse, JsonResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.views.decorators.http import require_http_methods, require_GET

from .access import visible_to
from .domain import InvalidDocument, validate_document
from .models import RenderJob, Sketch
from .rendering import fingerprint, render_path, serialize_job, validate_scene, worker_available
from .views import api, payload, name, articles_by_id


@require_http_methods(['GET', 'POST'])
@api
def jobs(request):
    if request.method == 'GET':
        records = visible_to(RenderJob, request.user)
        if 'sketch_id' in request.GET:
            value = request.GET['sketch_id']
            if not value.isdecimal() or len(value) > 18:
                raise InvalidDocument('Referencia de proyecto inválida.')
            sketch = get_object_or_404(visible_to(Sketch, request.user), pk=int(value))
            records = records.filter(sketch=sketch)
        return JsonResponse({'enabled': settings.RENDER_ENABLED, 'available': worker_available(),
            'jobs': [serialize_job(job) for job in records[:10]]})
    if not worker_available():
        return JsonResponse({'error': 'El servicio de imágenes no está disponible en este momento. Puedes seguir usando la vista 3D.'}, status=503)
    data = payload(request)
    document = validate_document(data.get('document'), articles_by_id())
    scene = validate_scene(data.get('scene'))
    if scene['settings'] != document.get('presentation3d', {}):
        raise InvalidDocument('La presentación cambió. Abre nuevamente la vista 3D y vuelve a intentar.')
    sketch = None
    revision = None
    if data.get('sketch_id') is not None:
        if type(data['sketch_id']) is not int:
            raise InvalidDocument('Referencia de proyecto inválida.')
        sketch = get_object_or_404(visible_to(Sketch, request.user), pk=data['sketch_id'])
        if fingerprint(validate_document(sketch.document, articles_by_id())) == fingerprint(document):
            revision = sketch.revision
    with transaction.atomic():
        # Serialize submissions by the same user; two active jobs per account.
        get_user_model().objects.select_for_update().get(pk=request.user.pk)
        if RenderJob.objects.filter(owner=request.user, status__in=['queued', 'running']).count() >= 2:
            return JsonResponse({'error': 'Ya tienes dos imágenes en proceso. Espera a que terminen antes de generar otra.'}, status=429)
        job = RenderJob.objects.create(owner=request.user, sketch=sketch, sketch_revision=revision,
            title=name(data), document=document, scene=scene, fingerprint=fingerprint(document))
    return JsonResponse(serialize_job(job), status=202)


@require_GET
@api
def image(request, pk):
    job = get_object_or_404(visible_to(RenderJob, request.user), pk=pk, status='ready')
    try:
        stream = render_path(job).open('rb')
    except FileNotFoundError:
        raise Http404('La imagen ya no está disponible.') from None
    return FileResponse(stream, content_type='image/png', as_attachment=request.GET.get('download') == '1',
        filename=f'{slugify(job.title)[:70] or "casa"}-{job.fingerprint[:8]}.png')
