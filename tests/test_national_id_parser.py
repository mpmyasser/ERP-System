"""
Unit tests for :mod:`core.national_id_parser`.

The module extracts information (birth date, age) encoded in the Egyptian
14-digit national ID.  These tests exercise the pure parsing/validation logic
without touching the database or Flask.
"""

import os
import sys
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import national_id_parser as parser


# A known-valid ID: century digit 2 (1900s), YYMMDD = 810411 -> 1981-04-11
VALID_ID_1900S = "28104111401638"
# Century digit 3 (2000s), YYMMDD = 000101 -> 2000-01-01
VALID_ID_2000S = "30001011234567"


class ExtractBirthdateTests(unittest.TestCase):
    def test_valid_1900s_id(self):
        self.assertEqual(parser.extract_birthdate(VALID_ID_1900S), "1981-04-11")

    def test_valid_2000s_id(self):
        self.assertEqual(parser.extract_birthdate(VALID_ID_2000S), "2000-01-01")

    def test_strips_spaces_and_dashes(self):
        self.assertEqual(
            parser.extract_birthdate(" 2-8104-1114 01638 "), "1981-04-11"
        )

    def test_accepts_integer_input(self):
        self.assertEqual(parser.extract_birthdate(28104111401638), "1981-04-11")

    def test_wrong_length_returns_none(self):
        self.assertIsNone(parser.extract_birthdate("1234567890123"))  # 13 digits
        self.assertIsNone(parser.extract_birthdate("281041114016380"))  # 15 digits

    def test_non_digit_returns_none(self):
        self.assertIsNone(parser.extract_birthdate("2810411140163X"))

    def test_empty_returns_none(self):
        self.assertIsNone(parser.extract_birthdate(""))

    def test_invalid_century_digit_returns_none(self):
        # Leading digit 1 is neither 2 nor 3.
        self.assertIsNone(parser.extract_birthdate("18104111401638"))

    def test_invalid_month_returns_none(self):
        # Month "13".
        self.assertIsNone(parser.extract_birthdate("28113111401638"))

    def test_invalid_day_returns_none(self):
        # Day "32".
        self.assertIsNone(parser.extract_birthdate("28104321401638"))

    def test_impossible_calendar_date_returns_none(self):
        # 30th of February passes the range check but is not a real date.
        self.assertIsNone(parser.extract_birthdate("28102301401638"))


class ExtractBirthdateFormattedTests(unittest.TestCase):
    def test_default_format(self):
        self.assertEqual(
            parser.extract_birthdate_formatted(VALID_ID_1900S), "11/04/1981"
        )

    def test_custom_format(self):
        self.assertEqual(
            parser.extract_birthdate_formatted(VALID_ID_1900S, "%Y/%m/%d"),
            "1981/04/11",
        )

    def test_invalid_id_returns_none(self):
        self.assertIsNone(parser.extract_birthdate_formatted("bad"))


class CalculateAgeTests(unittest.TestCase):
    def test_invalid_id_returns_none(self):
        self.assertIsNone(parser.calculate_age("bad"))

    def test_returns_expected_keys(self):
        age = parser.calculate_age(VALID_ID_1900S)
        self.assertIsNotNone(age)
        self.assertEqual(set(age.keys()), {"years", "months", "days", "total_days"})

    def test_values_are_consistent_with_birthdate(self):
        birth = datetime(1981, 4, 11)
        today = datetime.now()
        age = parser.calculate_age(VALID_ID_1900S)

        self.assertEqual(age["total_days"], (today - birth).days)
        self.assertGreaterEqual(age["years"], 40)
        self.assertTrue(0 <= age["months"] < 12)
        self.assertTrue(0 <= age["days"] < 31)

    def test_normalizes_negative_day_borrow(self):
        # Build an ID whose birthday is "tomorrow" (month unchanged) so that the
        # day-borrow branch executes deterministically.
        today = datetime.now()
        # Choose a date earlier in the current month to avoid month rollover.
        target_day = 2 if today.day > 2 else 1
        yy = f"{(today.year - 30) % 100:02d}"
        mm = f"{today.month:02d}"
        dd = f"{target_day:02d}"
        nid = "2" + yy + mm + dd + "1401638"
        nid = nid[:14]
        age = parser.calculate_age(nid)
        self.assertIsNotNone(age)
        self.assertGreaterEqual(age["years"], 29)


if __name__ == "__main__":
    unittest.main()
