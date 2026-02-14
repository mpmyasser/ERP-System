# Technical Specification: فصل الخزائن العمومية والفرعية

## Technical Context

- **Language**: Python 3.11
- **Web Framework**: Flask (converted from Streamlit)
- **Database**: SQLite with SQLAlchemy ORM
- **Primary Models**: `User`, `CashAccount`, `CashTransfer`, `BankAccount`
- **Authentication**: Flask login_required decorator
- **Authorization**: Role-based access control using `SystemPermission` and `User.is_admin`

## Technical Implementation Brief

### Current Issues
1. **Database Schema Error**: Column `display_order` doesn't exist in `cash_accounts` table (causing line 28 error)
2. **Missing Hierarchy**: No distinction between primary (عمومية) and subsidiary (فرعية) cash accounts
3. **No Parent-Child Relationship**: Can't filter transfers between specific cash account types

### Solution Approach
1. **Add Database Migration**: Add `parent_cash_id` and ensure `display_order` exists
2. **Enhanced Filtering**: Use `parent_cash_id` to identify account types
   - `parent_cash_id IS NULL` = Primary (عمومية) account
   - `parent_cash_id IS NOT NULL` = Subsidiary (فرعية) account
3. **Role-Based Access**: Use new `cash_type` values: 'General' (عمومية), 'Subsidiary' (فرعية)
4. **Smart Transfer Logic**:
   - Only allow transfers from General → Subsidiary
   - Admin can transfer between any accounts
   - Users can only initiate transfers from their assigned accounts
5. **Reports**: Query with type-based filters for accurate reporting

## Source Code Structure

```
d:\H.R\
├── core/
│   ├── treasury_models.py          # CashAccount, BankAccount, CashTransfer models
│   ├── database_models.py          # Base ORM models
│   ├── auth_models.py              # User, SystemPermission models
│   └── db_manager.py               # Database session management
├── app/
│   └── routes/
│       └── treasury.py             # Treasury routes (dashboard, transfers, reports)
└── migrations/
    └── add_cash_account_hierarchy.py  # NEW: Migration script
```

## Contracts

### Database Schema Changes

#### 1. CashAccount Model (treasury_models.py)
```python
class CashAccount(Base):
    __tablename__ = 'cash_accounts'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    type = Column(String(20), default='General')  # 'General' or 'Subsidiary'
    parent_cash_id = Column(Integer, ForeignKey('cash_accounts.id'), nullable=True)  # NEW
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)  # ENSURE EXISTS
    
    parent = relationship('CashAccount', remote_side=[id], backref='subsidiaries')  # NEW
    account = relationship('Account')
```

#### 2. CashTransfer Model (treasury_models.py)
```python
# Ensure status values are: 'Pending', 'Received', 'Cancelled'
# Ensure transfer_date is Date, not DateTime
```

#### 3. SQL Migrations Needed
- Add `parent_cash_id` column if missing
- Add `display_order` column if missing (data migration)
- Create index on `parent_cash_id` for better query performance
- Create index on `user_id` and `type`

### Route Changes

#### 1. Dashboard Route (`treasury_bp.route('/dashboard')`)
**Current Issue**: Line 28 queries with `.order_by(CashAccount.display_order)` but column doesn't exist

**Changes**:
- Filter by `type` and `parent_cash_id` in addition to `user_id`
- Show separate sections for "General" and "Subsidiary" accounts
- Show pending transfers count for each account

#### 2. Transfer Routes
**New logic**:
- `POST /transfer`: Only allow General → Subsidiary transfers
- Admin can override restrictions
- Auto-set `parent_cash_id` when creating transfers

#### 3. New Reports
- `GET /transfers/report`: Show all transfers with type-based filtering
- Add query parameters: `account_type`, `direction` (to, from)

### Authorization/Permissions

#### New Roles
1. **Financial Manager** (مدير مالي)
   - Permission: `manage_general_accounts`
   - Can see and manage only accounts where `type='General'`
   - Can initiate transfers to subsidiary accounts

2. **Subsidiary Treasurer** (أمين الخزينة الفرعية)
   - Permission: `manage_subsidiary_accounts`
   - Can see and manage only accounts where `type='Subsidiary'` and `user_id=<current_user>`
   - Can receive transfers and record expenditures

