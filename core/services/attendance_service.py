"""
Attendance Service
==================
Handles attendance record processing and calculations
"""

from datetime import datetime, time, timedelta
from sqlalchemy.orm import Session
from typing import Optional
from database_models import Employee, DailyRecord
from policy.hr_policy import HRPolicy, AttendanceStatus


class AttendanceService:
    """
    Service for processing attendance records
    """
    
    def __init__(self, db_session: Session):
        """Initialize attendance service"""
        self.session = db_session
    
    
    def process_attendance_record(
        self,
        employee_id: int,
        attendance_date: datetime.date,
        check_in: Optional[datetime.time],
        check_out: Optional[datetime.time]
    ) -> DailyRecord:
        """
        معالجة سجل حضور وإنشاء DailyRecord
        
        Args:
            employee_id: معرف الموظف
            attendance_date: تاريخ الحضور
            check_in: وقت الدخول
            check_out: وقت الخروج
            
        Returns:
            DailyRecord: السجل المنشأ أو المحدّث
        """
        # Get employee
        employee = self.session.query(Employee).filter_by(id=employee_id).first()
        if not employee:
            raise ValueError(f"Employee {employee_id} not found")
        
        # Check if record exists
        existing = self.session.query(DailyRecord).filter_by(
            employee_id=employee_id,
            date=attendance_date
        ).first()
        
        if existing:
            record = existing
        else:
            record = DailyRecord(
                employee_id=employee_id,
                date=attendance_date
            )
            self.session.add(record)
        
        # Update times
        record.check_in = check_in
        record.check_out = check_out
        
        # Calculate late minutes
        if check_in and employee.standard_start_time:
            record.late_minutes = self.calculate_late_minutes(check_in, employee.standard_start_time)
        else:
            record.late_minutes = 0
            
        # Calculate early leave minutes
        if check_out and employee.standard_end_time:
            record.early_leave_minutes = self.calculate_early_leave_minutes(check_out, employee.standard_end_time)
        else:
            record.early_leave_minutes = 0
        
        # Calculate overtime
        if check_out and employee.standard_end_time and employee.overtime_allowed:
            record.overtime_hours = self.calculate_overtime_hours(
                check_out,
                employee.standard_end_time,
                employee.overtime_allowed
            )
        else:
            record.overtime_hours = 0.0
        
        # Determine status
        record.status = self.determine_status(check_in, check_out)
        
        self.session.commit()
        return record
    
    
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
        allowed: bool
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
