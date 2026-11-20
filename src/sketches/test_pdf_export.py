from io import BytesIO
import json
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from PIL import Image

from .models import Sketch


def png_file(size=(600,400), mode='RGB'):
    output=BytesIO()
    Image.new(mode,size,'white').save(output,format='PNG')
    return SimpleUploadedFile('croquis.png',output.getvalue(),'image/png')


@override_settings(DEBUG=False, THREER_PRICING_ENABLED=False,
                   SESSION_COOKIE_SECURE=False, CSRF_COOKIE_SECURE=False)
class PdfExportTests(TestCase):
    def setUp(self):
        self.user=get_user_model().objects.create_user('exportador_pdf')
        self.client.force_login(self.user)

    def test_materials_recalculates_and_never_looks_up_prices_for_unpriced_copy(self):
        from .test_modulation import doc, wall
        from .pdf_export import materials_pdf
        data={'name':'Casa <Pablo>', 'document':doc(wall()), 'with_prices':False,
              'rows':[{'name':'Inventado', 'quantity':999999}]}
        with patch('sketches.views.quote') as quote, patch('sketches.views.materials_pdf', wraps=materials_pdf) as render:
            response=self.client.post('/api/export-materials-pdf/',json.dumps(data),content_type='application/json')
            self.assertEqual(response.status_code,200)
            self.assertTrue(b''.join(response.streaming_content).startswith(b'%PDF-'))
            quote.assert_not_called()
            self.assertIsNone(render.call_args.kwargs['pricing'])
            self.assertFalse(any(row['name']=='Inventado' for row in render.call_args.args[1]))
        data['with_prices']=True
        response=self.client.post('/api/export-materials-pdf/',json.dumps(data),content_type='application/json')
        self.assertEqual(response.status_code,200)
        self.assertIn('con-precios.pdf',response['Content-Disposition'])
        self.assertTrue(b''.join(response.streaming_content).startswith(b'%PDF-'))
        self.assertEqual(Sketch.objects.count(),0)
        with patch('sketches.views.quote', return_value={'complete':False,'subtotal_with_prices':123,
                'rows':[{'name':'Precio del servidor','unit':'unidades','quantity':1,
                         'unit_price':123,'amount':123}]}) as quote:
            response=self.client.post('/api/export-materials-pdf/',json.dumps(data),content_type='application/json')
            self.assertEqual(response.status_code,200)
            self.assertTrue(b''.join(response.streaming_content).startswith(b'%PDF-'))
            quote.assert_called_once()

    def test_materials_pdf_includes_trusted_height_and_grouped_panel_calculation(self):
        from .test_modulation import doc, wall
        from .pdf_export import materials_pdf, panel_calculation_rows
        data = {'name': 'Tapia 13 m', 'document': doc(wall(x2=13, height=2.7), linear_columns=8, t_columns=0),
                'with_prices': False, 'height_label': 'Altura inventada'}
        for priced in (False, True):
            data['with_prices'] = priced
            with patch('sketches.views.materials_pdf', wraps=materials_pdf) as render:
                response = self.client.post('/api/export-materials-pdf/', json.dumps(data), content_type='application/json')
                self.assertEqual(response.status_code, 200)
                self.assertTrue(b''.join(response.streaming_content).startswith(b'%PDF-'))
                calculation = render.call_args.kwargs['calculation']
                self.assertEqual(calculation['height_label'], '2,70 m')
                self.assertEqual(calculation['panels'], 7)
                grouped = panel_calculation_rows(calculation)
                two = next(row for row in grouped if row['panels'] == 6)
                one = next(row for row in grouped if row['panels'] == 1)
                self.assertEqual((two['long_each'], two['short_each'], two['long_total'], two['short_total']), (36, 12, 216, 72))
                self.assertEqual((one['long_each'], one['short_each']), (12, 12))
                self.assertNotIn('warnings', render.call_args.kwargs)

    def test_pdf_explains_beams_and_excel_steel_rounding_at_both_heights(self):
        from .test_modulation import doc, wall
        from .modulation import calculate_modulation
        from .pdf_export import other_calculation_rows
        for height, beam, steel in ((2.7, 33, 2), (2.9, 66, 4)):
            calculation = calculate_modulation(doc(wall(x2=13, height=height), linear_columns=8, t_columns=0), {})
            explanations = dict(other_calculation_rows(calculation))
            self.assertIn('13 m / 0,40 m = 32,5 -> 33 piezas', explanations['Vigabloques'])
            self.assertIn(f'= {beam} unidades', explanations['Vigabloques'])
            self.assertIn('6 x 1,5 + 1 x 0,5 = 9,5 -> 10', explanations['Varilla 3/8 - pared'])
            self.assertIn(f'= {steel} equivalentes', explanations['Varilla 3/8 - viga'])
            self.assertIn('312 bloques / 20 = 15,6 -> 16', explanations['Mortero'])
        narrow = calculate_modulation(doc(wall(x2=13, thickness=.1)), {})
        self.assertEqual(other_calculation_rows(narrow), [])

    def test_long_beam_explanation_can_paginate_without_losing_the_pdf(self):
        from .test_modulation import doc, wall
        from .modulation import calculate_modulation
        from .pdf_export import materials_pdf
        drawing = doc(*(wall(str(i), x2=(i + 1) / 2, y1=i, y2=i) for i in range(100)))
        calculation = calculate_modulation(drawing, {})
        self.assertEqual(calculation['status'], 'ready')
        output = materials_pdf('Proyecto con muchos tramos', calculation['items'], calculation=calculation)
        self.assertTrue(output.getvalue().startswith(b'%PDF-'))

    def test_materials_rejects_invalid_document_and_requires_authentication(self):
        data={'name':'Casa','document':{'version':1,'objects':[]},'with_prices':'yes'}
        self.assertEqual(self.client.post('/api/export-materials-pdf/',json.dumps(data),content_type='application/json').status_code,400)
        protected=Client(enforce_csrf_checks=True)
        protected.force_login(self.user)
        self.assertEqual(protected.post('/api/export-materials-pdf/',json.dumps(data),content_type='application/json').status_code,403)
        data['with_prices']=False
        data['document']={'broken':True}
        self.assertEqual(self.client.post('/api/export-materials-pdf/',json.dumps(data),content_type='application/json').status_code,400)
        self.client.logout()
        self.assertEqual(self.client.post('/api/export-materials-pdf/',json.dumps(data),content_type='application/json').status_code,403)

    def test_pdf_download_is_a_binary_attachment_without_saving_projects(self):
        for size in ((600,400),(400,600)):
            response=self.client.post('/api/export-pdf/',{'name':'Casa de José','image':png_file(size,mode='RGBA')})
            self.assertEqual(response.status_code,200)
            self.assertEqual(response['Content-Type'],'application/pdf')
            self.assertIn('attachment;',response['Content-Disposition'])
            self.assertIn('casa-de-jose.pdf',response['Content-Disposition'])
            self.assertIn('no-store',response['Cache-Control'])
            content=b''.join(response.streaming_content)
            self.assertTrue(content.startswith(b'%PDF-'))
            self.assertTrue(content.rstrip().endswith(b'%%EOF'))
            self.assertGreater(len(content),1000)
        self.assertEqual(Sketch.objects.count(),0)

    def test_rejects_missing_corrupt_oversized_or_non_png_images(self):
        for data in ({'name':'Casa'}, {'name':'','image':png_file()},
                     {'name':'Casa','image':SimpleUploadedFile('x.svg',b'<svg/>')},
                     {'name':'Casa','image':SimpleUploadedFile('x.png',b'not a png')},
                     {'name':'Casa','image':png_file((2401,1))},
                     {'name':'Casa','image':SimpleUploadedFile('x.png',b'x'*(8*1024*1024+1))}):
            with self.subTest(keys=list(data)):
                response=self.client.post('/api/export-pdf/',data)
                self.assertEqual(response.status_code,400)
                self.assertIn('error',response.json())
        self.assertEqual(Sketch.objects.count(),0)

    def test_pdf_requires_session_and_csrf_and_editor_offers_both_formats(self):
        self.client.logout()
        self.assertEqual(self.client.post('/api/export-pdf/',{'name':'Casa','image':png_file()}).status_code,403)
        protected=Client(enforce_csrf_checks=True)
        protected.force_login(self.user)
        self.assertEqual(protected.post('/api/export-pdf/',{'name':'Casa','image':png_file()}).status_code,403)
        editor=protected.get('/')
        self.assertContains(editor,'disabled>Descargar</button>')
        self.assertContains(editor,'id="download-dialog"')
        self.assertContains(editor,'value="pdf"')
        self.assertContains(editor,'value="png"')
        token=protected.cookies[settings.CSRF_COOKIE_NAME].value
        response=protected.post('/api/export-pdf/',{'name':'Casa','image':png_file()},HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code,200)
        self.assertTrue(b''.join(response.streaming_content).startswith(b'%PDF-'))
