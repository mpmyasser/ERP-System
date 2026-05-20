import pandas as pd
from core.commercial_models import Partner
from core.accounting_models import Account
from typing import Tuple
import traceback

def import_partners_from_excel(db_session, file_path: str) -> Tuple[bool, str]:
    """
    Imports Partners (Customers, Suppliers, Factories, Dyeing Houses) from an Excel file.
    Expected Columns:
    - name (String)
    - type (Customer, Supplier, Dyeing, Printing, Factory, Both)
    - phone (String, optional)
    - address (String, optional)
    - tax_id (String, optional)
    - account_code (String, optional) - To link to an existing accounting tree code
    """
    try:
        df = pd.read_excel(file_path)
        
        # Validate columns
        required_cols = ['name', 'type']
        for col in required_cols:
            if col not in df.columns:
                return False, f"العمود المطلوب غير موجود: {col}"
                
        existing_partners = {p.name: p for p in db_session.query(Partner).all()}
        
        for index, row in df.iterrows():
            name = str(row['name']).strip()
            if not name or name == 'nan':
                continue
                
            p_type = str(row['type']).strip()
            phone = str(row.get('phone', '')).strip()
            if phone == 'nan': phone = ''
            
            address = str(row.get('address', '')).strip()
            if address == 'nan': address = ''
            
            tax_id = str(row.get('tax_id', '')).strip()
            if tax_id == 'nan': tax_id = ''
            
            account_code = str(row.get('account_code', '')).strip()
            if account_code == 'nan': account_code = ''
            
            account_id = None
            if account_code:
                acc = db_session.query(Account).filter_by(code=account_code).first()
                if acc:
                    account_id = acc.id
            
            if name in existing_partners:
                partner = existing_partners[name]
                partner.type = p_type
                partner.phone = phone
                partner.address = address
                partner.tax_id = tax_id
                if account_id:
                    partner.account_id = account_id
            else:
                partner = Partner(
                    name=name,
                    type=p_type,
                    phone=phone,
                    address=address,
                    tax_id=tax_id,
                    account_id=account_id
                )
                db_session.add(partner)
                
        db_session.commit()
        return True, "تم استيراد بيانات الشركاء بنجاح"
        
    except Exception as e:
        db_session.rollback()
        error_msg = f"خطأ أثناء الاستيراد: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return False, str(e)
