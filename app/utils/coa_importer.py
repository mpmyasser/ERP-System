from core.accounting_models import Account, AccountType
from typing import Dict, List, Tuple
from app.utils.import_helpers import load_excel, clean_str, handle_import_error

def import_coa_from_excel(db_session, file_path: str) -> Tuple[bool, str]:
    """
    Imports Chart of Accounts from an Excel file.
    Expected Columns:
    - code (String)
    - name (String)
    - type (Asset, Liability, Equity, Income, Expense, Trading, Production)
    - parent_code (String, optional)
    - account_class (String, optional)
    - balance_type (Debit/Credit)
    """
    try:
        df, error = load_excel(file_path, ['code', 'name', 'type'])
        if error:
            return False, error
        assert df is not None
        
        # Ensure codes are strings to handle leading zeros
        df['code'] = df['code'].astype(str).str.strip()
        if 'parent_code' in df.columns:
            df['parent_code'] = df['parent_code'].astype(str).str.strip()
            df['parent_code'] = df['parent_code'].replace('nan', '')

        # Build a map of existing accounts to avoid duplicates or to update
        existing_accounts = {acc.code: acc for acc in db_session.query(Account).all()}
        
        # First pass: Create or update all accounts without setting parent_id
        new_accounts_map = {}
        
        for index, row in df.iterrows():
            code = row['code']
            if not code or code == 'nan':
                continue
                
            name = str(row['name']).strip()
            acc_type_raw = str(row['type']).strip()
            
            # Flexible type mapping — handles Arabic, English, various casing
            TYPE_MAP = {
                'asset': 'Asset', 'assets': 'Asset', 'أصول': 'Asset', 'أصل': 'Asset',
                'liability': 'Liability', 'liabilities': 'Liability', 'خصوم': 'Liability', 'التزامات': 'Liability',
                'equity': 'Equity', 'حقوق ملكية': 'Equity', 'حقوق': 'Equity',
                'income': 'Income', 'revenue': 'Income', 'revenues': 'Income',
                'إيرادات': 'Income', 'إيراد': 'Income',
                'expense': 'Expense', 'expenses': 'Expense',
                'مصروفات': 'Expense', 'مصروف': 'Expense',
                'trading': 'Trading', 'متاجرة': 'Trading',
                'production': 'Production', 'تشغيل': 'Production',
            }
            acc_type = TYPE_MAP.get(acc_type_raw.lower(), 'Asset')
            
            acc_class = clean_str(row.get('account_class', ''))
            
            balance_type = clean_str(row.get('balance_type', 'Debit'), 'Debit')
            
            if code in existing_accounts:
                acc = existing_accounts[code]
                acc.name = name
                acc.type = acc_type
                acc.account_class = acc_class
                acc.balance_type = balance_type
            else:
                acc = Account(
                    code=code,
                    name=name,
                    type=acc_type,
                    account_class=acc_class,
                    balance_type=balance_type
                )
                db_session.add(acc)
            
            new_accounts_map[code] = acc
            existing_accounts[code] = acc
            
        db_session.flush() # Flush to get IDs for new accounts
        
        # Second pass: Set parent_id, level, and path
        for index, row in df.iterrows():
            code = row['code']
            if not code or code == 'nan':
                continue
                
            acc = existing_accounts[code]
            parent_code = row.get('parent_code', '')
            
            if parent_code and parent_code != 'nan' and parent_code in existing_accounts:
                parent_acc = existing_accounts[parent_code]
                acc.parent_id = parent_acc.id
                acc.level = (parent_acc.level or 1) + 1
                acc.path = f"{parent_acc.path or parent_acc.code}/{acc.code}"
            else:
                acc.parent_id = None
                acc.level = 1
                acc.path = acc.code
                
        db_session.commit()
        return True, "تم استيراد شجرة الحسابات بنجاح"
        
    except Exception as e:
        return False, handle_import_error(db_session, e)
