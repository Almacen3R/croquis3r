from .testing import AuthenticatedTestCase as TestCase
from django.test import override_settings

from .house_templates import TEMPLATES
from .models import Attention
from .test_house_calculator import entries
from .test_house_templates import original_data


@override_settings(DEBUG=True)
class AttentionTests(TestCase):
    def save_manual(self, **changes):
        return self.client.post('/calculador-casas/', entries(panel_4='1', customer='Cliente de prueba',
                                notes='Revisar ventanas', action='save', **changes))

    def test_save_recover_and_snapshot_do_not_recalculate(self):
        response = self.save_manual()
        record = Attention.objects.get()
        self.assertRedirects(response, f'/atenciones/{record.pk}/')
        self.assertEqual((record.customer, record.result['tp50']), ('Cliente de prueba', 36))
        self.assertEqual(record.inputs['panel_4'], 1)
        opened = self.client.get(f'/calculador-casas/?attention={record.pk}')
        self.assertEqual(opened.context['form']['panel_4'].value(), 1)
        self.assertEqual(opened.context['form']['record_revision'].value(), 1)
        record.result['items'][0][1] = 999  # La vista histórica conserva el resultado almacenado.
        record.save()
        self.assertContains(self.client.get(f'/atenciones/{record.pk}/'), '999')

    def test_update_conflict_and_copy_preserve_newer_data(self):
        self.save_manual()
        record = Attention.objects.get()
        data = entries(panel_4='2', customer='Cliente de prueba', action='save', record_id=record.pk, record_revision=1)
        self.assertEqual(self.client.post('/calculador-casas/', data).status_code, 302)
        record.refresh_from_db()
        self.assertEqual((record.revision, record.result['tp50']), (2, 72))
        conflict = self.client.post('/calculador-casas/', {**data, 'panel_4': '3'})
        self.assertContains(conflict, 'Otra sesión actualizó', status_code=400)
        record.refresh_from_db()
        self.assertEqual(record.result['tp50'], 72)
        copied = self.client.post('/calculador-casas/', {**data, 'action': 'save_copy', 'panel_4': '3'})
        self.assertEqual(copied.status_code, 302)
        self.assertEqual(Attention.objects.count(), 2)
        self.assertEqual(Attention.objects.exclude(pk=record.pk).get().result['tp50'], 108)

    def test_template_save_reopen_preserves_unknown_quantities_and_original(self):
        data = {**original_data(TEMPLATES[0]), 'action': 'save', 'tp48': '320', 'customer': 'Cliente plantilla'}
        response = self.client.post('/calculador-casas/plantillas/modelo-e/', data)
        self.assertEqual(response.status_code, 302)
        record = Attention.objects.get()
        self.assertEqual(record.result['blocks'], 502)
        self.assertEqual(record.result['unknown'], 2)
        detail = self.client.get(f'/atenciones/{record.pk}/')
        self.assertContains(detail, 'Pendiente')
        self.assertContains(detail, 'original: 316')
        loaded = self.client.get(f'/calculador-casas/plantillas/modelo-e/?attention={record.pk}')
        self.assertEqual(loaded.context['form']['tp48'].value(), 320)
        self.assertEqual(loaded.context['result']['unknown'], 2)
        self.assertEqual(TEMPLATES[0].materials[2].quantity, 316)

    def test_invalid_input_and_cross_kind_update_never_overwrite(self):
        self.save_manual()
        record = Attention.objects.get()
        url = '/calculador-casas/plantillas/modelo-e/'
        data = {**original_data(TEMPLATES[0]), 'action': 'save', 'record_id': record.pk, 'record_revision': 1}
        self.assertEqual(self.client.post(url, data).status_code, 400)
        self.assertEqual(self.client.get(f'{url}?attention={record.pk}').status_code, 404)
        self.assertEqual(self.client.post('/calculador-casas/', entries(panel_4='-1', action='save')).status_code, 400)
        self.assertEqual(Attention.objects.count(), 1)
        record.refresh_from_db()
        self.assertEqual(record.kind, 'manual')

    def test_search_and_escape_customer_notes(self):
        data = entries(panel_4='1', action='save', customer='<script>cliente</script>', notes='<img src=x>')
        self.client.post('/calculador-casas/', data)
        page = self.client.get('/atenciones/?q=cliente')
        self.assertContains(page, '&lt;script&gt;cliente&lt;/script&gt;')
        self.assertContains(self.client.get('/atenciones/?q=sin-coincidencias'), 'No hay coincidencias')
        detail = self.client.get(f'/atenciones/{Attention.objects.get().pk}/')
        self.assertContains(detail, '&lt;img src=x&gt;')
        self.assertNotContains(detail, '<img src=x>')

    def test_calculation_and_preview_do_not_save_implicitly(self):
        self.client.post('/calculador-casas/', entries(panel_4='1'))
        self.client.get('/calculador-casas/plantillas/modelo-e/')
        self.assertEqual(Attention.objects.count(), 0)

    def test_empty_house_cannot_be_saved_as_a_completed_attention(self):
        response = self.client.post('/calculador-casas/', entries(action='save'))
        self.assertContains(response, 'Agrega al menos un paño', status_code=400)
        self.assertEqual(Attention.objects.count(), 0)

    def test_browser_result_cannot_override_server_snapshot(self):
        self.save_manual(result='{"tp50":999999}')
        self.assertEqual(Attention.objects.get().result['tp50'], 36)

    @override_settings(DEBUG=False)
    def test_production_access_restricted(self):
        self.client.logout()
        self.assertEqual(self.client.get('/atenciones/').status_code, 302)
        self.assertEqual(self.client.get('/atenciones/1/').status_code, 302)

    def test_bad_identifiers_do_not_crash(self):
        for raw in ('abc', '9' * 100, '-1'):
            self.assertEqual(self.client.get(f'/calculador-casas/?attention={raw}').status_code, 404)
