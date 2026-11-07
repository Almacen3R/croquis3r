import copy
import json
import tempfile
from pathlib import Path
from datetime import timedelta
from unittest.mock import patch, MagicMock
from PIL import Image

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import override_settings
from django.utils import timezone

from .domain import InvalidDocument, validate_document
from .management.commands.render_worker import claim_job, run_job
from .models import RenderJob, RenderWorker, Sketch
from .rendering import fingerprint, render_path, validate_scene
from .test_modulation import doc, wall
from .testing import AuthenticatedTestCase


def scene():
    return {'version':1,'units':'m','boxes':[{'role':'wall','position':[2,1.25,0],
        'size':[4,2.5,.12],'rotation':0}],'openings':[],'floors':[],
        'roof':{'surfaces':[],'closures':[]},'settings':{}}


@override_settings(RENDER_ENABLED=True)
class RenderTests(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()
        self.other = get_user_model().objects.create_user('other_render')
        RenderWorker.objects.create(pk=1, heartbeat=timezone.now())
        self.data = {'name':'Prueba render','document':{**doc(wall()),'presentation3d':{}},'scene':scene()}

    def post(self, data=None):
        return self.client.post('/api/renders/',json.dumps(data or self.data),content_type='application/json')

    def test_captures_owned_snapshot_and_revision_and_enforces_limit(self):
        sketch=Sketch.objects.create(owner=self.user,name='Original',document=self.data['document'],revision=3)
        self.data['sketch_id']=sketch.pk
        response=self.post()
        self.assertEqual(response.status_code,202)
        job=RenderJob.objects.get(pk=response.json()['id'])
        self.assertEqual(job.owner,self.user)
        self.assertEqual(job.sketch_revision,3)
        self.assertEqual(job.fingerprint,fingerprint(validate_document(self.data['document'],{})))
        self.assertEqual(self.post().status_code,202)
        self.assertEqual(self.post().status_code,429)
        self.assertEqual(RenderJob.objects.count(),2)
        sketch.document=doc(wall(x2=8));sketch.save()
        job.refresh_from_db();self.assertEqual(job.document['objects'][0]['x2'],4)

    def test_absent_worker_disabled_or_stale_heartbeat_does_not_accept_jobs(self):
        RenderWorker.objects.update(heartbeat=timezone.now()-timedelta(seconds=30))
        self.assertEqual(self.post().status_code,503)
        with override_settings(RENDER_ENABLED=False):
            self.assertEqual(self.post().status_code,503)
        self.assertFalse(RenderJob.objects.exists())

    def test_normal_users_cannot_list_or_download_another_users_images(self):
        job=RenderJob.objects.create(owner=self.other,title='Private',document=doc(wall()),scene=scene(),fingerprint='a'*64,status='ready')
        self.client.force_login(get_user_model().objects.create_user('seller_render'))
        self.assertEqual(self.client.get('/api/renders/').json()['jobs'],[])
        self.assertEqual(self.client.get(f'/api/renders/{job.pk}/image/').status_code,404)
        sketch=Sketch.objects.create(owner=self.other,name='Private',document=doc(wall()))
        self.data['sketch_id']=sketch.pk
        self.assertEqual(self.post().status_code,404)
        self.assertEqual(self.client.get(f'/api/renders/?sketch_id={sketch.pk}').status_code,404)
        self.client.logout();self.assertEqual(self.client.get('/api/renders/').status_code,403)

    def test_ready_image_is_private_and_missing_files_are_not_server_errors(self):
        job=RenderJob.objects.create(owner=self.user,title='Safe name',document=doc(wall()),scene=scene(),fingerprint='b'*64,status='ready')
        with tempfile.TemporaryDirectory() as root,override_settings(RENDER_ROOT=Path(root)):
            self.assertEqual(self.client.get(f'/api/renders/{job.pk}/image/').status_code,404)
            path=render_path(job);path.parent.mkdir();path.write_bytes(b'png-test')
            response=self.client.get(f'/api/renders/{job.pk}/image/?download=1')
            self.assertEqual(response.status_code,200)
            self.assertEqual(response['Content-Type'],'image/png')
            self.assertIn('no-store',response['Cache-Control'])
            self.assertIn('attachment',response['Content-Disposition'])
            # Consume the streaming response through Django's test-client wrapper.
            # Calling response.close() directly emits request_finished and closes
            # PostgreSQL inside TestCase's outer transaction (SQLite masks this).
            with patch.object(connection, 'close', side_effect=AssertionError(
                    'La descarga no debe cerrar la transacción de TestCase')) as close_connection:
                self.assertEqual(b''.join(response.streaming_content), b'png-test')
                close_connection.assert_not_called()
            self.assertTrue(RenderJob.objects.filter(pk=job.pk).exists())

    def test_scene_bounds_and_settings_are_validated(self):
        for mutation in [lambda s:s.update(boxes=[]),lambda s:s['boxes'][0].update(role='script'),
                         lambda s:s['boxes'][0].update(position=[1,float('inf'),0]),
                         lambda s:s['boxes'][0].update(size=[4,2.5,-1]),
                         lambda s:s.update(settings={'roof_type':'external'})]:
            bad=copy.deepcopy(scene());mutation(bad)
            with self.assertRaises(InvalidDocument):validate_scene(bad)
        self.data['scene']['settings']={'wall_color':'sand'}
        self.assertEqual(self.post().status_code,400)

    def test_only_one_worker_claims_a_job_and_bad_blender_execution_fails_cleanly(self):
        response=self.post();job=claim_job()
        self.assertEqual(str(job.pk),response.json()['id'])
        self.assertIsNone(claim_job())
        with tempfile.TemporaryDirectory() as root,override_settings(RENDER_ROOT=Path(root)),patch(
            'sketches.management.commands.render_worker.subprocess.Popen',side_effect=OSError('no binary')):
            run_job(job)
        job.refresh_from_db();self.assertEqual(job.status,'failed')
        self.assertNotIn('binary',job.error)

    def test_successful_process_produces_a_verified_png_and_ready_status(self):
        self.post();job=claim_job()
        def process(command, **kwargs):
            Image.new('RGB',(1280,960),'white').save(command[-1])
            return MagicMock(returncode=0, poll=lambda:0)
        with tempfile.TemporaryDirectory() as root,override_settings(RENDER_ROOT=Path(root)),patch(
            'sketches.management.commands.render_worker.subprocess.Popen',side_effect=process):
            run_job(job)
        job.refresh_from_db();self.assertEqual(job.status,'ready');self.assertIsNotNone(job.finished_at)

    def test_timeout_kills_the_process_and_reports_a_recoverable_failure(self):
        self.post();job=claim_job();process=MagicMock();process.poll.return_value=None
        with tempfile.TemporaryDirectory() as root,override_settings(RENDER_ROOT=Path(root),RENDER_TIMEOUT=1),patch(
            'sketches.management.commands.render_worker.subprocess.Popen',return_value=process),patch(
            'sketches.management.commands.render_worker.monotonic',side_effect=[0,2]):
            run_job(job)
        process.kill.assert_called_once();process.wait.assert_called_once()
        job.refresh_from_db();self.assertEqual(job.status,'failed');self.assertIn('tiempo',job.error)
