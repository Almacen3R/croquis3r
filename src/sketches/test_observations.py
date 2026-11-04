import json
from django.core.files.uploadedfile import SimpleUploadedFile
from .testing import AuthenticatedTestCase
from .domain import InvalidDocument, validate_document
from .test_modulation import doc, wall
from .modulation import calculate_modulation
from .models import Sketch


class ObservationsTests(AuthenticatedTestCase):
    def test_notes_survive_save_edit_template_and_portable_import_without_changing_quantities(self):
        drawing=doc(wall())
        baseline=calculate_modulation(drawing,{})['items']
        notes='Confirmar ventanas con José.\nNo incluye pintura. <Pendiente> & revisión.'
        drawing['observations']=notes
        response=self.client.post('/api/sketches/',json.dumps({'name':'Prueba notas','document':drawing,'is_template':True}),content_type='application/json')
        self.assertEqual(response.status_code,201)
        pk=response.json()['id']
        self.assertEqual(self.client.get(f'/api/sketches/{pk}/').json()['document']['observations'],notes)
        self.assertTrue(Sketch.objects.get(pk=pk).is_template)
        drawing['observations']+='\nEntrega por confirmar.'
        response=self.client.put(f'/api/sketches/{pk}/',json.dumps({'name':'Prueba notas','document':drawing,'revision':1}),content_type='application/json')
        self.assertEqual(response.status_code,200)
        archive={'format':'croquis3r-project','format_version':1,'units':'m','name':'Notas importadas','document':drawing,'articles':[]}
        response=self.client.post('/proyectos/importar/',{'project_file':SimpleUploadedFile('notas.json',json.dumps(archive).encode(),'application/json')})
        self.assertEqual(response.status_code,302)
        self.assertEqual(Sketch.objects.get(name='Notas importadas').document['observations'],drawing['observations'])
        self.assertEqual(calculate_modulation(drawing,{})['items'],baseline)

    def test_old_projects_work_and_invalid_notes_are_rejected(self):
        self.assertNotIn('observations',validate_document(doc(wall()),{}))
        for value in (None,False,{},'a'*1001,'\n'*20,'texto\x00oculto'):
            with self.subTest(value=repr(value)[:25]), self.assertRaises(InvalidDocument):
                validate_document({**doc(wall()),'observations':value},{})
