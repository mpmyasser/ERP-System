"""
Permissions Service
===================
Handles employee permissions (تصاريح)
"""

from datetime import date
from sqlalchemy.orm import Session
from typing import List
from database_models import DailyRecord, Employee
from policy.hr_policy import HRPolicy


class PermissionsService:
    """
    Service for managing employee permissions
    """
    
    def __init__(self, db_session: Session):
        """Initialize permissions service"""
        self.session = db_session
    
    
    def add_permission(
        self,
        employee_id: int,
        permission_date: date,
        hours: float,
        reason: str = ""
    ):
        """
        إضافة تصريح
        
        Args:
            employee_id: معرف الموظف
            permission_date: تاريخ التصريح
            hours: عدد ساعات التصريح
            reason: سبب التصريح
        """
        # Get or create daily record
        record = self.session.query(DailyRecord).filter_by(
            employee_id=employee_id,
            date=permission_date
        ).first()
        
        if not record:
            record = DailyRecord(
                employee_id=employee_id,
                date=permission_date,
                status="تصريح"
            )
            self.session.add(record)
        
        # Store permission hours in manual_adjustment (negative value)
        record.manual_adjustment = -hours
        
        self.session.commit()
    
    
    def calculate_permission_deduction(self, hours: float, hourly_salary: float) -> float:
        """
        حساب خصم التصريح
        
        قاعدة: كل ساعة تصريح = خصم ساعة كاملة
        
        Args:
            hours: عدد ساعات التصريح
            hourly_salary: راتب الساعة
            
        Returns:
            float: قيمة الخصم
        """
        return hours * hourly_salary * HRPolicy.PERMISSION_DEDUCTION_RATE
    
    
    def get_monthly_permissions(self, employee_id: int, month: int, year: int) -> List[DailyRecord]:
        """
        الحصول على تصاريح الشهر
        
        Args:
            employee_id: معرف الموظف
            month: الشهر
            year: السنة
            
        Returns:
            list: قائمة بالتصاريح
        """
        records = self.session.query(DailyRecord).filter(
            DailyRecord.employee_id == employee_id,
            DailyRecord.status == "تصريح"
        ).all()
        
        return [r for r in records if r.date.month == month and r.date.year == year]
