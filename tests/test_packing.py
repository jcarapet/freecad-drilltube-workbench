import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from freecad.drilltube_workbench import packing


class TestPacking(unittest.TestCase):
    def test_known_ratios(self):
        self.assertAlmostEqual(packing.enclosing_diameter_ratio(1), 1.0)
        self.assertAlmostEqual(packing.enclosing_diameter_ratio(2), 2.0)
        self.assertAlmostEqual(packing.enclosing_diameter_ratio(3), 2.1547005384, places=6)
        self.assertAlmostEqual(packing.enclosing_diameter_ratio(4), 2.4142135624, places=6)
        self.assertAlmostEqual(packing.enclosing_diameter_ratio(7), 3.0)

    def test_ratio_grows_monotonically(self):
        ratios = [packing.enclosing_diameter_ratio(n) for n in range(1, 40)]
        for a, b in zip(ratios, ratios[1:]):
            self.assertLessEqual(a, b + 1e-9)

    def test_large_n_uses_asymptotic_formula(self):
        ratio = packing.enclosing_diameter_ratio(100)
        self.assertGreater(ratio, packing.enclosing_diameter_ratio(19))
        self.assertTrue(math.isfinite(ratio))

    def test_ratio_does_not_jump_at_table_boundary(self):
        # Regression test: the large-N fallback formula once had a spurious factor of 2,
        # which didn't break monotonicity (still an increase) but made the ratio roughly
        # double between count=19 (from the table) and count=20 (from the formula) --
        # reported as "tube diameter jumps significantly at >=20 bits". Consecutive counts
        # should differ by roughly sqrt((n+1)/n), not by a large discontinuous jump.
        for n in range(15, 30):
            a = packing.enclosing_diameter_ratio(n)
            b = packing.enclosing_diameter_ratio(n + 1)
            self.assertLess(b / a, 1.15,
                             "ratio jumped by {:.1f}% from count={} to count={}".format(
                                 (b / a - 1) * 100, n, n + 1))

    def test_ratio_close_to_asymptotic_prediction(self):
        # sqrt(N/density) is the leading-order asymptotic behavior; the real ratio
        # (table or formula) should track it within a modest constant factor, not be
        # off by ~2x the way the spurious-factor-of-2 bug made large-N counts come out.
        density = math.pi / (2 * math.sqrt(3))
        for n in (19, 20, 25, 50, 100):
            ratio = packing.enclosing_diameter_ratio(n)
            predicted = math.sqrt(n / density)
            self.assertLess(ratio / predicted, 1.3)
            self.assertGreater(ratio / predicted, 0.8)

    def test_bore_diameter_single_bit(self):
        self.assertAlmostEqual(packing.bore_diameter(6.0, 1, clearance=0.0), 6.0)

    def test_bore_diameter_with_clearance(self):
        d = packing.bore_diameter(6.0, 1, clearance=0.3)
        self.assertAlmostEqual(d, 6.3)

    def test_bore_diameter_multiple_bits(self):
        d = packing.bore_diameter(6.0, 7, clearance=0.0)
        self.assertAlmostEqual(d, 18.0)  # ratio 3.0 * 6.0mm

    def test_invalid_count(self):
        with self.assertRaises(ValueError):
            packing.enclosing_diameter_ratio(0)

    def test_invalid_diameter(self):
        with self.assertRaises(ValueError):
            packing.bore_diameter(0, 1)


if __name__ == "__main__":
    unittest.main()
