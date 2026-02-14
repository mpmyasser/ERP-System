# -*- coding: utf-8 -*-
"""
تحديث قاعدة البيانات لإضافة جداول الإجازات
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from sqlalchemy import create_engine
from database_models import Base, LeaveBalance, Leave
from db_manager import DBManager

def update_database():
    """إضافة جداول الإجازات"""
    print("=" * 60)
    print("تحديث قاعدة البيانات - إضافة نظام الإجازات")
    print("=" * 60)
    
    db = DBManager()
    engine = create_engine(f'sqlite:///{db.db_path}')
    
    # إنشاء الجداول الجديدة فقط
    print("\n>> انشاء جداول الاجازات...")
    Base.metadata.create_all(engine, tables=[
        LeaveBalance.__table__,
        Leave.__table__
    ])
    
    print(">> تم انشاء الجداول بنجاح:")
    print("   - leave_balances (ارصدة الاجازات)")
    print("   - leaves (سجل الاجازات)")
    
    print("\n" + "=" * 60)
    print(">> اكتمل التحديث بنجاح!")
    print("=" * 60)
    print("\n>> الخطوات التالية:")
    print("   1. شغل البرنامج: python run.py")
    print("   2. اذهب إلى: http://localhost:5000/leaves/balances")
    print("   3. اضغط 'تهيئة الأرصدة' لإنشاء أرصدة جميع الموظفين")
    print("   4. اذهب إلى: http://localhost:5000/leaves/bulk")
    print("   5. أدخل الإجازات جماعياً")
    print("=" * 60)

if __name__ == '__main__':
    update_database()
