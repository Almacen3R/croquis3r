from decimal import Decimal

from django.test import SimpleTestCase

from .beams import beam_runs, pieces
from .house_calculator import HouseCalculatorForm, calculate_house
from .modulation import calculate_modulation
from .test_house_calculator import entries
from .test_modulation import doc, opening, wall


class BeamTests(SimpleTestCase):
    def test_nominal_forty_cm_requires_whole_pieces_rounded_up(self):
        for length, expected in [('0.5', 2), ('1', 3), ('1.5', 4), ('2', 5), ('3.5', 9)]:
            self.assertEqual(pieces(Decimal(length)), expected)

    def test_collinear_adjacent_walls_merge_but_gaps_and_corners_do_not(self):
        walls = [wall(x2=1.5), wall('b', 3, 0, 1.5, 0), wall('c', 4, 0, 4.5, 0), wall('d', 3, 0, 3, 1)]
        self.assertEqual(sorted(beam_runs(walls)), [Decimal('.5'), Decimal('1'), Decimal('3')])

    def test_panel_preference_columns_and_openings_do_not_round_beam_again(self):
        for span in ('2', '1.5', '1', '0.5'):
            data = doc(wall(), opening(), max_span=span)
            result = calculate_modulation(data, {})
            self.assertEqual(result['status'], 'ready')
            self.assertEqual(next(r['quantity'] for r in result['items'] if r['name'] == 'Vigabloque'), 10)
            self.assertEqual(result['beam_details'], [{'length': Decimal('4'), 'pieces': 10}])
        data['columns'] = [{'id': 'c', 'x': 1.5, 'y': 0, 'column_type': 'C'}]
        self.assertEqual(calculate_modulation(data, {})['beam_details'][0]['pieces'], 10)

    def test_rectangle_beam_follows_wall_lengths_and_includes_door_module(self):
        walls = [wall(), wall('b', 4, 0, 4, 3), wall('c', 4, 3, 0, 3), wall('d', 0, 3, 0, 0)]
        data = doc(*walls, opening(kind='door', offset=1, width=2))
        result = calculate_modulation(data, {})
        self.assertEqual(result['beam_layers'], 1)
        # 4 + 3 + 4 + 3 m -> 10 + 8 + 10 + 8, NOT ceil(14 * 2.5).
        self.assertEqual(next(r['quantity'] for r in result['items'] if r['name'] == 'Vigabloque'), 36)

    def test_heights_and_ten_cm_exception(self):
        for height, family, expected in [(2.5, .12, 5), (2.7, .12, 5), (2.9, .12, 10), (2.5, .1, 0)]:
            result = calculate_modulation(doc(wall(x2=2, height=height, thickness=family)), {})
            self.assertEqual(next(r['quantity'] for r in result['items'] if r['name'] == 'Vigabloque'), expected)

    def test_manual_rounds_per_panel_and_explains_basis(self):
        form = HouseCalculatorForm(entries(panel_7='2'))
        self.assertTrue(form.is_valid())
        result = calculate_house(form.cleaned_data)
        self.assertEqual((result['beam'], result['beam_basis']), (4, 'paño independiente'))
        self.assertTrue(result['version'].endswith('2026-10-22-v4'))
