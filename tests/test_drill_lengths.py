import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from freecad.drilltube_workbench import drill_lengths


class TestDrillLengths(unittest.TestCase):
    def test_exact_calibration_point(self):
        self.assertAlmostEqual(drill_lengths.jobber_length_mm(6.0), 93.0)

    def test_interpolates_between_points(self):
        length = drill_lengths.jobber_length_mm(4.5)
        self.assertGreater(length, drill_lengths.jobber_length_mm(4.0))
        self.assertLess(length, drill_lengths.jobber_length_mm(5.0))

    def test_extrapolates_below_table(self):
        length = drill_lengths.jobber_length_mm(0.5)
        self.assertGreater(length, 0)
        self.assertLess(length, drill_lengths.jobber_length_mm(1.0))

    def test_extrapolates_above_table(self):
        length = drill_lengths.jobber_length_mm(30.0)
        self.assertGreater(length, drill_lengths.jobber_length_mm(25.0))

    def test_stub_shorter_than_jobber_shorter_than_long(self):
        d = 6.0
        stub = drill_lengths.length_for(d, drill_lengths.CATEGORY_STUB)
        jobber = drill_lengths.length_for(d, drill_lengths.CATEGORY_JOBBER)
        long_ = drill_lengths.length_for(d, drill_lengths.CATEGORY_LONG)
        self.assertLess(stub, jobber)
        self.assertLess(jobber, long_)

    def test_unknown_category(self):
        with self.assertRaises(ValueError):
            drill_lengths.length_for(6.0, "Bogus")

    def test_invalid_diameter(self):
        with self.assertRaises(ValueError):
            drill_lengths.jobber_length_mm(0)


if __name__ == "__main__":
    unittest.main()
