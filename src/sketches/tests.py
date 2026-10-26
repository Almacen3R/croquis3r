from django.conf import settings
import json

from django.contrib.auth import get_user_model
from .testing import AuthenticatedTestCase as TestCase
from django.test import Client, override_settings

from catalog.models import Article
from .domain import InvalidDocument, calculate, validate_document
from .models import Sketch


def wall(oid="wall", **kwargs):
    return {"id": oid, "kind": "wall", "label": oid, "x1": 0, "y1": 0, "x2": 4, "y2": 0,
            "height": 2.4, "thickness": .15, "assignments": [], **kwargs}


def door(**kwargs):
    return {"id": "door", "kind": "door", "label": "Puerta", "wall_id": "wall", "offset": 1,
            "width": .9, "height": 2.1, "sill": 0, "assignments": [], **kwargs}


def document(*objects):
    return {"version": 1, "objects": list(objects)}


class CalculationTests(TestCase):
    def setUp(self):
        super().setUp()
        self.article = Article.objects.create(sku="TEST-BLOCK", name="Block de prueba")
        self.articles = {self.article.id: self.article}
        self.rule = {"article_id": self.article.id, "basis": "area", "factor": "12.5", "waste_percent": "5"}

    def test_net_wall_area_deducts_opening_then_applies_waste_and_ceiling(self):
        result = calculate(document(wall(assignments=[self.rule]), door()), self.articles)
        self.assertEqual(result["items"][0]["quantity"], 102)
        self.assertEqual(result["details"][0]["base"], "7.71")
        self.assertEqual(result["details"][0]["unrounded"], "101.19375")

    def test_fixed_and_linear_rules_and_rounding_per_object(self):
        a = wall(assignments=[{**self.rule, "basis": "length", "factor": "0.3", "waste_percent": "0"}])
        b = wall("b", y1=2, y2=2, assignments=[{**self.rule, "basis": "object", "factor": "1.1", "waste_percent": "0"}])
        result = calculate(document(a, b), self.articles)
        self.assertEqual(result["items"][0]["quantity"], 4)
        self.assertEqual([d["quantity"] for d in result["details"]], [2, 2])

    def test_reversed_wall_and_door_article(self):
        w = wall(x1=4, x2=0)
        o = door(assignments=[{**self.rule, "basis": "object", "factor": "1", "waste_percent": "0"}])
        result = calculate(document(w, o), self.articles)
        self.assertEqual(result["items"][0]["quantity"], 1)

    def test_door_orientation_is_preserved_without_affecting_materials(self):
        baseline = calculate(document(wall(assignments=[self.rule]), door()), self.articles)["items"]
        for rotation in range(4):
            doc = document(wall(assignments=[self.rule]), door(door_rotation=rotation))
            self.assertEqual(validate_document(doc, self.articles)["objects"][1]["door_rotation"], rotation)
            self.assertEqual(calculate(doc, self.articles)["items"], baseline)
        for rotation in (-1, 4, True, "1", 1.5, None):
            with self.subTest(rotation=rotation), self.assertRaises(InvalidDocument):
                validate_document(document(wall(), door(door_rotation=rotation)), self.articles)

    def test_contiguous_walls_are_allowed(self):
        self.assertEqual(len(validate_document(document(wall(), wall("b", x1=4, x2=8)), self.articles)["objects"]), 2)

    def test_invalid_geometry_and_rules_are_rejected(self):
        cases = [
            document(wall(x2=0)), document(wall(height="NaN")),
            document(wall(x1=True)), document(wall(), wall()),
            document(wall(), wall("b", x1=2, x2=5)),
            document(wall(x2=3,y2=4), wall("b", x1=1.5,y1=2,x2=6,y2=8)),
            document(wall(), door(width=5)), document(wall(), door(height=3)),
            document(wall(), door(sill=1)), document(door(wall_id="missing")),
            document(wall(), door(), door(id="other", offset=1.5)),
            document(wall(assignments=[{**self.rule, "factor": -1}])),
            document(wall(assignments=[{**self.rule, "article_id": 99999}])),
            document(wall(assignments=[self.rule, self.rule])),
            document(wall(assignments=[{**self.rule, "article_id": True}])),
            document(wall(assignments=[{**self.rule, "waste_percent": 101}])),
            document(wall(assignments=[None])), document(wall(assignments=None)),
            {"version": 1, "objects": "invalid"}, document(*[wall(str(i)) for i in range(301)]), None,
        ]
        for case in cases:
            with self.subTest(case=str(case)[:120]), self.assertRaises(InvalidDocument):
                calculate(case, self.articles)

    def test_diagonal_wall_uses_real_length_and_deducts_its_opening(self):
        result = calculate(document(wall(x2=3,y2=4,assignments=[self.rule]), door()), self.articles)
        self.assertEqual(result["details"][0]["base"], "10.11")
        self.assertEqual(result["items"][0]["quantity"], 133)

    def test_diagonal_contiguous_and_parallel_walls_do_not_overlap(self):
        doc = document(wall(x2=3,y2=4), wall("b",x1=6,y1=8,x2=3,y2=4), wall("c",y1=1,x2=3,y2=5))
        self.assertEqual(len(validate_document(doc,self.articles)["objects"]),3)


