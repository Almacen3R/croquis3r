import json
import shutil
import subprocess
import time
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections
from django.utils import timezone
from PIL import Image

from sketches.models import RenderJob, RenderWorker
from sketches.rendering import render_path, worker_available


def heartbeat():
    RenderWorker.objects.update_or_create(pk=1, defaults={'heartbeat': timezone.now()})


def claim_job():
    # Compare-and-swap works on PostgreSQL and local SQLite. No duplicate claiming.
    for pk in RenderJob.objects.filter(status='queued').order_by('created_at').values_list('pk', flat=True)[:10]:
        if RenderJob.objects.filter(pk=pk, status='queued').update(status='running', started_at=timezone.now()):
            return RenderJob.objects.get(pk=pk)
    return None


def run_job(job):
    output = render_path(job)
    output.parent.mkdir(parents=True, exist_ok=True)
    scene = output.parent / 'scene.json'
    scene.write_text(json.dumps(job.scene, allow_nan=False), encoding='utf-8')
    script = settings.BASE_DIR / 'src/sketches/render_blender.py'
    command = [str(settings.BLENDER_BINARY), '--background', '--factory-startup', '--disable-autoexec',
               '--threads', '2', '--python-exit-code', '1', '--python', str(script), '--', str(scene), str(output)]
    process = None
    try:
        with (output.parent / 'blender.log').open('wb') as log:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
            deadline = time.monotonic() + settings.RENDER_TIMEOUT
            while process.poll() is None:
                heartbeat()
                if time.monotonic() >= deadline:
                    raise TimeoutError('Render deadline')
                time.sleep(1)
            if process.returncode != 0 or not output.is_file() or output.stat().st_size < 100:
                raise RuntimeError('Blender did not produce an image')
            with Image.open(output) as image:
                if image.format != 'PNG' or image.size != (1280, 960):
                    raise RuntimeError('Invalid rendered image')
                image.verify()
        RenderJob.objects.filter(pk=job.pk, status='running').update(status='ready', finished_at=timezone.now(), error='')
    except (OSError, RuntimeError, TimeoutError) as exc:
        RenderJob.objects.filter(pk=job.pk, status='running').update(status='failed', finished_at=timezone.now(),
            error='La imagen excedió el tiempo disponible. Puedes volver a intentarlo.' if isinstance(exc, TimeoutError)
                  else 'No se pudo generar la imagen. La vista 3D y el croquis siguen disponibles.')
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait(timeout=15)


class Command(BaseCommand):
    help = 'Consume the private Blender rendering queue (one task at a time).'

    def add_arguments(self, parser):
        parser.add_argument('--once', action='store_true')
        parser.add_argument('--check', action='store_true')

    def handle(self, *args, **options):
        if options['check']:
            if not worker_available():
                raise CommandError('Render worker unavailable')
            return
        if not shutil.which(str(settings.BLENDER_BINARY)):
            raise CommandError('Configure BLENDER_BINARY con un ejecutable Blender disponible.')
        self.stdout.write('Trabajador de imágenes listo. Una tarea a la vez.')
        while True:
            close_old_connections()
            heartbeat()
            RenderJob.objects.filter(status='running', started_at__lt=timezone.now()-timedelta(
                seconds=settings.RENDER_TIMEOUT+60)).update(status='failed', finished_at=timezone.now(),
                error='La generación se interrumpió. Puedes solicitar una nueva imagen.')
            job = claim_job()
            if job:
                self.stdout.write(f'Generando {job.pk}', ending='\n')
                try:
                    run_job(job)
                except OSError:
                    RenderJob.objects.filter(pk=job.pk).update(status='failed', finished_at=timezone.now(),
                        error='El almacenamiento de imágenes no está disponible. Intenta más tarde.')
            if options['once']:
                return
            time.sleep(3)
