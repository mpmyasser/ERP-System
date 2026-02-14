import sys
import os
import re

# Add core to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
core_dir = os.path.join(current_dir, 'core')
if core_dir not in sys.path:
    sys.path.insert(0, core_dir)

from db_manager import DBManager
from accounting_models import Account, AccountType
from sqlalchemy.orm import Session

def determine_type(code):
    """
    Determine account type based on code prefix according to user's chart.
    1 -> Asset
    11, 12, 13, 16, 18 -> Asset
    26 -> Liability (Creditors)
    27 -> Equity/Liability
    28 -> Expense (Operating)
    29 -> Expense (G&A)
    30 -> Expense (Financial)
    32 -> Expense (Supplies)
    33 -> Expense (Services)
    41, 42 -> Income
    9 -> Equity/Other
    """
    if code.startswith('1'):
        return AccountType.ASSET.value
    elif code.startswith('26'):
        return AccountType.LIABILITY.value
    elif code.startswith('27'):
        return AccountType.EQUITY.value # Partners
    elif code.startswith('28') or code.startswith('29') or code.startswith('3'):
        return AccountType.EXPENSE.value
    elif code.startswith('4'):
        return AccountType.INCOME.value
    else:
        return "Other"

def seed_coa():
    print("Seeding Chart of Accounts...")
    db = DBManager()
    session = db.get_session()
    
    input_file = os.path.join(current_dir, 'coa_input.txt')
    if not os.path.exists(input_file):
        print(f"File not found: {input_file}")
        return

    # 1. Read and Parse
    accounts_data = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if "Page" in line and "of" in line:
                continue
                
            # Regex to find Code at the end of the line
            # Pattern: Name then space/tab then digits
            match = re.search(r'^(.*?)\s+(\d+)$', line)
            if match:
                name = match.group(1).strip()
                code = match.group(2).strip()
                
                # Check if it duplicates
                # We handle duplicates on insert
                
                accounts_data.append({
                    'code': code,
                    'name': name,
                    'type': determine_type(code)
                })
            else:
                # specific fix for lines that might be reversed "Code Name" or malformed
                # User data seems consistently "Name \t Code"
                pass

    # 2. Sort by code length (parents first usually, but hierarchy building needs parents to exist)
    # Sorting by code string length ensures '11' comes before '111'
    accounts_data.sort(key=lambda x: len(x['code']))
    
    print(f"Found {len(accounts_data)} accounts to process.")
    
    # 3. Insert and Build Hierarchy
    code_to_id = {} # map code -> db_id
    
    count_new = 0
    count_updated = 0
    
    try:
        for acc in accounts_data:
            code = acc['code']
            
            # Find Parent
            parent_id = None
            # logic: peel off digits until we find a parent
            # Try removing last digit, then last 2, etc.
            # 11101 -> parent might be 111 (remove 2)
            # 111 -> parent might be 11 (remove 1)
            
            # We try standard prefixes
            potential_parents = []
            if len(code) > 2:
                # Try typical parent lengths
                # User structure seems variable. 11 -> 111 -> 11101
                # just iterating downwards length
                for i in range(1, len(code)):
                    sub = code[:-i]
                    if sub in code_to_id:
                        parent_id = code_to_id[sub]
                        break
            
            # Check exist
            existing = session.query(Account).filter_by(code=code).first()
            if existing:
                existing.name = acc['name']
                existing.type = acc['type']
                existing.parent_id = parent_id
                code_to_id[code] = existing.id
                count_updated += 1
            else:
                new_acc = Account(
                    code=code,
                    name=acc['name'],
                    type=acc['type'],
                    parent_id=parent_id,
                    is_active=1
                )
                session.add(new_acc)
                session.flush() # to get ID
                code_to_id[code] = new_acc.id
                count_new += 1
                
        session.commit()
        print(f"Success! Added {count_new}, Updated {count_updated}.")
        
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    seed_coa()
