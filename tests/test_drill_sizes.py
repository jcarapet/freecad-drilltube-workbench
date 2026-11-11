import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from freecad.drilltube_workbench import drill_sizes


class TestDrillSizes(unittest.TestCase):
    def test_fractional_sizes_count_and_ends(self):
        sizes = drill_sizes.fractional_sizes_in()
        self.assertEqual(len(sizes), 64)
        self.assertEqual(sizes[0], ('1/64"', 1 / 64.0))
        self.assertEqual(sizes[-1], ('1"', 1.0))

    def test_fractional_label_reduces(self):
        table = drill_sizes.fractional_sizes_lookup_in()
        self.assertIn('1/4"', table)
        self.assertAlmostEqual(table['1/4"'], 0.25)
        self.assertIn('1/2"', table)
        self.assertAlmostEqual(table['1/2"'], 0.5)

    def test_number_gauge_known_values(self):
        self.assertAlmostEqual(drill_sizes.NUMBER_GAUGE_SIZES_IN["#1"], 0.2280)
        self.assertAlmostEqual(drill_sizes.NUMBER_GAUGE_SIZES_IN["#80"], 0.0135)
        self.assertEqual(len(drill_sizes.NUMBER_GAUGE_SIZES_IN), 80)

    def test_letter_gauge_known_values(self):
        self.assertAlmostEqual(drill_sizes.LETTER_GAUGE_SIZES_IN["A"], 0.234)
        self.assertAlmostEqual(drill_sizes.LETTER_GAUGE_SIZES_IN["Z"], 0.413)
        self.assertEqual(len(drill_sizes.LETTER_GAUGE_SIZES_IN), 26)

    def test_resolve_metric(self):
        self.assertAlmostEqual(drill_sizes.resolve_diameter_mm(drill_sizes.SYSTEM_METRIC, 6.0), 6.0)

    def test_resolve_custom(self):
        self.assertAlmostEqual(drill_sizes.resolve_diameter_mm(drill_sizes.SYSTEM_CUSTOM, 7.25), 7.25)

    def test_resolve_fractional(self):
        mm = drill_sizes.resolve_diameter_mm(drill_sizes.SYSTEM_FRACTIONAL, '1/4"')
        self.assertAlmostEqual(mm, 0.25 * 25.4)

    def test_resolve_number(self):
        mm = drill_sizes.resolve_diameter_mm(drill_sizes.SYSTEM_NUMBER, "#30")
        self.assertAlmostEqual(mm, 0.1285 * 25.4)

    def test_resolve_letter(self):
        mm = drill_sizes.resolve_diameter_mm(drill_sizes.SYSTEM_LETTER, "Q")
        self.assertAlmostEqual(mm, 0.332 * 25.4)

    def test_resolve_unknown_system(self):
        with self.assertRaises(ValueError):
            drill_sizes.resolve_diameter_mm("Nonsense", 1)


if __name__ == "__main__":
    unittest.main()
