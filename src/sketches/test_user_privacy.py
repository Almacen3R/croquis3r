import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client, TestCase, override_settings

from .models import Attention, ObjectTemplate, Sketch
from .test_house_calculator import entries
from .test_house_templates import original_data
from .house_templates import TEMPLATES
from .tests import document, wall


@override_settings(THREER_PRICING_ENABLED=False, DEBUG=False, SESSION_COOKIE_SECURE=False, CSRF_COOKIE_SECURE=False)
class UserPrivacyTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.a = users.objects.create_user('vendedor_a')
        self.b = users.objects.create_user('vendedor_b', is_staff=True)
        self.admin = users.objects.create_superuser('administrador', '', None)
        self.client.force_login(self.a)
        self.own = Sketch.objects.create(name='Privado A', owner=self.a, document=document(wall()))
        self.other = Sketch.objects.create(name='Privado B', owner=self.b, document=document(wall()), is_template=True)
        self.legacy = Sketch.objects.create(name='Anterior sin dueño', document=document(wall()))
        for owner in (self.a, self.b, None):
            ObjectTemplate.objects.create(name=f'Pared {owner}', owner=owner, specification=wall())
        self.record = Attention.objects.create(owner=self.b, kind='manual', project='Cliente privado B', inputs=entries(panel_4='1'), result={'items': []})
        self.personal_template = Attention.objects.create(owner=self.b, kind='template', template_slug='modelo-e', project='Promo privada B', inputs=original_data(TEMPLATES[0]), result={'rows': []})

    def post_json(self, url, data):
        return self.client.post(url, json.dumps(data), content_type='application/json')

    def test_lists_and_home_are_scoped_even_for_staff(self):
        self.assertEqual([row['id'] for row in self.client.get('/api/sketches/').json()['sketches']], [self.own.pk])
        self.assertEqual(len(self.client.get('/api/object-templates/').json()['templates']), 1)
        home = self.client.get('/atenciones/?q=Cliente')
        self.assertNotContains(home, 'Cliente privado B')
        self.assertNotContains(home, 'Promo privada B')
        self.assertNotContains(home, 'Privado B')
        self.client.force_login(self.b)
        self.assertEqual([row['id'] for row in self.client.get('/api/sketches/').json()['sketches']], [self.other.pk])
        self.assertContains(self.client.get('/atenciones/'), 'Cliente privado B')

    def test_guessed_urls_and_update_cannot_access_other_or_ownerless_sketch(self):
        for record in (self.other, self.legacy):
            url = f'/api/sketches/{record.pk}/'
            self.assertEqual(self.client.get(url).status_code, 404)
            response = self.client.put(url, json.dumps({'name':'Ataque','document':document(wall()),'revision':1}), content_type='application/json')
            self.assertEqual(response.status_code, 404)
            record.refresh_from_db()
            self.assertEqual(record.revision, 1)

    def test_owner_is_taken_from_session_and_cannot_be_forged_on_create_update_or_copy(self):
        data = {'name':'Mía','document':document(wall()),'owner':self.b.pk,'is_template':True}
        response = self.post_json('/api/sketches/', data)
        record = Sketch.objects.get(pk=response.json()['id'])
        self.assertEqual(record.owner, self.a)
        url = f'/api/sketches/{record.pk}/'
        self.assertEqual(self.client.put(url, json.dumps({**data,'revision':1}), content_type='application/json').status_code,200)
        record.refresh_from_db(); self.assertEqual(record.owner,self.a)
        response = self.post_json('/api/object-templates/', {'name':'Mía','owner':self.b.pk,'specification':wall()})
        self.assertEqual(ObjectTemplate.objects.get(pk=response.json()['id']).owner,self.a)

    def test_attention_detail_reopen_and_forged_copy_are_all_blocked(self):
        for record, url, data in [(self.record,'/calculador-casas/',entries(panel_4='1')),
                                  (self.personal_template,'/calculador-casas/plantillas/modelo-e/',original_data(TEMPLATES[0]))]:
            self.assertEqual(self.client.get(f'/atenciones/{record.pk}/').status_code,404)
            self.assertEqual(self.client.get(f'{url}?attention={record.pk}').status_code,404)
            for action in ('save','save_copy'):
                response=self.client.post(url,{**data,'action':action,'record_id':record.pk,'record_revision':1})
                self.assertEqual(response.status_code,400)
            record.refresh_from_db();self.assertEqual(record.revision,1)
        self.assertEqual(Attention.objects.count(),2)

    def test_new_manual_and_template_attentions_belong_to_creator(self):
        for url, data in [('/calculador-casas/',entries(panel_4='1')),
                          ('/calculador-casas/plantillas/modelo-e/',original_data(TEMPLATES[0]))]:
            response=self.client.post(url,{**data,'action':'save','owner':self.b.pk})
            self.assertEqual(response.status_code,302)
        self.assertEqual(Attention.objects.filter(owner=self.a).count(),2)
        self.assertContains(self.client.get('/calculador-casas/plantillas/'),'Modelo E')

    def test_administrator_sees_all_and_update_preserves_original_owner(self):
        self.client.force_login(self.admin)
        self.assertEqual(len(self.client.get('/api/sketches/').json()['sketches']),3)
        self.assertEqual(len(self.client.get('/api/object-templates/').json()['templates']),3)
        self.assertContains(self.client.get('/atenciones/'),'Cliente privado B')
        self.assertEqual(self.client.get(f'/api/sketches/{self.legacy.pk}/').status_code,200)
        response=self.client.put(f'/api/sketches/{self.other.pk}/',json.dumps({'name':'Revisado','revision':1,'document':document(wall())}),content_type='application/json')
        self.assertEqual(response.status_code,200)
        self.other.refresh_from_db();self.assertEqual(self.other.owner,self.b)
        response=self.client.post('/calculador-casas/',entries(panel_4='2',action='save',record_id=self.record.pk,record_revision=1))
        self.assertEqual(response.status_code,302)
        self.record.refresh_from_db();self.assertEqual(self.record.owner,self.b)

    def test_staff_permissions_do_not_grant_global_record_access_in_admin(self):
        self.b.user_permissions.add(*Permission.objects.filter(content_type__app_label='sketches'))
        self.client.force_login(self.b)
        for path in ('sketch','objecttemplate','attention'):
            self.assertEqual(self.client.get(f'/admin/sketches/{path}/').status_code,403)
        self.client.force_login(self.admin)
        self.assertContains(self.client.get('/admin/sketches/sketch/'),'Anterior sin dueño')

    def test_login_logout_csrf_and_anonymous_access_also_in_debug(self):
        for debug in (True,False):
            with self.settings(DEBUG=debug):
                anonymous=Client()
                self.assertEqual(anonymous.get('/').status_code,302)
                self.assertEqual(anonymous.get('/api/sketches/').status_code,403)
        csrf_client=Client(enforce_csrf_checks=True);csrf_client.force_login(self.a)
        self.assertEqual(csrf_client.get('/salir/').status_code,405)
        self.assertEqual(csrf_client.post('/salir/').status_code,403)
        response=csrf_client.get('/')
        self.assertIn('no-store',response['Cache-Control'])
        self.assertContains(response,'Cerrar sesión')
        token=csrf_client.cookies['csrftoken'].value
        self.assertEqual(csrf_client.post('/salir/',HTTP_X_CSRFTOKEN=token).status_code,302)
        self.assertEqual(csrf_client.get('/api/sketches/').status_code,403)
        self.assertRedirects(csrf_client.get('/'),'/ingresar/?next=/',fetch_redirect_response=False)

    def test_normal_account_can_login_and_inactive_account_cannot(self):
        self.a.set_password('Password-Test-Only-4109');self.a.save()
        c=Client();response=c.post('/ingresar/',{'username':self.a.username,'password':'Password-Test-Only-4109','next':'https://example.invalid/'})
        self.assertRedirects(response,'/atenciones/',fetch_redirect_response=False)
        self.assertEqual(c.get('/').status_code,200)
        c.logout();self.a.is_active=False;self.a.save()
        response=c.post('/ingresar/',{'username':self.a.username,'password':'Password-Test-Only-4109'})
        self.assertContains(response,'Iniciar sesión')
        self.assertEqual(c.get('/api/sketches/').status_code,403)
