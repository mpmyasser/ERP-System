"""
Loans Service
=============
Handles employee loans (سلف) management
"""

from datetime import date
from sqlalchemy.orm import Session
from typing import List
from database_models import Loan, Employee
from policy.hr_policy import LoanType, HRPolicy


class LoansService:
    """
    Service for managing employee loans
    """
    
    def __init__(self, db_session: Session):
        """Initialize loans service"""
        self.session = db_session
    
    
    def calculate_monthly_installment(self, employee_id: int, month: int, year: int) -> float:
        """
        حساب قسط السلف الشهري
        
        Args:
            employee_id: معرف الموظف
            month: الشهر
            year: السنة
            
        Returns:
            float: قيمة القسط المستحق
        """
        active_loans = self.get_active_loans(employee_id)
        
        total_installment = 0.0
        for loan in active_loans:
            if loan.installments_remaining and loan.installments_remaining > 0:
                total_installment += loan.monthly_installment
        
        return total_installment
    
    
    def get_active_loans(self, employee_id: int) -> List[Loan]:
        """
        الحصول على السلف النشطة
        
        Args:
            employee_id: معرف الموظف
            
        Returns:
            list: قائمة السلف النشطة
        """
        return self.session.query(Loan).filter_by(
            employee_id=employee_id,
            is_paid_off=False
        ).all()
    
    
    def get_remaining_balance(self, loan_id: int) -> float:
        """
        حساب المتبقي من السلفة
        
        Args:
            loan_id: معرف السلفة
            
        Returns:
            float: المبلغ المتبقي
        """
        loan = self.session.query(Loan).filter_by(id=loan_id).first()
        if not loan:
            return 0.0
        
        if loan.is_paid_off:
            return 0.0
        
        if loan.installments_remaining and loan.monthly_installment:
            return loan.installments_remaining * loan.monthly_installment
        
        return loan.total_amount - loan.paid_amount if loan.paid_amount else loan.total_amount
    
    
    def deduct_installment(self, loan_id: int):
        """
        خصم قسط من السلفة
        
        Args:
            loan_id: معرف السلفة
        """
        loan = self.session.query(Loan).filter_by(id=loan_id).first()
        if not loan or loan.is_paid_off:
            return
        
        if loan.installments_remaining and loan.installments_remaining > 0:
            loan.installments_remaining -= 1
            
            if loan.paid_amount:
                loan.paid_amount += loan.monthly_installment
            else:
                loan.paid_amount = loan.monthly_installment
            
            if loan.installments_remaining == 0:
                loan.is_paid_off = True
            
            self.session.commit()
