"""
Attendance Service
==================
Handles attendance record processing and calculations
"""

from datetime import datetime, time
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from database_models import Employee, DailyRecord
from policy.hr_policy import HRPolicy, AttendanceStatus


class AttendanceService:
    """Service for processing attendance records"""

    def __init__(self, db_session: Session):
        """Initialize attendance service"""
        self.session = db_session

    def upsert_daily_record(
        self,
        employee_id: int,
        attendance_date: datetime.date,
        check_in: Optional[datetime.time],
        check_out: Optional[datetime.time],
        source: str = 'system',
        commit: bool = True,
    ) -> Tuple[Optional[DailyRecord], bool]:
        """Single write path for DailyRecord."""
        employee = self.session.query(Employee).filter_by(id=employee_id).first()
        if not employee:
            raise ValueError(f"Employee {employee_id} not found")

        source_key = (source or 'system').strip().lower()
        is_manual_source = source_key == 'manual'

        record = self.session.query(DailyRecord).filter_by(
            employee_id=employee_id,
            date=attendance_date,
        ).first()

        # Preserve manual edits from non-manual sources.
        if record and record.is_manual_override and not is_manual_source:
            return record, False

        # Clearing both times removes the record from payroll/work-day calculations.
        if not check_in and not check_out:
            if record:
                self.session.delete(record)
                if commit:
                    self.session.commit()
                return None, True
            return None, False

        if not record:
            record = DailyRecord(employee_id=employee_id, date=attendance_date)
            self.session.add(record)

        if is_manual_source:
            record.is_manual_override = True

        record.check_in = check_in
        record.check_out = check_out

        if check_in and employee.standard_start_time:
            record.late_minutes = self.calculate_late_minutes(check_in, employee.standard_start_time)
        else:
            record.late_minutes = 0

        if check_out and employee.standard_end_time:
            record.early_leave_minutes = self.calculate_early_leave_minutes(check_out, employee.standard_end_time)
        else:
            record.early_leave_minutes = 0

        if check_out and employee.standard_end_time and employee.overtime_allowed:
            record.overtime_hours = self.calculate_overtime_hours(
                check_out,
                employee.standard_end_time,
                employee.overtime_allowed,
            )
        else:
            record.overtime_hours = 0.0

        record.status = self.determine_status(check_in, check_out)

        if commit:
            self.session.commit()
        return record, True

    def process_attendance_record(
        self,
        employee_id: int,
        attendance_date: datetime.date,
        check_in: Optional[datetime.time],
        check_out: Optional[datetime.time],
        source: str = 'system',
        commit: bool = True,
    ) -> Optional[DailyRecord]:
        record, _ = self.upsert_daily_record(
            employee_id=employee_id,
            attendance_date=attendance_date,
            check_in=check_in,
            check_out=check_out,
            source=source,
            commit=commit,
        )
        return record

    def process_attendance_record_by_id(
        self,
        record_id: int,
        check_in: Optional[datetime.time],
        check_out: Optional[datetime.time],
        source: str = 'manual',
        commit: bool = True,
    ) -> Optional[DailyRecord]:
        record = self.session.query(DailyRecord).filter_by(id=record_id).first()
        if not record:
            raise ValueError(f"DailyRecord {record_id} not found")

        return self.process_attendance_record(
            employee_id=record.employee_id,
            attendance_date=record.date,
            check_in=check_in,
            check_out=check_out,
            source=source,
            commit=commit,
        )

    def calculate_late_minutes(self, check_in: time, standard_start: time) -> int:
        """
        حساب دقائق التأخير

        Args:
            check_in: وقت الدخول الفعلي
            standard_start: وقت الدخول المفترض

        Returns:
            int: عدد دقائق التأخير
        """
        # Convert to datetime for calculation
        today = datetime.today().date()
        actual = datetime.combine(today, check_in)
        expected = datetime.combine(today, standard_start)

        if actual > expected:
            diff = actual - expected
            return int(diff.total_seconds() / 60)
        return 0

    def calculate_early_leave_minutes(self, check_out: time, standard_end: time) -> int:
        """
        حساب دقائق الانصراف المبكر
        """
        today = datetime.today().date()
        actual = datetime.combine(today, check_out)
        expected = datetime.combine(today, standard_end)

        if actual < expected:
            diff = expected - actual
            return int(diff.total_seconds() / 60)
        return 0

    def calculate_overtime_hours(
        self,
        check_out: time,
        standard_end: time,
        allowed: bool,
    ) -> float:
        """
        حساب ساعات الإضافي

        Args:
            check_out: وقت الخروج الفعلي
            standard_end: وقت الخروج المفترض
            allowed: هل مسموح بالإضافي

        Returns:
            float: عدد ساعات الإضافي
        """
        if not allowed:
            return 0.0

        today = datetime.today().date()
        actual = datetime.combine(today, check_out)
        expected = datetime.combine(today, standard_end)

        if actual > expected:
            diff = actual - expected
            hours = diff.total_seconds() / 3600
            # الحساب فقط عند إكمال الحد الأدنى المسجل في الإعدادات (ساعة كاملة)
            if hours >= (HRPolicy.OVERTIME_MIN_MINUTES / 60.0):
                return hours

        return 0.0

    def determine_status(self, check_in: Optional[time], check_out: Optional[time]) -> str:
        """
        تحديد حالة الحضور

        Args:
            check_in: وقت الدخول
            check_out: وقت الخروج

        Returns:
            str: حالة الحضور
        """
        if not check_in and not check_out:
            return AttendanceStatus.ABSENT
        elif check_in and check_out:
            return AttendanceStatus.PRESENT
        elif check_in:
            return AttendanceStatus.LATE
        else:
            return AttendanceStatus.PRESENT
