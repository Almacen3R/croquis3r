import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings

from catalog.models import Article
from .models import Attention, Sketch
from .tests import document, wall, door


@override_settings(DEBUG=False, THREER_PRICING_ENABLED=False,
                   SESSION_COOKIE_SECURE=False, CSRF_COOKIE_SECURE=False)
class ProjectFileTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('vendedor_archivos')
        self.other = get_user_model().objects.create_user('otro_vendedor')
        self.client.force_login(self.user)

    def file(self, **changes):
        data = {'format':'croquis3r-project','format_version':1,'name':'Casa portátil',
            'document':document(wall(height=2.5,thickness=.12),door(width=1,door_rotation=3)),
            'articles':[], **changes}
        return SimpleUploadedFile('casa.croquis3r.json', json.dumps(data).encode(), 'application/json')

    def test_import_roundtrip_preserves_geometry_and_creates_independent_owned_copy(self):
        original = Sketch.objects.create(owner=self.other, name='Ajeno',document=document(wall()))
        doc = document(wall(height=2.5,thickness=.12),door(width=1,door_rotation=3))
        doc['columns']=[{'id':'col','kind':'column','label':'Lineal','x':0,'y':0,'column_type':'C'}]
        doc['ticoblock']={'max_span':'1.5','floor_level':1,'block_family':'12',
                         'linear_columns':0,'t_columns':0}
        response=self.client.post('/proyectos/importar/', {'project_file':self.file(document=doc,
            owner=self.other.pk,id=original.pk,revision=999,is_template=True)})
        imported=Sketch.objects.exclude(pk=original.pk).get()
        self.assertRedirects(response,f'/?sketch={imported.pk}&imported=1',fetch_redirect_response=False)
        self.assertEqual(imported.owner,self.user)
        self.assertEqual(imported.document,doc)
        self.assertEqual(imported.revision,1)
        self.assertFalse(imported.is_template)
        original.refresh_from_db()
        self.assertEqual(original.name,'Ajeno')
        self.assertEqual(original.revision,1)
        self.assertContains(self.client.get('/atenciones/'),'Casa portátil')

    def test_article_ids_are_remapped_by_sku_not_foreign_database_id(self):
        article=Article.objects.create(sku='PORTABLE-BLOCK',name='Block')
        doc=document(wall(assignments=[{'article_id':987654,'basis':'length','factor':'2','waste_percent':'0'}]))
        response=self.client.post('/proyectos/importar/',{'project_file':self.file(document=doc,
            articles=[{'id':987654,'sku':article.sku}])})
        self.assertEqual(response.status_code,302)
        self.assertEqual(Sketch.objects.get().document['objects'][0]['assignments'][0]['article_id'],article.pk)

    def test_bad_files_never_leave_a_partial_project(self):
        cases=[{}, {'project_file':SimpleUploadedFile('x.svg',b'<svg onload="alert(1)"/>')},
            {'project_file':SimpleUploadedFile('x.json',b'{' + b' '*1_048_576)},
            {'project_file':self.file(format_version=2)}, {'project_file':self.file(format_version=True)}, {'project_file':self.file(units='cm')},
            {'project_file':self.file(name='')}, {'project_file':self.file(document=document(wall(x2=0)))},
            {'project_file':self.file(articles=[{'id':1,'sku':'INEXISTENTE'}])},
            {'project_file':self.file(document=document(wall(assignments=[{'article_id':1}])))},
            {'project_file':SimpleUploadedFile('nan.json',b'{"x":NaN}')}]
        for data in cases:
            with self.subTest(data=list(data)):
                response=self.client.post('/proyectos/importar/',data)
                self.assertEqual(response.status_code,400)
                self.assertContains(response,'role="alert"',status_code=400)
                self.assertEqual(Sketch.objects.count(),0)

    def test_import_requires_session_and_csrf(self):
        self.client.logout()
        self.assertEqual(self.client.post('/proyectos/importar/',{'project_file':self.file()}).status_code,302)
        csrf=Client(enforce_csrf_checks=True)
        csrf.force_login(self.user)
        self.assertEqual(csrf.post('/proyectos/importar/',{'project_file':self.file()}).status_code,403)
        csrf.get('/atenciones/')
        token=csrf.cookies[settings.CSRF_COOKIE_NAME].value
        self.assertEqual(csrf.post('/proyectos/importar/',{'project_file':self.file(),'csrfmiddlewaretoken':token}).status_code,302)
        self.assertEqual(Sketch.objects.count(),1)

    def test_one_search_and_paginated_list_cover_all_types_with_privacy(self):
        Sketch.objects.create(owner=self.user,name='Cliente búsqueda croquis',document={})
        Sketch.objects.create(owner=self.user,name='Cliente búsqueda plantilla',document={},is_template=True)
        Sketch.objects.create(owner=self.other,name='Cliente búsqueda ajeno',document={})
        Attention.objects.create(owner=self.user,kind='manual',project='Cálculo',customer='Cliente búsqueda',result={})
        response=self.client.get('/atenciones/?q=búsqueda')
        self.assertContains(response,'Cliente búsqueda croquis')
        self.assertContains(response,'Cliente búsqueda plantilla')
        self.assertContains(response,'Cálculo')
        self.assertNotContains(response,'Cliente búsqueda ajeno')
        self.assertEqual(response.context['projects'].paginator.count,3)
        self.assertLess(response.content.index(b'Proyectos guardados'),response.content.index(b'Empezar otro proyecto'))
        for i in range(27):
            Sketch.objects.create(owner=self.user,name=f'Listado {i}',document={})
        page=self.client.get('/atenciones/?page=2').context['projects']
        self.assertEqual(page.paginator.count,30)
        self.assertEqual(len(page),5)
