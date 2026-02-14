"""
قائمة التغييرات التي تم تطبيقها على نموذج Database Models
لإضافة جدول تسجيل سجل تاريخي لتعديلات الرواتب
"""

# أضف هذا النموذج إلى نهاية ملف core/database_models.py

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

class SalaryHistory(Base):
    """
    نموذج لتسجيل السجل التاريخي لتعديلات رواتب الموظفين
    يحفظ كل تعديل على الراتب مع التاريخ والقيمة القديمة والجديدة والسبب
    """
    __tablename__ = 'salary_history'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    
    # الراتب القديم والجديد
    old_salary = Column(Float, nullable=False)
    new_salary = Column(Float, nullable=False)
    
    # الفرق (التعديل)
    salary_change = Column(Float, nullable=False)
    
    # تاريخ التعديل
    change_date = Column(DateTime, default=datetime.now, nullable=False)
    
    # سبب التعديل (ترقية، تخفيض، تصحيح، إلخ)
    reason = Column(String(255), nullable=True)
    
    # معلومات إضافية
    notes = Column(Text, nullable=True)
    
    # من قام بالتعديل (اسم المستخدم)
    modified_by = Column(String(100), nullable=True)
    
    # العلاقة مع الموظف
    employee = relationship('Employee', back_populates='salary_history')
    
    def __repr__(self):
        return f"<SalaryHistory {self.id} - Employee: {self.employee_id} - Change: {self.salary_change} - Date: {self.change_date}>"
    
    @property
    def formatted_change_date(self):
        """تنسيق التاريخ بالعربية"""
        if self.change_date:
            return self.change_date.strftime('%d/%m/%Y %H:%M')
        return '-'
    
    @property
    def change_type(self):
        """نوع التعديل (زيادة أو تخفيض)"""
        if self.salary_change > 0:
            return 'زيادة'
        elif self.salary_change < 0:
            return 'تخفيض'
        else:
            return 'بدون تغيير'


# تأكد من إضافة العلاقة إلى نموذج Employee:
# salary_history = relationship('SalaryHistory', back_populates='employee', cascade='all, delete-orphan')
