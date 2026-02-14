#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
فحص قيم السلف - المقارنة بين remaining_balance و auto_remaining_balance
"""

import sys
import os
from pathlib import Path

# إضافة المسار الصحيح
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'core'))

# استيراد المكتبات
from db_manager import DBManager

def main():
    db = DBManager()
    session = db.get_session()
    
    try:
        # احصل على جميع السلف
        loans = db.get_all_loans()
        
        print("\n" + "=" * 90)
        print("🔍 فحص قيم السلف - المقارنة بين remaining_balance و auto_remaining_balance")
        print("=" * 90)
        
        if not loans:
            print("❌ لا توجد سلف في قاعدة البيانات")
            return
        
        for loan in loans:
            if loan.employee:
                old_value = loan.remaining_balance
                new_value = loan.auto_remaining_balance
                difference = old_value - new_value
                
                print(f"\n📊 السلفة #{loan.id}")
                print(f"   الموظف: {loan.employee.name} ({loan.employee.code})")
                print(f"   النوع: {loan.type}")
                print(f"   المبلغ الأصلي: {loan.amount:,.2f}")
                print(f"   تاريخ الصرف: {loan.date}")
                print(f"   عدد الأقساط: {loan.installments_count}")
                print(f"   القسط الشهري: {loan.monthly_installment:,.2f}")
                print(f"   ")
                print(f"   ❌ القيمة القديمة (remaining_balance): {old_value:,.2f}")
                print(f"   ✅ القيمة الصحيحة (auto_remaining_balance): {new_value:,.2f}")
                print(f"   الفرق: {difference:,.2f}")
                
                if difference != 0:
                    print(f"   ⚠️  تنبيه: هناك فرق بين القيمتين!")
        
        print("\n" + "=" * 90 + "\n")
        
    finally:
        session.close()

if __name__ == '__main__':
    main()
