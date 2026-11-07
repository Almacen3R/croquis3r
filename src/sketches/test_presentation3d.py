import json

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

from .domain import InvalidDocument, validate_document
from .models import Sketch
from .modulation import calculate_modulation
from .test_modulation import doc, wall
from .testing import AuthenticatedTestCase


OPTIONS = {'wall_color': 'sage', 'floor_finish': 'wood', 'roof_type': 'gable',
           'roof_color': 'terracotta', 'roof_rise': 1.2, 'ridge_axis': 'z'}


class PresentationValidationTests(SimpleTestCase):
    def test_visual_settings_do_not_change_quantities_and_legacy_documents_stay_compatible(self):
        original = doc(wall())
        presented = {**original, 'presentation3d': OPTIONS}
        self.assertEqual(validate_document(presented, {})['presentation3d'], OPTIONS)
        self.assertNotIn('presentation3d', validate_document(original, {}))
        self.assertEqual(calculate_modulation(original, {})['items'],
                         calculate_modulation(presented, {})['items'])

    def test_rejects_unbounded_and_unknown_visual_options(self):
        for options in (None, [], False, {'wall_color': '#fff'}, {'floor_finish': '<script>'},
                        {'roof_type': 'custom'}, {'ridge_axis': 'y'}, {'roof_color': []},
                        {'roof_rise': True}, {'roof_rise': -1}, {'roof_rise': 50},
                        {'roof_rise': 'NaN'}, {'roof_rise': 'Infinity'}, {'external_url': 'https://example.invalid'}):
            with self.subTest(options=options), self.assertRaises(InvalidDocument):
                validate_document({**doc(wall()), 'presentation3d': options}, {})


class PresentationPersistenceTests(AuthenticatedTestCase):
    def test_save_reopen_template_and_portable_import_preserve_finishes(self):
        drawing = {**doc(wall()), 'presentation3d': OPTIONS}
        created = self.client.post('/api/sketches/', json.dumps({
            'name': 'Casa con acabados', 'document': drawing, 'is_template': True}),
            content_type='application/json')
        self.assertEqual(created.status_code, 201)
        pk = created.json()['id']
        self.assertEqual(self.client.get(f'/api/sketches/{pk}/').json()['document']['presentation3d'], OPTIONS)
        self.assertTrue(Sketch.objects.get(pk=pk).is_template)
        archive = {'format': 'croquis3r-project', 'format_version': 1, 'units': 'm',
                   'name': 'Acabados importados', 'document': drawing, 'articles': []}
        response = self.client.post('/proyectos/importar/', {'project_file': SimpleUploadedFile(
            'acabados.json', json.dumps(archive).encode(), 'application/json')})
        self.assertEqual(response.status_code, 302)
        imported = Sketch.objects.get(name='Acabados importados')
        self.assertEqual(imported.document['presentation3d'], OPTIONS)
        self.assertEqual(imported.owner, self.user)
        drawing['presentation3d'] = {**OPTIONS, 'roof_type': 'flat'}
        updated = self.client.put(f'/api/sketches/{pk}/', json.dumps({
            'name': 'Casa con acabados', 'document': drawing, 'revision': 1}), content_type='application/json')
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(self.client.get(f'/api/sketches/{pk}/').json()['document']['presentation3d']['roof_type'], 'flat')