3. **Admin** (مسؤول)
   - Full access to all functionality

#### Implementation
- Add role check in routes before rendering templates
- Use `current_user_id` and `account.type` to determine access
- Return 403 Forbidden if user tries to access unauthorized accounts

## Delivery Phases

### Phase 1: Database Migration & Error Fix (Critical)
- Create migration script to add `parent_cash_id` and fix `display_order`
- Run migration
- Verify no schema errors in dashboard

**Deliverable**: Dashboard loads without errors

---

### Phase 2: Account Type Filtering
- Update `CashAccount` model with `parent_cash_id` relationship
- Update dashboard to show separate sections for General/Subsidiary accounts
- Update all queries to include type filtering
- Update forms to show appropriate accounts based on user role

**Deliverable**: Dashboard shows accounts separated by type with correct filtering

---

### Phase 3: Enhanced Transfer System
- Implement logic to enforce General → Subsidiary transfers only
- Add validation in `POST /transfer` route
- Update `receive_transfers` route to show only subsidiary accounts
- Add transfer direction indicators in UI

**Deliverable**: Can send and receive transfers between account types correctly

---

### Phase 4: Reports Enhancement
- Create report template showing transfer history with account types
- Add filters for account type, direction, date range
- Show running balances for each account
- Generate detailed "كشف الحساب" (account statement)

**Deliverable**: Reports show accurate transfer data with proper filtering

---

### Phase 5: Authorization & Permissions
- Add permission checks to all routes
- Create permission assignment logic
- Add role-specific UI elements
- Test access control for different user roles

**Deliverable**: Users can only see/access accounts matching their role

---

## Verification Strategy

### Phase 1 Verification
1. Run: `python -m pytest test_treasury_schema.py` (to be created)
2. Check: `PRAGMA table_info(cash_accounts)` includes `display_order` and `parent_cash_id`
3. Run: `GET /treasury/dashboard` - should load without 404 errors

### Phase 2 Verification
1. Run: Helper script `verify_account_filtering.py`
   - Creates test data: 2 General accounts, 2 Subsidiary accounts
   - Queries both types
   - Verifies counts and filtering
2. Check dashboard UI shows separate account sections
3. Verify forms show correct account options

### Phase 3 Verification
1. Unit test: `test_transfer_validation.py`
   - Test: Can't transfer General→General
   - Test: Can't transfer Subsidiary→Subsidiary
   - Test: Can transfer General→Subsidiary
   - Test: Admin can transfer any direction
2. Integration test: Full transfer flow (send → receive → confirm)
3. Check: CashTransfer records created with correct from/to accounts

### Phase 4 Verification
1. Run: `test_reports_generation.py`
   - Generate report with test data
   - Verify correct filtering by type and date range
   - Check balance calculations are accurate
2. Visual verification: Open report page and test filters
3. Export and verify data completeness

### Phase 5 Verification
1. Unit test: `test_treasury_permissions.py`
   - Test Financial Manager can only see General accounts
   - Test Subsidiary Treasurer can only see their account
   - Test Admin sees all accounts
2. Integration test: Try to access unauthorized accounts → 403
3. Check permission UI elements show/hide correctly

### Helper Scripts & Tools

#### `migrations/add_cash_account_hierarchy.py`
- Adds missing columns to cash_accounts table
- Populates `display_order` with default values if NULL
- Creates necessary indexes

#### `verify_account_filtering.py`
- Creates test data in test database
- Tests query filtering
- Outputs filtering verification report

#### `test_treasury_schema.py` (unittest)
- Verifies schema changes applied correctly
- Tests model relationships

#### `test_transfer_validation.py` (unittest)
- Tests transfer direction rules
- Tests role-based restrictions

#### `test_reports_generation.py` (unittest)
- Tests report query logic
- Verifies data accuracy in reports

#### `test_treasury_permissions.py` (unittest)
- Tests authorization checks on routes
- Tests role-based access control

### Sample Data Requirements
- Create test fixtures with:
  - 1 General cash account (type='General', parent_cash_id=NULL)
  - 2 Subsidiary cash accounts (type='Subsidiary', parent_cash_id=1)
  - 2 Users: 1 Financial Manager, 1 Subsidiary Treasurer
  - Sample CashTransfer records with various statuses

### MCP Servers
- None required (using built-in SQLite and Python)

