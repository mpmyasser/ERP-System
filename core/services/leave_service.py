# -*- coding: utf-8 -*-
"""
Leave Service
=============
خدمة إدارة الإجازات
"""

from datetime import date
from sqlalchemy.orm import Session
from database_models import Employee, Leave, LeaveBalance, LeaveTypeEnum


class LeaveService:
    """خدمة إدارة الإجازات"""
    
    def __init__(self, db_session: Session):
        self.session = db_session
    
    def initialize_employee_balance(self, employee_id: int, year: int) -> LeaveBalance:
        """
        تهيئة رصيد الإجازات للموظف في سنة معينة
        
        Args:
            employee_id: معرف الموظف
            year: السنة المالية
            
        Returns:
            LeaveBalance: رصيد الإجازات
        """
        # التحقق من وجود رصيد مسبق
        existing = self.session.query(LeaveBalance).filter_by(
            employee_id=employee_id,
            year=year
        ).first()
        
        if existing:
            return existing
        
        # إنشاء رصيد جديد
        balance = LeaveBalance(
            employee_id=employee_id,
            year=year,
            annual_balance=21.0,   # 21 يوم إجازة سنوية
            annual_used=0.0,
            sick_balance=30.0,     # 30 يوم إجازة مرضية
            sick_used=0.0,
            casual_balance=7.0,    # 7 أيام إجازة عارضة
            casual_used=0.0,
            emergency_balance=3.0, # 3 أيام إجازة طارئة
            emergency_used=0.0
        )
        
        self.session.add(balance)
        return balance
    
    def initialize_all_balances(self, year: int) -> int:
        """
        تهيئة أرصدة الإجازات لجميع الموظفين النشطين
        
        Args:
            year: السنة المالية
            
        Returns:
            int: عدد الموظفين المُهيئين
        """
        employees = self.session.query(Employee).filter_by(is_active=True).all()
        count = 0
        
        for emp in employees:
            self.initialize_employee_balance(emp.id, year)
            count += 1
        
        return count
    
    def update_balance_after_leave(self, employee_id: int, leave: Leave) -> None:
        """
        تحديث رصيد الإجازات بعد إضافة إجازة
        
        Args:
            employee_id: معرف الموظف
            leave: الإجازة
        """
        # الحصول على السنة من تاريخ البداية
        year = leave.start_date.year
        
        # الحصول أو إنشاء الرصيد
        balance = self.initialize_employee_balance(employee_id, year)
        
        # تحديث الرصيد المستخدم حسب النوع
        if leave.leave_type == LeaveTypeEnum.ANNUAL.value:
            balance.annual_used += leave.days_count
        elif leave.leave_type == LeaveTypeEnum.SICK.value:
            balance.sick_used += leave.days_count
        elif leave.leave_type == LeaveTypeEnum.CASUAL.value:
            balance.casual_used += leave.days_count
        elif leave.leave_type == LeaveTypeEnum.EMERGENCY.value:
            balance.emergency_used += leave.days_count
        
        self.session.flush()
    
    def restore_balance_after_delete(self, leave: Leave) -> None:
        """
        استرجاع رصيد الإجازات بعد حذف إجازة
        
        Args:
            leave: الإجازة المحذوفة
        """
        year = leave.start_date.year
        
        balance = self.session.query(LeaveBalance).filter_by(
            employee_id=leave.employee_id,
            year=year
        ).first()
        
        if not balance:
            return
        
        # استرجاع الأيام
        if leave.leave_type == LeaveTypeEnum.ANNUAL.value:
            balance.annual_used = max(0, balance.annual_used - leave.days_count)
        elif leave.leave_type == LeaveTypeEnum.SICK.value:
            balance.sick_used = max(0, balance.sick_used - leave.days_count)
        elif leave.leave_type == LeaveTypeEnum.CASUAL.value:
            balance.casual_used = max(0, balance.casual_used - leave.days_count)
        elif leave.leave_type == LeaveTypeEnum.EMERGENCY.value:
            balance.emergency_used = max(0, balance.emergency_used - leave.days_count)
        
        self.session.flush()
    
    def check_leave_availability(self, employee_id: int, leave_type: str, 
                                 days: float, year: int) -> tuple[bool, str]:
        """
        التحقق من توفر رصيد كافٍ للإجازة
        
        Args:
            employee_id: معرف الموظف
            leave_type: نوع الإجازة
            days: عدد الأيام المطلوبة
            year: السنة
            
        Returns:
            tuple: (متوفر؟، رسالة)
        """
        balance = self.session.query(LeaveBalance).filter_by(
            employee_id=employee_id,
            year=year
        ).first()
        
        if not balance:
            balance = self.initialize_employee_balance(employee_id, year)
        
        # التحقق حسب النوع
        if leave_type == LeaveTypeEnum.ANNUAL.value:
            remaining = balance.annual_remaining
            if days > remaining:
                return False, f"الرصيد المتبقي: {remaining} يوم فقط"
        elif leave_type == LeaveTypeEnum.SICK.value:
            remaining = balance.sick_remaining
            if days > remaining:
                return False, f"الرصيد المتبقي: {remaining} يوم فقط"
        elif leave_type == LeaveTypeEnum.CASUAL.value:
            remaining = balance.casual_remaining
            if days > remaining:
                return False, f"الرصيد المتبقي: {remaining} يوم فقط"
        elif leave_type == LeaveTypeEnum.EMERGENCY.value:
            remaining = balance.emergency_remaining
            if days > remaining:
                return False, f"الرصيد المتبقي: {remaining} يوم فقط"
        elif leave_type == LeaveTypeEnum.UNPAID.value:
            # إجازات بدون راتب دائماً متاحة
            pass
        
        return True, "الرصيد متاح"
    
    def get_employee_leave_summary(self, employee_id: int, year: int) -> dict:
        """
        الحصول على ملخص إجازات الموظف
        
        Args:
            employee_id: معرف الموظف
            year: السنة
            
        Returns:
            dict: ملخص الإجازات
        """
        balance = self.session.query(LeaveBalance).filter_by(
            employee_id=employee_id,
            year=year
        ).first()
        
        if not balance:
            balance = self.initialize_employee_balance(employee_id, year)
        
        leaves = self.session.query(Leave).filter(
            Leave.employee_id == employee_id,
            Leave.start_date >= date(year, 1, 1),
            Leave.start_date <= date(year, 12, 31)
        ).all()
        
        return {
            'balance': balance,
            'leaves': leaves,
            'total_days_taken': sum(l.days_count for l in leaves),
            'annual_remaining': balance.annual_remaining,
            'sick_remaining': balance.sick_remaining,
            'casual_remaining': balance.casual_remaining,
            'emergency_remaining': balance.emergency_remaining
        }
    
    def calculate_working_days(self, start_date: date, end_date: date,
                              exclude_fridays: bool = True) -> int:
        """
        حساب أيام العمل الفعلية (بدون عطلات نهاية الأسبوع)
        
        Args:
            start_date: تاريخ البداية
            end_date: تاريخ النهاية
            exclude_fridays: استبعاد الجمعة؟
            
        Returns:
            int: عدد أيام العمل
        """
        from datetime import timedelta
        
        total_days = (end_date - start_date).days + 1
        working_days = 0
        
        current = start_date
        while current <= end_date:
            # استبعاد الجمعة (weekday = 4)
            if exclude_fridays and current.weekday() == 4:
                pass
            else:
                working_days += 1
            current += timedelta(days=1)
        
        return working_days
