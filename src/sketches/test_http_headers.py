import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, SimpleTestCase, TestCase, override_settings

from .models import Sketch
from .tests import document, wall


@override_settings(LAN_HTTP_MODE=True, ALLOWED_HOSTS=['192.168.0.214', 'localhost', '.localhost',
                  '127.0.0.1', '[::1]', 'croquis.example.invalid'])
class HttpHeaderTests(SimpleTestCase):
    def test_lan_http_omits_only_the_ignored_header(self):
        response = self.client.get('/ingresar/', HTTP_HOST='192.168.0.214:8013')
        self.assertNotIn('Cross-Origin-Opener-Policy', response)
        self.assertEqual(response['X-Frame-Options'], 'DENY')
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response['Referrer-Policy'], 'same-origin')

    def test_https_keeps_coop_even_in_lan_mode(self):
        response = self.client.get('/ingresar/', secure=True, HTTP_HOST='croquis.example.invalid')
        self.assertEqual(response['Cross-Origin-Opener-Policy'], 'same-origin')

    def test_trustworthy_loopback_http_keeps_coop(self):
        for host in ('localhost:8013', 'test.localhost', '127.0.0.1:8013', '[::1]:8013'):
            with self.subTest(host=host):
                self.assertEqual(self.client.get('/ingresar/', HTTP_HOST=host)['Cross-Origin-Opener-Policy'], 'same-origin')

    @override_settings(LAN_HTTP_MODE=False)
    def test_default_mode_keeps_django_policy(self):
        self.assertEqual(self.client.get('/ingresar/', HTTP_HOST='192.168.0.214:8013')['Cross-Origin-Opener-Policy'], 'same-origin')


@override_settings(LAN_HTTP_MODE=True, DEBUG=False, SESSION_COOKIE_SECURE=False,
                  CSRF_COOKIE_SECURE=False, THREER_PRICING_ENABLED=False,
                  ALLOWED_HOSTS=['192.168.0.214'])
class HttpSaveTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('prueba_guardado')
        self.client = Client(enforce_csrf_checks=True, HTTP_HOST='192.168.0.214:8013')
        self.client.force_login(self.user)

    def test_lan_save_reopen_update_and_attention_link_with_other_apps_cookies(self):
        self.client.cookies['sessionid'] = 'sesion-de-otra-aplicacion'
        self.client.cookies['csrftoken'] = 'token-de-otra-aplicacion'
        page = self.client.get('/')
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'name="csrf-cookie-name" content="croquis3r_csrftoken"')
        token = self.client.cookies[settings.CSRF_COOKIE_NAME].value
        body = {'name': 'Croquis guardado por HTTP', 'document': document(wall(height=2.5, thickness=.12))}
        kwargs = {'content_type': 'application/json', 'HTTP_X_CSRFTOKEN': token}
        created = self.client.post('/api/sketches/', json.dumps(body), **kwargs)
        self.assertEqual(created.status_code, 201)
        pk = created.json()['id']
        self.assertNotIn('Cross-Origin-Opener-Policy', created)
        self.assertEqual(self.client.get(f'/api/sketches/{pk}/').json()['document'], body['document'])
        self.assertContains(self.client.get('/atenciones/'), f'?sketch={pk}')
        updated = self.client.put(f'/api/sketches/{pk}/', json.dumps({**body, 'revision': 1}), **kwargs)
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()['revision'], 2)
        self.assertEqual(Sketch.objects.count(), 1)

    def test_coop_adjustment_does_not_allow_csrf_or_anonymous_writes(self):
        body = json.dumps({'name': 'No guardar', 'document': document(wall())})
        self.assertEqual(self.client.post('/api/sketches/', body, content_type='application/json').status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get('/api/sketches/').status_code, 403)
        self.assertEqual(Sketch.objects.count(), 0)
