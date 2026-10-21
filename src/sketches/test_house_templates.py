from django.test import Client, SimpleTestCase, TestCase, override_settings

from .house_templates import HouseTemplateForm, TEMPLATES, TEMPLATES_BY_SLUG, template_result


def original_data(house):
    return {"project": "Mi casa", **{item.key: "" if item.quantity is None else str(item.quantity)
                                    for item in house.materials}}


class TemplateDataTests(SimpleTestCase):
    def test_seven_source_tables_preserve_material_quantities(self):
        # Transcripción independiente de las siete tablas, en orden del documento.
        expected = (
            ("modelo-e", "24,75", [12, 7, 316, 182, 1, 2, 1, None, None]),
            ("modelo-d", "39", [18, 9, 432, 282, 1, 3, 1]),
            ("promo-a", "45,5", [20, 9, 516, 306, 1, 3, 1]),
            ("modelo-estandar", "48,75", [20, 10, 482, 307, 1, 1, 3]),
            ("modelo-j", "48", [23, 10, 508, 344, 1, None, 4]),
            ("modelo-g", "54", [23, 11, 580, 362, 1, 4, 1]),
            ("modelo-63", "63", [28, 12, 620, 402, 2, 4, 1]),
        )
        self.assertEqual(len(TEMPLATES), 7)
        for house, (slug, area, quantities) in zip(TEMPLATES, expected):
            with self.subTest(slug=slug):
                self.assertEqual((house.slug, house.area), (slug, area))
                self.assertEqual([item.quantity for item in house.materials], quantities)
                form = HouseTemplateForm(house, original_data(house))
                self.assertTrue(form.is_valid(), form.errors)
                self.assertFalse(template_result(house, form.cleaned_data)["changed"])

    def test_adjustment_changes_copy_and_does_not_mutate_original(self):
        house = TEMPLATES_BY_SLUG["modelo-e"]
        form = HouseTemplateForm(house, {**original_data(house), "tp48": "320", "column_c": "0", "wide": "1"})
        self.assertTrue(form.is_valid())
        result = template_result(house, form.cleaned_data)
        self.assertEqual((result["blocks"], result["columns"], result["unknown"]), (502, 7, 1))
        self.assertTrue(result["changed"])
        self.assertEqual(house.materials[2].quantity, 316)
        self.assertEqual(sum(row["changed"] for row in result["rows"]), 3)

    def test_guion_is_unknown_and_duplicate_window_is_not_counted_twice(self):
        house = TEMPLATES_BY_SLUG["modelo-e"]
        form = HouseTemplateForm(house, original_data(house))
        self.assertTrue(form.is_valid())
        result = template_result(house, form.cleaned_data)
        self.assertEqual(result["unknown"], 2)
        self.assertEqual(sum(item.key == "regular" for item in house.materials), 1)
        self.assertIn("repite", house.note)

    def test_invalid_and_blank_known_quantities_rejected(self):
        house = TEMPLATES[0]
        for value in ("-1", "0.5", "100001", "NaN", ""):
            with self.subTest(value=value):
                form = HouseTemplateForm(house, {**original_data(house), "tp48": value})
                self.assertFalse(form.is_valid())


class TemplateViewTests(TestCase):
    @override_settings(DEBUG=True)
    def test_gallery_and_all_details(self):
        self.assertContains(self.client.get("/calculador-casas/plantillas/"), "Empieza por una casa")
        for house in TEMPLATES:
            response = self.client.get(f"/calculador-casas/plantillas/{house.slug}/")
            self.assertContains(response, house.name)
            self.assertContains(response, "Cantidades originales de TicoBlock")
            self.assertFalse(response.context["result"]["changed"])

    @override_settings(DEBUG=True)
    def test_update_validation_and_source_names(self):
        url = "/calculador-casas/plantillas/modelo-e/"
        data = original_data(TEMPLATES[0])
        response = self.client.post(url, {**data, "tp48": "320", "project": "<script>x</script>"})
        self.assertContains(response, "Lista ajustada por el usuario")
        self.assertContains(response, "&lt;script&gt;x&lt;/script&gt;")
        self.assertContains(response, "TP48")
        self.assertEqual(response.context["result"]["blocks"], 502)
        invalid = self.client.post(url, {**data, "tp48": "-1"})
        self.assertEqual(invalid.status_code, 400)
        self.assertIsNone(invalid.context["result"])
        self.assertEqual(self.client.get("/calculador-casas/plantillas/inventada/").status_code, 404)

    @override_settings(DEBUG=False)
    def test_access_control(self):
        for url in ("/calculador-casas/plantillas/", "/calculador-casas/plantillas/modelo-e/"):
            self.assertEqual(self.client.get(url).status_code, 302)

    @override_settings(DEBUG=True)
    def test_csrf(self):
        client = Client(enforce_csrf_checks=True)
        url = "/calculador-casas/plantillas/modelo-e/"
        self.assertEqual(client.post(url, original_data(TEMPLATES[0])).status_code, 403)
        client.get(url)
        self.assertEqual(client.post(url, original_data(TEMPLATES[0]),
            HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value).status_code, 200)
