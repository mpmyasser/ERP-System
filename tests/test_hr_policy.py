"""
Unit tests for :mod:`core.policy.hr_policy`.

``HRPolicy`` reads its tunable constants from the database through a metaclass,
but ``_get_setting_meta`` falls back to hard-coded defaults whenever there is no
Flask application context.  These tests run outside any app context, so the
documented defaults are in effect and the payroll calculation helpers can be
verified deterministically.
"""

import os
import sys
import unittest
from datetime import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.policy.hr_policy import HRPolicy, LoanType, AttendanceStatus


class PolicyDefaultsTests(unittest.TestCase):
    """The metaclass properties must yield the documented defaults off-app."""

    def test_numeric_defaults(self):
        self.assertEqual(HRPolicy.WORKING_DAYS_PER_MONTH, 26)
        self.assertEqual(HRPolicy.LATE_GRACE_PERIOD_MINUTES, 10)
        self.assertEqual(HRPolicy.LATE_MULTIPLIER, 1.0)
        self.assertEqual(HRPolicy.ABSENCE_GRACE_DAYS, 2)
        self.assertEqual(HRPolicy.ABSENCE_PENALTY_DAYS, 0.25)
        self.assertEqual(HRPolicy.OVERTIME_MIN_MINUTES, 60)
        self.assertEqual(HRPolicy.OVERTIME_RATE, 1.5)
        self.assertEqual(HRPolicy.INCENTIVE_FULL_THRESHOLD, 24)
        self.assertEqual(HRPolicy.INCENTIVE_HALF_THRESHOLD, 15)

    def test_boolean_default(self):
        self.assertIs(HRPolicy.OVERTIME_FIRST_HOUR_FIXED, True)

    def test_string_default(self):
        self.assertEqual(HRPolicy.OVERTIME_ROUNDING_MODE, "HALF_HOUR")

    def test_static_constants(self):
        self.assertEqual(HRPolicy.WEEKLY_HOLIDAY, "الأحد")
        self.assertEqual(HRPolicy.DEFAULT_START_TIME, time(8, 0))
        self.assertEqual(HRPolicy.DEFAULT_END_TIME, time(16, 0))
        self.assertEqual(HRPolicy.DEFAULT_WORK_HOURS, 8.0)


class SalaryCalculationTests(unittest.TestCase):
    def test_daily_salary(self):
        self.assertEqual(HRPolicy.calculate_daily_salary(2600), 100.0)

    def test_hourly_salary_default_hours(self):
        self.assertEqual(HRPolicy.calculate_hourly_salary(2600), 12.5)

    def test_hourly_salary_custom_hours(self):
        self.assertEqual(HRPolicy.calculate_hourly_salary(2600, daily_hours=10), 10.0)


class LateDeductionTests(unittest.TestCase):
    def test_within_grace_no_deduction(self):
        self.assertEqual(HRPolicy.calculate_late_deduction(10, 12.5), 0.0)

    def test_beyond_grace(self):
        # 70 min late, 10 min grace -> 60 extra min * 1.0 / 60 * 12 = 12.
        self.assertEqual(HRPolicy.calculate_late_deduction(70, 12.0), 12.0)


class EarlyDepartureDeductionTests(unittest.TestCase):
    def test_within_grace_no_deduction(self):
        # Default early-departure grace is 0, so 0 minutes deducts nothing.
        self.assertEqual(HRPolicy.calculate_early_departure_deduction(0, 12.0), 0.0)

    def test_beyond_grace(self):
        # 30 early min * 1.0 / 60 * 12 = 6.
        self.assertEqual(HRPolicy.calculate_early_departure_deduction(30, 12.0), 6.0)


class AbsencePenaltyTests(unittest.TestCase):
    def test_within_grace(self):
        self.assertEqual(HRPolicy.calculate_absence_penalty(2), 0.0)

    def test_beyond_grace(self):
        # (4 - 2) * 0.25 = 0.5.
        self.assertEqual(HRPolicy.calculate_absence_penalty(4), 0.5)


class IncentiveTests(unittest.TestCase):
    def test_full_incentive(self):
        self.assertEqual(HRPolicy.calculate_incentive_amount(24, 200), 200)

    def test_half_incentive(self):
        self.assertEqual(HRPolicy.calculate_incentive_amount(15, 200), 100.0)

    def test_no_incentive(self):
        self.assertEqual(HRPolicy.calculate_incentive_amount(14, 200), 0.0)


class OvertimeRoundingTests(unittest.TestCase):
    def test_below_minimum_gate(self):
        self.assertEqual(HRPolicy.calculate_overtime_hours_rounded(0.5), 0.0)

    def test_exactly_one_hour(self):
        self.assertEqual(HRPolicy.calculate_overtime_hours_rounded(1.0), 1.0)

    def test_remainder_below_threshold_rounds_down(self):
        # 1h24m -> first hour fixed + 24 remaining (< 30) -> 1.0.
        self.assertEqual(HRPolicy.calculate_overtime_hours_rounded(1.4), 1.0)

    def test_remainder_at_threshold_gives_half(self):
        # 1h30m -> remaining == 30 -> +0.5 -> 1.5.
        self.assertEqual(HRPolicy.calculate_overtime_hours_rounded(1.5), 1.5)

    def test_remainder_above_threshold_rounds_up(self):
        # 1h45m -> remaining 45 (> 30) -> +1.0 -> 2.0.
        self.assertEqual(HRPolicy.calculate_overtime_hours_rounded(1.75), 2.0)


class OvertimePayTests(unittest.TestCase):
    def test_no_pay_below_gate(self):
        self.assertEqual(HRPolicy.calculate_overtime_pay(0.5, 10.0), 0.0)

    def test_pay_uses_rounded_hours_and_rate(self):
        # 2h -> rounded 2.0; 2.0 * 10 * 1.5 = 30.
        self.assertEqual(HRPolicy.calculate_overtime_pay(2.0, 10.0), 30.0)


class EnumLikeConstantsTests(unittest.TestCase):
    def test_loan_types(self):
        self.assertEqual(LoanType.MONTHLY, "شهرية")
        self.assertEqual(LoanType.EXTENDED, "ممتدة")
        self.assertEqual(LoanType.EMERGENCY, "طارئة")

    def test_attendance_statuses(self):
        self.assertEqual(AttendanceStatus.PRESENT, "حاضر")
        self.assertEqual(AttendanceStatus.ABSENT, "غائب")
        self.assertEqual(AttendanceStatus.LATE, "متأخر")
        self.assertEqual(AttendanceStatus.PERMISSION, "تصريح")
        self.assertEqual(AttendanceStatus.HOLIDAY, "عطلة")


if __name__ == "__main__":
    unittest.main()