@override_settings(DEBUG=True)
class ApiTests(TestCase):
    def setUp(self):
        super().setUp()
        self.article = Article.objects.create(sku="DEMO-BLOCK", name="Block")
        self.data = {"name": "Casa 1", "document": document(wall()), "is_template": False}

    def test_columns_survive_save_and_reopen_without_changing_legacy_counts(self):
        columns = [{"id": "c", "kind": "column", "label": "Esquina", "x": 0, "y": 0, "column_type": "E"}]
        data = {**self.data, "document": {**document(wall()), "columns": columns}}
        response = self.client.post("/api/sketches/", data=json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 201)
        saved = self.client.get(f'/api/sketches/{response.json()["id"]}/').json()
        self.assertEqual(saved["document"]["columns"], columns)

    def post(self, url, data):
        return self.client.post(url, json.dumps(data), content_type="application/json")

    def test_save_load_and_revision_conflict_preserves_newer_document(self):
        created = self.post("/api/sketches/", self.data)
        self.assertEqual(created.status_code, 201)
        obj = created.json()
        url = f'/api/sketches/{obj["id"]}/'
        self.assertEqual(self.client.get(url).json()["document"], self.data["document"])
        changed = {**self.data, "name": "Casa corregida", "revision": 1}
        self.assertEqual(self.client.put(url, json.dumps(changed), content_type="application/json").status_code, 200)
        self.assertEqual(self.client.put(url, json.dumps(changed), content_type="application/json").status_code, 409)
        sketch = Sketch.objects.get()
        self.assertEqual((sketch.name, sketch.revision), ("Casa corregida", 2))

    def test_invalid_input_never_creates_sketch(self):
        for data in [[], None, {}, {**self.data, "name": " "}, {**self.data, "document": document(wall(height=-1))}, {**self.data, "is_template": "yes"}]:
            self.assertEqual(self.post("/api/sketches/", data).status_code, 400)
        self.assertEqual(Sketch.objects.count(), 0)

    def test_save_and_load_rotated_wall_with_opening(self):
        data = {**self.data,"document":document(wall(x2=3,y2=4),door(width=2))}
        created = self.post("/api/sketches/",data)
        self.assertEqual(created.status_code,201)
        loaded = self.client.get(f'/api/sketches/{created.json()["id"]}/').json()
        self.assertEqual(loaded["document"],data["document"])

    def test_only_catalog_door_modules_can_be_saved(self):
        for width in (.5, 1, 1.5, 2, 3):
            data = {**self.data, "document": document(wall(), door(width=width, offset=0))}
            response = self.post("/api/sketches/", data)
            self.assertEqual(response.status_code, 201, response.content)
            self.assertEqual(response.json()["document"], data["document"])
        for width in (.9, 2.5):
            data = {**self.data, "document": document(wall(), door(width=width, offset=0))}
            response = self.post("/api/sketches/", data)
            self.assertEqual(response.status_code, 400)
            self.assertIn("fuera de catálogo", response.json()["error"])
        self.assertEqual(Sketch.objects.count(), 5)

    def test_legacy_invalid_door_remains_readable_and_requires_explicit_correction(self):
        legacy = document(wall(), door(width=.9))
        sketch = Sketch.objects.create(name="Anterior", document=legacy)
        url = f"/api/sketches/{sketch.pk}/"
        self.assertEqual(self.client.get(url).json()["document"], legacy)
        data = {**self.data, "document": legacy, "revision": 1}
        response = self.client.put(url, json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 400)
        sketch.refresh_from_db()
        self.assertEqual(sketch.document, legacy)
        self.assertEqual(sketch.revision, 1)
        data["document"] = document(wall(), door(width=1.5))
        self.assertEqual(self.client.put(url, json.dumps(data), content_type="application/json").status_code, 200)

    def test_catalog_filters_inactive_and_estimate_rejects_them(self):
        self.article.active = False
        self.article.save()
        self.assertEqual(self.client.get("/api/catalog/").json()["articles"], [])
        rule = {"article_id": self.article.id, "factor": 1, "basis": "object"}
        self.assertEqual(self.post("/api/estimate/", {"document": document(wall(assignments=[rule]))}).status_code, 400)

    def test_templates_and_health(self):
        self.assertEqual(self.post("/api/sketches/", {**self.data, "is_template": True}).status_code, 201)
        self.assertTrue(self.client.get("/api/sketches/").json()["sketches"][0]["is_template"])
        self.assertEqual(self.post("/api/object-templates/", {"name": "Pared estándar", "specification": wall()}).status_code, 201)
        self.assertEqual(len(self.client.get("/api/object-templates/").json()["templates"]), 1)
        self.assertEqual(self.client.get("/health/").json()["application"], "croquis3r")

    def test_mutations_require_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post("/api/sketches/", json.dumps(self.data), content_type="application/json").status_code, 403)
        self.assertEqual(client.get("/").status_code, 200)
        token = client.cookies[settings.CSRF_COOKIE_NAME].value
        self.assertEqual(client.post("/api/sketches/", json.dumps(self.data), content_type="application/json", HTTP_X_CSRFTOKEN=token).status_code, 201)

    @override_settings(DEBUG=False, SECURE_SSL_REDIRECT=False)
    def test_production_allows_active_sales_account_without_admin_access(self):
        self.client.logout()
        self.assertEqual(self.client.get("/api/sketches/").status_code, 403)
        self.assertEqual(self.client.get("/").status_code, 302)
        user = get_user_model().objects.create_user(username="employee", password="test-password")
        self.client.force_login(user)
        self.assertEqual(self.client.get("/api/sketches/").status_code, 200)
        user.is_staff = True
        user.save()
        self.assertEqual(self.client.get("/api/sketches/").status_code, 200)
