# Automated unit conversion, input validation and batch-processing tests.
# Run from the project folder: python -m unittest discover -s tests -v

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from unit_converter import (CATEGORIES, convert_batch, convert_value,
                            format_number, formula_description, parse_measurement)


class UnitConverterTest(unittest.TestCase):
    def test_both_directions_of_four_required_categories(self):
        cases = [
            ("Length", "mm", "in", 25.4, 1),
            ("Length", "in", "mm", 1, 25.4),
            ("Temperature", "°C", "°F", 100, 212),
            ("Temperature", "°F", "°C", 32, 0),
            ("Mass", "kg", "lb", 0.45359237, 1),
            ("Mass", "lb", "kg", 1, 0.45359237),
            ("Speed", "km/h", "m/s", 36, 10),
            ("Speed", "m/s", "km/h", 10, 36),
        ]
        for category, source, destination, value, expected in cases:
            with self.subTest(category=category, direction=source):
                self.assertAlmostEqual(
                    convert_value(category, source, destination, value), expected,
                    places=8)

    def test_negative_temperature_below_freezing(self):
        self.assertAlmostEqual(convert_value("Temperature", "°C", "°F", -40), -40)
        self.assertAlmostEqual(convert_value("Temperature", "°F", "°C", -40), -40)

    def test_no_change_returns_same_value(self):
        for category, (unit, _) in CATEGORIES.items():
            self.assertEqual(convert_value(category, unit, unit, 1), 1)

    def test_round_trip_accuracy(self):
        for category, (first, second) in CATEGORIES.items():
            source_value = -15.2 if category == "Temperature" else 91.375
            output = convert_value(category, first, second, source_value)
            returned = convert_value(category, second, first, output)
            self.assertAlmostEqual(returned, source_value, places=9)

    def test_bad_input_handling(self):
        for text in ("", "ten", "nan", "inf"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_measurement(text, "Mass")
        with self.assertRaises(ValueError):
            parse_measurement("-1", "Speed")
        with self.assertRaises(ValueError):
            convert_value("Unknown", "kg", "lb", 1)
        with self.assertRaises(ValueError):
            convert_value("Mass", "kg", "mm", 1)
        with self.assertRaises(ValueError):
            convert_value("Length", "mm", "in", math.inf)

    def test_batch_safely_continues_after_bad_lines(self):
        batch = convert_batch("Speed", "km/h", "m/s", "36\ninvalid\n\n72\n-1")
        self.assertEqual(len(batch), 4)
        self.assertEqual([row[0] for row in batch], [1, 2, 4, 5])
        self.assertEqual([row[2] for row in batch], [10, None, 20, None])
        self.assertTrue(batch[1][3])
        with self.assertRaises(ValueError):
            convert_batch("Length", "mm", "in", "1\n" * 501)

    def test_precision_and_formula_explanation(self):
        self.assertEqual(format_number(25.4, 2), "25.40")
        self.assertIn("e", format_number(0.000000001, 2))
        self.assertIn("25.4", formula_description("Length", "in", "mm"))
        with self.assertRaises(ValueError):
            format_number(1.234, 3)


if __name__ == "__main__":
    unittest.main()
