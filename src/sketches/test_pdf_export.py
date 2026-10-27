from io import BytesIO

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
