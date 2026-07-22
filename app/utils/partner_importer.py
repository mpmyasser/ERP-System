from core.commercial_models import Partner
from core.accounting_models import Account
from typing import Tuple
from app.utils.import_helpers import load_excel, clean_str, handle_import_error

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
        df, error = load_excel(file_path, ['name', 'type'])
        if error:
            return False, error
        assert df is not None

        existing_partners = {p.name: p for p in db_session.query(Partner).all()}
        
        for index, row in df.iterrows():
            name = clean_str(row['name'])
            if not name:
                continue
                
            p_type = clean_str(row['type'])
            phone = clean_str(row.get('phone', ''))
            address = clean_str(row.get('address', ''))
            tax_id = clean_str(row.get('tax_id', ''))
            account_code = clean_str(row.get('account_code', ''))
            
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
        return False, handle_import_error(db_session, e)
