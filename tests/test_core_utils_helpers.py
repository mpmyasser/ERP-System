"""
Unit tests for :mod:`core.utils.helpers`.

Covers currency/date formatting, unit conversions, the flexible date parser
(``parse_date_compact``) and the national-ID helpers.  All functions are pure,
so no database or Flask context is required.
"""

import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.utils import helpers


class FormatCurrencyTests(unittest.TestCase):
    def test_default_currency_and_thousands_separator(self):
        self.assertEqual(helpers.format_currency(1234.5), "1,234.50 جنيه")

    def test_custom_currency(self):
        self.assertEqual(helpers.format_currency(10, "USD"), "10.00 USD")

    def test_zero(self):
        self.assertEqual(helpers.format_currency(0), "0.00 جنيه")


class FormatDateArTests(unittest.TestCase):
    def test_none_returns_empty(self):
        self.assertEqual(helpers.format_date_ar(None), "")

    def test_string_passthrough(self):
        self.assertEqual(helpers.format_date_ar("2025-01-01"), "2025-01-01")

    def test_date_object_formatted_dd_mm_yyyy(self):
        self.assertEqual(helpers.format_date_ar(date(2025, 3, 9)), "09/03/2025")


class CalculateAgeTests(unittest.TestCase):
    def test_none_returns_none(self):
        self.assertIsNone(helpers.calculate_age(None))

    def test_birthday_not_yet_reached_this_year(self):
        today = date.today()
        # Birthday tomorrow-ish: set to a future month if possible.
        future_month = 12 if today.month < 12 else 1
        birth = date(today.year - 30, future_month, 28)
        expected = 29 if future_month > today.month else 30
        # Guard: only assert the "not reached" case when it truly is in the future.
        if future_month > today.month:
            self.assertEqual(helpers.calculate_age(birth), expected)

    def test_birthday_already_passed(self):
        today = date.today()
        birth = date(today.year - 25, 1, 1)
        # Jan 1 has passed for any date after Jan 1.
        expected = 25 if today > date(today.year, 1, 1) else 24
        self.assertEqual(helpers.calculate_age(birth), expected)


class UnitConversionTests(unittest.TestCase):
    def test_minutes_to_hours(self):
        self.assertEqual(helpers.minutes_to_hours(90), 1.5)

    def test_hours_to_minutes(self):
        self.assertEqual(helpers.hours_to_minutes(2), 120)

    def test_roundtrip(self):
        self.assertAlmostEqual(helpers.minutes_to_hours(helpers.hours_to_minutes(3)), 3.0)


class ParseDateCompactTests(unittest.TestCase):
    def test_iso_format(self):
        self.assertEqual(helpers.parse_date_compact("2025-12-08"), date(2025, 12, 8))

    def test_dash_dd_mm_yyyy(self):
        self.assertEqual(helpers.parse_date_compact("08-12-2025"), date(2025, 12, 8))

    def test_slash_dd_mm_yyyy(self):
        self.assertEqual(helpers.parse_date_compact("08/12/2025"), date(2025, 12, 8))

    def test_compact_ddmmyyyy(self):
        self.assertEqual(helpers.parse_date_compact("08122025"), date(2025, 12, 8))

    def test_arabic_numerals(self):
        self.assertEqual(helpers.parse_date_compact("٠٨/١٢/٢٠٢٥"), date(2025, 12, 8))

    def test_empty_and_none(self):
        self.assertIsNone(helpers.parse_date_compact(""))
        self.assertIsNone(helpers.parse_date_compact(None))

    def test_out_of_range_returns_none(self):
        self.assertIsNone(helpers.parse_date_compact("32/12/2025"))  # day
        self.assertIsNone(helpers.parse_date_compact("08/13/2025"))  # month
        self.assertIsNone(helpers.parse_date_compact("08/12/1800"))  # year

    def test_wrong_slash_part_count_returns_none(self):
        self.assertIsNone(helpers.parse_date_compact("08/12"))

    def test_wrong_compact_length_returns_none(self):
        self.assertIsNone(helpers.parse_date_compact("0812025"))  # 7 digits


class ValidateDateFormatTests(unittest.TestCase):
    def test_valid(self):
        self.assertTrue(helpers.validate_date_format("08/12/2025"))

    def test_invalid(self):
        self.assertFalse(helpers.validate_date_format("not a date"))


class FormatDateInputHintTests(unittest.TestCase):
    def test_returns_non_empty_string(self):
        hint = helpers.format_date_input_hint()
        self.assertIsInstance(hint, str)
        self.assertIn("DDMMYYYY", hint)


class NationalIdHelpersTests(unittest.TestCase):
    VALID_ID = "28104111401638"

    def test_extract_birthdate_returns_date(self):
        self.assertEqual(
            helpers.extract_birthdate_from_national_id(self.VALID_ID),
            date(1981, 4, 11),
        )

    def test_extract_birthdate_2000s(self):
        self.assertEqual(
            helpers.extract_birthdate_from_national_id("30001011234567"),
            date(2000, 1, 1),
        )

    def test_extract_birthdate_invalid_inputs(self):
        self.assertIsNone(helpers.extract_birthdate_from_national_id(""))
        self.assertIsNone(helpers.extract_birthdate_from_national_id(None))
        self.assertIsNone(helpers.extract_birthdate_from_national_id("123"))
        self.assertIsNone(helpers.extract_birthdate_from_national_id("18104111401638"))
        self.assertIsNone(helpers.extract_birthdate_from_national_id("28102301401638"))

    def test_calculate_age_invalid_returns_none(self):
        self.assertIsNone(helpers.calculate_age_from_national_id("bad"))

    def test_calculate_age_structure(self):
        age = helpers.calculate_age_from_national_id(self.VALID_ID)
        self.assertIsNotNone(age)
        self.assertEqual(set(age.keys()), {"years", "months", "days", "total_days"})
        self.assertEqual(
            age["total_days"], (date.today() - date(1981, 4, 11)).days
        )


if __name__ == "__main__":
    unittest.main()
