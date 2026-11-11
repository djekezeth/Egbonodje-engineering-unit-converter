# Additional regression tests for the UX workflows and edge cases.
# Run: python -m unittest discover -s tests -v

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from unit_converter import convert_batch, convert_value, format_number, parse_measurement


class WorkflowTests(unittest.TestCase):
    def test_swap_can_preserve_measured_quantity(self):
        # The GUI's Swap button uses the first result as the reversed input.
        new_input = convert_value("Length", "mm", "in", 25.4)
        self.assertAlmostEqual(new_input, 1)
        self.assertAlmostEqual(convert_value("Length", "in", "mm", new_input), 25.4)

    def test_zero_and_precision_behavior(self):
        self.assertEqual(convert_value("Length", "mm", "in", 0), 0)
        self.assertEqual(convert_value("Temperature", "°C", "°F", 0), 32)
        self.assertEqual(format_number(1 / 3, 2), "0.33")
        self.assertEqual(format_number(1 / 3, 8), "0.33333333")

    def test_small_nonzero_output_not_hidden_by_rounding(self):
        small = convert_value("Length", "mm", "in", 1e-8)
        self.assertNotEqual(format_number(small, 4), "0.0000")

    def test_high_and_low_valid_temperatures(self):
        self.assertAlmostEqual(convert_value("Temperature", "°F", "°C", 212), 100)
        self.assertAlmostEqual(convert_value("Temperature", "°C", "°F", -40), -40)

    def test_batch_capacity_and_invalid_values(self):
        rows = convert_batch("Mass", "kg", "lb", "1\n" * 500)
        self.assertEqual(len(rows), 500)
        self.assertTrue(all(not row[3] for row in rows))
        with self.assertRaises(ValueError):
            convert_batch("Mass", "kg", "lb", "1\n" * 501)

    def test_invalid_nonfinite_input_and_units(self):
        for bad in ("NaN", "Infinity", "not a number"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    parse_measurement(bad, "Length")
        with self.assertRaises(ValueError):
            convert_value("Speed", "kg", "m/s", 12)


if __name__ == "__main__":
    unittest.main()
