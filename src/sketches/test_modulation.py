import json

from django.test import Client, SimpleTestCase, TestCase, override_settings

from .domain import InvalidDocument, validate_document
from .modulation import calculate_modulation


def wall(oid="w", x1=0, y1=0, x2=4, y2=0, **extra):
    return {"id": oid, "kind": "wall", "label": oid, "x1": x1, "y1": y1,
            "x2": x2, "y2": y2, "height": 2.5, "thickness": .12, "assignments": [], **extra}


def opening(oid="o", kind="window", **extra):
    return {"id": oid, "kind": kind, "label": oid, "wall_id": "w", "offset": 1.5,
            "width": 1, "height": 1.2, "sill": 1 if kind == "window" else 0,
            "assignments": [], **extra}


def doc(*objects, **settings):
    return {"version": 1, "objects": list(objects), "ticoblock": settings}


class ModulationTests(SimpleTestCase):
    def test_drawn_columns_replace_manual_counts_and_share_intersections(self):
        data = doc(wall(), wall("b", 4, 0, 4, 2), linear_columns=99, t_columns=99)
        data["columns"] = [{"id": f"c{i}", "x": x, "y": y, "column_type": kind}
                           for i, (x, y, kind) in enumerate([(0, 0, "C"), (2, 0, "C"), (4, 0, "E"), (4, 2, "C")])]
        result = calculate_modulation(data, {})
        self.assertEqual(result["status"], "ready")
        self.assertEqual([r["quantity"] for r in result["items"]][2:4], [3, 1])
        self.assertFalse(result["columns_pending"])
        self.assertEqual(result["missing_column_positions"], [])
        self.assertEqual(result["drawn_column_count"], 4)

    def test_intermediate_column_splits_panels_and_recalculates_blocks(self):
        data = doc(wall(x2=2))
        baseline = calculate_modulation(data, {})
        data["columns"] = [{"id": "c", "x": 1, "y": 0, "column_type": "C"}]
        result = calculate_modulation(data, {})
        self.assertEqual([s["length"] for s in result["segments"]], [1, 1])
        self.assertNotEqual(result["items"][0]["quantity"], baseline["items"][0]["quantity"])
        self.assertTrue(result["columns_pending"])
        self.assertEqual(len(result["missing_column_positions"]), 2)
        self.assertIsNone(result["weight"])

    def test_empty_drawn_columns_do_not_restore_old_manual_totals(self):
        data = doc(wall(x2=2), linear_columns=7, t_columns=3)
        data["columns"] = []
        result = calculate_modulation(data, {})
        self.assertEqual([r["quantity"] for r in result["items"]][2:4], [0, 0])
        self.assertTrue(result["columns_pending"])

    def test_off_wall_non_modular_and_inside_opening_columns_block_calculation(self):
        for x, y in [(1, 2), (.7, 0), (2, 0)]:
            data = doc(wall(), opening())
            data["columns"] = [{"id": "c", "x": x, "y": y, "column_type": "C"}]
            result = calculate_modulation(data, {})
            self.assertEqual(result["status"], "incomplete")
            self.assertEqual(result["items"], [])
            self.assertEqual(result["issues"][0]["object_id"], "c")

    def test_column_validation_rejects_duplicates_and_obsolete_types(self):
        column = {"id": "c", "x": 0, "y": 0, "column_type": "C"}
        cases = [[column, {**column, "id": "other"}], [{**column, "column_type": "codo"}],
                 [{**column, "id": "w"}], [{**column, "x": True}], [{**column, "x": "NaN"}], None]
        for columns in cases:
            with self.subTest(columns=columns), self.assertRaises(InvalidDocument):
                validate_document({**doc(wall()), "columns": columns}, {})

    def test_reference_13_5_m_matches_manual_and_only_uses_explicit_column_quantities(self):
        result = calculate_modulation(doc(wall(x2=13.5, height=2.7), max_span="2", linear_columns=8), {})
        self.assertEqual(result["status"], "ready")
        values = [row["quantity"] for row in result["items"]]
        self.assertEqual(values, [240, 84, 8, 0, 34, 17, 10, 2])
        self.assertEqual(len(result["column_positions"]), 8)

    def test_rectangle_4_by_3_with_2_m_door_and_1_m_window(self):
        walls = [wall(), wall("b", 4, 0, 4, 3), wall("c", 4, 3, 0, 3), wall("d", 0, 3, 0, 0)]
        result = calculate_modulation(doc(*walls, opening(), opening("door", "door", wall_id="c", offset=1, width=2), max_span="1.5"), {})
        self.assertEqual(result["status"], "ready")
        self.assertEqual([row["quantity"] for row in result["items"]], [173, 101, None, None, 36, 14, 8, 2])
        self.assertTrue(result["columns_pending"])
        self.assertEqual((result["panels"], result["meters"], len(result["column_positions"])), (10, 14, 10))
        self.assertEqual(sum(s["kind"] == "Puerta estándar" for s in result["segments"]), 1)

    def test_old_paper_door_one_meter_requires_review_without_rewriting_sketch(self):
        data=doc(wall(),opening('p','door',offset=1,width=1))
        result=calculate_modulation(data,{})
        self.assertEqual(result['status'],'incomplete')
        self.assertEqual(data['objects'][1]['width'],1)
        self.assertEqual(result['issues'][0]['object_id'],'p')

    def test_rectangle_with_confirmed_bath_door_matches_current_manual_recipe(self):
        walls = [wall(x2=4),wall('b',4,0,4,4),wall('c',4,4,0,4),wall('d',0,4,0,0)]
        data=doc(*walls,opening(wall_id='b'),opening('v2',wall_id='c',offset=2.5,width=1.5),
                 opening('p','door',wall_id='c',offset=1,width=1.5),linear_columns=6,t_columns=4)
        result=calculate_modulation(data,{})
        self.assertEqual(result['status'],'ready')
        self.assertEqual([r['quantity'] for r in result['items']],[219,94,6,4,40,16,10,3])
        self.assertEqual((result['panels'],result['meters'],result['weight']),(10,16,6258))
        self.assertEqual(len(result['column_positions']),10)
        right=sorted((s for s in result['segments'] if s['wall_id']=='b'),key=lambda s:s['start'])
        self.assertEqual([s['length'] for s in right],[1.5,1,1.5])

    def test_default_prefers_two_then_one_point_five_then_one_then_half(self):
        for length, expected in [(4,[2,2]),(3.5,[2,1.5]),(3,[2,1]),(2.5,[2,.5])]:
            result=calculate_modulation(doc(wall(x2=length)),{})
            self.assertEqual([s['length'] for s in result['segments']],expected)

    def test_window_kinds_use_their_own_recipe_and_preserve_metadata(self):
        for kind, expected in (("regular", (5, 5)), ("kitchen", (6, 6)), ("bath", (10, 10))):
            data = doc(wall(x2=1), opening(offset=0, panel_type=kind))
            result = calculate_modulation(data, {})
            self.assertEqual(tuple(row["quantity"] for row in result["items"][:2]), expected)
            self.assertEqual(validate_document(data, {})["objects"][1]["panel_type"], kind)

    def test_non_modular_lengths_positions_and_missing_recipes_block_entire_total(self):
        cases = (doc(wall(x2=4.1)), doc(wall(), opening(offset=1.2)),
                 doc(wall(), opening(width=1.2)), doc(wall(), opening(width=2, offset=1, panel_type="bath")),
                 doc(wall(height=2.4)), doc(wall(thickness=.15)), doc(wall(), opening(kind="door", offset=1, width=.5)))
        for data in cases:
            with self.subTest(data=data):
                result = calculate_modulation(data, {})
                self.assertEqual(result["status"], "incomplete")
                self.assertEqual(result["items"], [])
                self.assertTrue(result["issues"])

    def test_t_junction_splits_wall_and_shares_position(self):
        result = calculate_modulation(doc(wall(x2=3), wall("b", 1, 0, 1, 1)), {})
        self.assertEqual(result["status"], "ready")
        self.assertEqual(sum(p["x"] == 1 and p["y"] == 0 for p in result["column_positions"]), 1)
        self.assertFalse(any(s["x1"] < 1 < s["x2"] and s["wall_id"] == "w" for s in result["segments"]))

    def test_crossing_walls_split_at_shared_intersection(self):
        result = calculate_modulation(doc(wall(x2=3), wall("b", 1.5, -1.5, 1.5, 1.5)), {})
        self.assertEqual(result["status"], "ready")
        self.assertEqual(len(result["segments"]), 4)
        self.assertEqual(len(result["column_positions"]), 5)

    def test_crossing_opening_or_non_modular_junction_block_result(self):
        for b in (wall("b", 2, 0, 2, 1), wall("b", .7, 0, .7, 1)):
            self.assertEqual(calculate_modulation(doc(wall(), opening(), b), {})["status"], "incomplete")

    def test_vertical_separated_openings_have_no_combined_recipe(self):
        result = calculate_modulation(doc(wall(), opening(height=.5, sill=0), opening("other", height=.5, sill=1)), {})
        self.assertEqual(result["status"], "incomplete")

    def test_reversed_and_diagonal_walls_use_true_length(self):
        result = calculate_modulation(doc(wall(x1=3, y1=4, x2=0, y2=0)), {})
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["meters"], 5)
        self.assertEqual(sum(s["length"] for s in result["segments"]), 5)

    def test_mixed_height_requires_a_project_choice(self):
        result = calculate_modulation(doc(wall(), wall("b", 4, 0, 4, 3, height=2.7)), {})
        self.assertEqual(result["status"], "incomplete")

    def test_empty_has_zero_columns_and_quantities(self):
        result = calculate_modulation(doc(), {})
        self.assertEqual(result["status"], "empty")
        self.assertEqual(result["items"], [])
        self.assertEqual(result["column_positions"], [])

    def test_invalid_settings_or_window_type_are_rejected(self):
        for settings in ({"max_span": "3"}, {"t_columns": -1}, {"linear_columns": .5}, {"t_columns": True}):
            with self.assertRaises(InvalidDocument):
                calculate_modulation(doc(wall(), **settings), {})
        with self.assertRaises(InvalidDocument):
            calculate_modulation(doc(wall(), opening(panel_type="invented")), {})


