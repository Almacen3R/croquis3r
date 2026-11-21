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

    @override_settings(RENDER_TIMEOUT=60)
    def test_listing_expires_overdue_jobs_only_in_the_users_visible_scope(self):
        seller=get_user_model().objects.create_user('status_seller')
        old=timezone.now()-timedelta(seconds=125)
        own=RenderJob.objects.create(owner=seller,title='Old',document=doc(wall()),scene=scene(),fingerprint='a'*64,status='running',started_at=old)
        other=RenderJob.objects.create(owner=self.other,title='Private',document=doc(wall()),scene=scene(),fingerprint='b'*64,status='running',started_at=old)
        active=RenderJob.objects.create(owner=seller,title='Active',document=doc(wall()),scene=scene(),fingerprint='c'*64,status='running',started_at=timezone.now()-timedelta(seconds=5))
        self.client.force_login(seller)
        response=self.client.get('/api/renders/').json()
        self.assertEqual(response['timeout_seconds'],60)
        own.refresh_from_db();other.refresh_from_db();active.refresh_from_db()
        self.assertEqual(own.status,'failed')
        self.assertIn('interrumpió',own.error)
        self.assertEqual(other.status,'running')
        self.assertEqual(active.status,'running')
        self.assertTrue(all('elapsed_seconds' in job for job in response['jobs']))

    def test_missing_heartbeat_is_reported_without_prematurely_failing_active_work(self):
        job=RenderJob.objects.create(owner=self.user,title='Working',document=doc(wall()),scene=scene(),fingerprint='d'*64,status='running',started_at=timezone.now())
        RenderWorker.objects.update(heartbeat=timezone.now()-timedelta(seconds=30))
        response=self.client.get('/api/renders/').json()
        self.assertFalse(response['available'])
        job.refresh_from_db();self.assertEqual(job.status,'running')
        self.assertEqual(response['jobs'][0]['status'],'running')

    @override_settings(RENDER_TIMEOUT=60)
    def test_overdue_work_no_longer_blocks_the_owners_submission_quota(self):
        for i in range(2):
            RenderJob.objects.create(owner=self.user,title='Interrupted',document=doc(wall()),scene=scene(),fingerprint='e'*64,status='running',started_at=timezone.now()-timedelta(seconds=125))
        self.assertEqual(self.post().status_code,202)
        self.assertEqual(RenderJob.objects.filter(owner=self.user,status='failed').count(),2)

    def test_camera_details_and_visual_overhang_are_bounded(self):
        data = scene()
        data['details'] = [{'role':'metal','position':[1,1,0], 'size':[.1,.02,.04], 'rotation':0}]
        data['camera'] = {'position':[2,1.6,2], 'target':[2,1.6,0], 'fov':70}
        data['settings'] = {'roof_overhang':.25, 'ridge_axis':'z'}
        cleaned = validate_scene(data)
        self.assertEqual(cleaned['camera'], data['camera'])
        self.assertEqual(cleaned['details'], data['details'])
        self.assertEqual(cleaned['settings']['roof_overhang'], .25)
        for mutate in (lambda d:d['camera'].update(position=[float('inf'),0,0]),
                       lambda d:d['camera'].update(target=d['camera']['position']),
                       lambda d:d['camera'].update(fov=0),
                       lambda d:d['details'][0].update(role='script'),
                       lambda d:d['settings'].update(roof_overhang=.61)):
            invalid = copy.deepcopy(data)
            mutate(invalid)
            with self.assertRaises(InvalidDocument):
                validate_scene(invalid)

    def test_visual_settings_do_not_change_material_quantities(self):
        from .modulation import calculate_modulation
        original = doc(wall())
        styled = {**original, 'presentation3d': {'roof_type':'gable', 'roof_overhang':.4, 'ridge_axis':'z'}}
        self.assertEqual(calculate_modulation(original,{})['items'], calculate_modulation(styled,{})['items'])
        self.assertEqual(validate_document(styled,{})['presentation3d']['ridge_axis'], 'z')

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
