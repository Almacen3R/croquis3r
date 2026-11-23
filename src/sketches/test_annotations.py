import json
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from .domain import InvalidDocument, validate_document
from .modulation import calculate_modulation
from .models import Sketch
from .testing import AuthenticatedTestCase
from .test_modulation import doc, wall

NOTES=[{'id':'note','kind':'text','text':'Confirmar acceso\nNo incluye pintura <pendiente>',
        'x':-1.,'y':-1.,'color':'blue','font_size':.25},
       {'id':'arrow','kind':'arrow','text':'Entrada','x1':-1.,'y1':0.,'x2':0.,'y2':0.,'color':'black','font_size':.3}]

class AnnotationValidationTests(SimpleTestCase):
    def test_annotations_are_preserved_without_changing_materials(self):
        original=doc(wall());annotated={**original,'annotations':NOTES}
        self.assertEqual(validate_document(annotated,{})['annotations'],NOTES)
        self.assertEqual(calculate_modulation(original,{})['items'],calculate_modulation(annotated,{})['items'])
        self.assertNotIn('annotations',validate_document(original,{}))

    def test_text_rotation_accepts_quarter_turns_only_and_keeps_materials(self):
        original=doc(wall())
        for angle in (0,90,180,270):
            annotation={**NOTES[0], 'text_rotation':angle}
            drawing={**original,'annotations':[annotation]}
            self.assertEqual(validate_document(drawing,{})['annotations'][0]['text_rotation'],angle)
            self.assertEqual(calculate_modulation(drawing,{})['items'],calculate_modulation(original,{})['items'])
        for value in (True,45,360,-90,90.0,'90',None):
            with self.subTest(value=value),self.assertRaises(InvalidDocument):
                validate_document({**original,'annotations':[{**NOTES[0],'text_rotation':value}]},{})

    def test_limits_kinds_ids_and_coordinates_are_validated(self):
        for value in (None,{},[NOTES[0]]*101,[{**NOTES[0],'kind':'script'}],
                      [{**NOTES[0],'id':'w'}],[NOTES[0],NOTES[0]],
                      [{**NOTES[0],'text':' '}],[{**NOTES[0],'text':'a'*301}],
                      [{**NOTES[0],'color':'url(x)'}],[{**NOTES[0],'font_size':10}],
                      [{**NOTES[0],'x':float('nan')}],[{**NOTES[0],'x':101}],
                      [{**NOTES[1],'x2':-1,'y2':0}]):
            with self.subTest(value=value),self.assertRaises(InvalidDocument):
                validate_document({**doc(wall()),'annotations':value},{})

class AnnotationPersistenceTests(AuthenticatedTestCase):
    def test_save_template_and_import_preserve_notes(self):
        rotated=[{**note,'text_rotation':270} for note in NOTES]
        drawing={**doc(wall()),'annotations':rotated}
        response=self.client.post('/api/sketches/',json.dumps({'name':'Con notas','document':drawing,'is_template':True}),content_type='application/json')
        self.assertEqual(response.status_code,201)
        pk=response.json()['id']
        self.assertEqual(self.client.get(f'/api/sketches/{pk}/').json()['document']['annotations'],rotated)
        archive={'format':'croquis3r-project','format_version':1,'name':'Notas importadas','units':'m','document':drawing,'articles':[]}
        imported=self.client.post('/proyectos/importar/',{'project_file':SimpleUploadedFile('notas.json',json.dumps(archive).encode(),'application/json')})
        self.assertEqual(imported.status_code,302)
        self.assertEqual(Sketch.objects.get(name='Notas importadas').document['annotations'],rotated)
