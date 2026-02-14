from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date, Boolean, Text
from sqlalchemy.orm import relationship
from core.database_models import Base
from datetime import datetime

class CashAccount(Base):
    """
    الخزائن (الرئيسية، فرعية، عهدة)
    """
    __tablename__ = 'cash_accounts'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False) # الربط بشجرة الحسابات
    type = Column(String(20), default='General') # General (عمومية), Subsidiary (فرعية)
    parent_cash_id = Column(Integer, ForeignKey('cash_accounts.id'), nullable=True) # ربط الخزينة الفرعية بالعمومية
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True) # المستخدم المسؤول عن الخزينة
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    
    account = relationship('Account', foreign_keys=[account_id])
    parent = relationship('CashAccount', remote_side=[id], backref='subsidiaries')
    
    def is_general(self):
        """تحديد ما إذا كانت الخزينة عمومية (بدون أم)"""
        return self.parent_cash_id is None
    
    def is_subsidiary(self):
        """تحديد ما إذا كانت الخزينة فرعية (لديها أم)"""
        return self.parent_cash_id is not None
    
    def get_account_type_label(self):
        """الحصول على تسمية نوع الخزينة بالعربية"""
        return 'عمومية' if self.is_general() else 'فرعية'

class BankAccount(Base):
    """
    حسابات البنوك
    """
    __tablename__ = 'bank_accounts'
    
    id = Column(Integer, primary_key=True)
    bank_name = Column(String(100), nullable=False)
    account_number = Column(String(50), nullable=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False) # الربط بشجرة الحسابات
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    
    account = relationship('Account')

class CheckRecord(Base):
    """
    سجل الشيكات (أوراق القبض والدفع)
    """
    __tablename__ = 'check_records'
    
    id = Column(Integer, primary_key=True)
    type = Column(String(20), nullable=False) # Receivable (قابض) / Payable (دفع)
    check_number = Column(String(50), nullable=False)
    bank_name = Column(String(100), nullable=True)
    drawer_name = Column(String(100), nullable=True) # اسم الساحب
    
    amount = Column(Float, nullable=False)
    issue_date = Column(Date, default=datetime.now)
    due_date = Column(Date, nullable=False)
    
    status = Column(String(20), default='Pending') # Pending, Collected, Bounced, Cancelled
    
    notes = Column(Text, nullable=True)
    
    # الربط بالمحاسبة
    journal_entry_id = Column(Integer, ForeignKey('journal_entries.id'), nullable=True)
    
    entry = relationship('JournalEntry')

class CashTransfer(Base):
    """
    تحويلات الخزائن
    """
    __tablename__ = 'cash_transfers'
    
    id = Column(Integer, primary_key=True)
    from_cash_id = Column(Integer, ForeignKey('cash_accounts.id'), nullable=False)
    to_cash_id = Column(Integer, ForeignKey('cash_accounts.id'), nullable=False)
    amount = Column(Float, nullable=False)
    transfer_date = Column(Date, nullable=False)
    description = Column(String(200), nullable=True)
    
    status = Column(String(20), default='Pending') # Pending, Received, Cancelled
    
    # الربط بالمحاسبة
    journal_entry_id = Column(Integer, ForeignKey('journal_entries.id'), nullable=True)
    
    received_date = Column(Date, nullable=True)
    received_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    from_cash = relationship('CashAccount', foreign_keys=[from_cash_id])
    to_cash = relationship('CashAccount', foreign_keys=[to_cash_id])
    entry = relationship('JournalEntry')

from core.accounting_models import Account