@override_settings(DEBUG=True)
class ModulationApiTests(TestCase):
    def test_api_and_persistence_round_trip_include_options_and_window_recipe(self):
        data = doc(wall(), opening(panel_type="kitchen"), max_span="2", linear_columns=3)
        response = self.client.post("/api/ticoblock-estimate/", json.dumps({"document": data}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ready")
        saved = self.client.post("/api/sketches/", json.dumps({"name": "Caso TicoBlock", "document": data}), content_type="application/json")
        self.assertEqual(saved.status_code, 201)
        loaded = self.client.get(f'/api/sketches/{saved.json()["id"]}/').json()["document"]
        self.assertEqual(loaded["ticoblock"]["linear_columns"], 3)
        self.assertEqual(loaded["objects"][1]["panel_type"], "kitchen")

    def test_invalid_input_and_csrf_are_handled(self):
        url = "/api/ticoblock-estimate/"
        self.assertEqual(self.client.post(url, "null", content_type="application/json").status_code, 400)
        response = self.client.post(url, json.dumps({"document": doc(wall(x2=1.1))}), content_type="application/json")
        self.assertEqual(response.json()["status"], "incomplete")
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(url, "{}", content_type="application/json").status_code, 403)

    @override_settings(DEBUG=False)
    def test_production_access_is_restricted(self):
        self.assertEqual(self.client.post("/api/ticoblock-estimate/", "{}", content_type="application/json").status_code, 403)
