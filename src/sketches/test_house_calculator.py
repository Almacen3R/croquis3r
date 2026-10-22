from django.test import Client, SimpleTestCase, TestCase, override_settings

from .house_calculator import HouseCalculatorForm, RECIPES, calculate_house


def entries(**changes):
    return {"project": "Prueba", "height": "0", "column_mode": "chain",
            "linear_columns": "0", "t_columns": "0",
            **{recipe.key: "0" for recipe in RECIPES}, **changes}


class HouseCalculationTests(SimpleTestCase):
    def calculate(self, **changes):
        form = HouseCalculatorForm(entries(**changes))
        self.assertTrue(form.is_valid(), form.errors)
        return calculate_house(form.cleaned_data)

    def test_reference_13_5_m_matches_extracted_excel_and_scan(self):
        result = self.calculate(panel_4="6", panel_5="1", height="1")
        self.assertEqual((result["tp50"], result["tp37"], result["columns"], result["beam"]),
                         (240, 84, 8, 34))
        self.assertEqual(str(result["meters"]), "13.5")
        self.assertEqual((result["mortar"], result["wall_steel"], result["beam_steel"], result["weight"]),
                         (17, 10, 2, 6308))

    def test_full_2_m_rounds_half_up_like_excel(self):
        result = self.calculate(panel_4="1", height="2")
        self.assertEqual((result["tp50"], result["tp37"], result["wall_steel"],
                          result["beam"], result["mortar"], result["weight"]), (36, 12, 2, 10, 3, 1044))
        self.assertTrue(any("cero varillas de viga" in warning for warning in result["warnings"]))

    def test_second_layer_doubles_rounded_first_layer_not_raw_length(self):
        result = self.calculate(panel_6="1", height="2")
        self.assertEqual(result["beam_one"], 3)  # 1 × 2,5 → 3
        self.assertEqual(result["beam"], 6)
        self.assertEqual(result["wall_steel"], 1)  # 0,5 → 1, no bankers rounding

    def test_all_current_recipes_after_confirmed_door_module_changes(self):
        result = self.calculate(**{recipe.key: "1" for recipe in RECIPES}, height="1")
        self.assertEqual((result["tp50"], result["tp37"], result["columns"], result["beam"],
                          result["mortar"], result["wall_steel"], result["beam_steel"], result["weight"]),
                         (168, 122, 19, 68, 15, 11, 4, 6682))
        self.assertEqual(str(result["meters"]), "24.5")

    def test_empty_chain_has_no_phantom_column(self):
        result = self.calculate()
        self.assertEqual((result["panels"], result["columns"], result["weight"]), (0, 0, 0))
        self.assertTrue(any("Excel manual muestra una" in w for w in result["warnings"]))

    def test_manual_columns_use_only_current_c_and_e_products(self):
        result = self.calculate(column_mode="manual", linear_columns="3", t_columns="2")
        self.assertEqual(result["columns"], 5)
        self.assertEqual(result["weight"], 540)
        self.assertEqual([label for label, _, _ in result["items"] if label.startswith("Columna")],
                         ["Columna C · lineal", "Columna E · esquina/cruz"])
        self.assertEqual(len([key for key in HouseCalculatorForm().fields if key.endswith("_columns")]), 2)

    def test_chain_ignores_manual_columns(self):
        result = self.calculate(panel_7="1", linear_columns="20", t_columns="5")
        self.assertEqual((result["linear_columns"], result["t_columns"]), (2, 0))

    def test_door_adds_length_without_wall_blocks_or_wall_steel(self):
        result = self.calculate(panel_18="1", panel_101="1", panel_102="1", height="1")
        self.assertEqual((result["tp50"], result["tp37"], result["mortar"], result["wall_steel"], result["beam"]),
                         (0, 0, 0, 0, 17))

    def test_base_height_includes_one_crown_beam(self):
        result = self.calculate(panel_4="1")
        self.assertEqual((result["beam"], result["beam_steel"]), (5, 0))

    def test_invalid_inputs_rejected(self):
        for key, value in (("panel_4", "-1"), ("panel_4", "1.5"), ("panel_4", "101"),
                           ("panel_4", "NaN"), ("panel_4", ""), ("height", "3"),
                           ("column_mode", "unknown"), ("linear_columns", "-2")):
            with self.subTest(key=key, value=value):
                self.assertFalse(HouseCalculatorForm(entries(**{key: value})).is_valid())


class HouseCalculatorViewTests(TestCase):
    @override_settings(DEBUG=True)
    def test_get_and_post_render_and_escape_project_name(self):
        self.assertContains(self.client.get("/calculador-casas/"), "De paños a materiales")
        response = self.client.post("/calculador-casas/", entries(panel_4="1", project="<script>x</script>"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["result"]["tp50"], 36)
        self.assertContains(response, "&lt;script&gt;x&lt;/script&gt;")
        self.assertNotContains(response, "<script>x</script>")

    @override_settings(DEBUG=True)
    def test_invalid_form_does_not_present_stale_result(self):
        response = self.client.post("/calculador-casas/", entries(panel_4="-1"))
        self.assertEqual(response.status_code, 400)
        self.assertIsNone(response.context["result"])

    @override_settings(DEBUG=False)
    def test_production_requires_authorized_user(self):
        self.assertEqual(self.client.get("/calculador-casas/").status_code, 302)
        self.assertEqual(self.client.post("/calculador-casas/", entries()).status_code, 302)

    @override_settings(DEBUG=True)
    def test_csrf_enforced(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post("/calculador-casas/", entries()).status_code, 403)
        client.get("/calculador-casas/")
        response = client.post("/calculador-casas/", entries(),
                               HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value)
        self.assertEqual(response.status_code, 200)
