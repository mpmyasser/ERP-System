# Product Requirements Document (PRD)

## Human Resources & ERP Management System

| Meta | |
|---|---|
| **Document Version** | 1.0 |
| **Status** | Draft |
| **Prepared From** | project_index.md, architecture.md, features.md, data_model.md, requirements.md |
| **System Type** | Monolithic Flask Web Application — Bilingual (Arabic/English) |
| **Deployment Model** | Offline, single-server, SQLite-backed |

---

## 1. Executive Summary

This document defines the product requirements for a bilingual (Arabic/English) Human Resources and Enterprise Resource Planning (ERP) management system originally migrated from Streamlit to Flask. The system has grown beyond pure HR into a full ERP covering payroll, accounting (double-entry), treasury (cash/bank/check management), commercial operations (inventory, sales, purchases), manufacturing operations (cutting, dispatch, receiving, packing, factory accounting), and fabric roll tracking.

The system serves Egyptian small-to-medium enterprises with:
- Egyptian-specific HR policy rules (payroll cycles, insurance policies, absence penalties)
- Full Arabic RTL user interface
- Server-side DataTables for performance
- Session-based authentication with role-based permissions
- Three SQLite databases with schema auto-migration
- An independent manufacturing operations subsystem with its own database

This PRD is derived exclusively from the five discovery-phase analysis documents. All information herein is traced back to those documents. Assumptions are explicitly marked.

---

## 2. Product Vision

A comprehensive, offline-capable, bilingual HR and ERP management system that enables small-to-medium Egyptian enterprises to manage their entire workforce lifecycle, financial operations, and manufacturing processes from a single unified platform.

---

## 3. Business Objectives

| Objective | Description |
|---|---|
| **BO-01** | Provide a single platform for all HR operations — employee lifecycle, attendance, payroll, loans, leaves, permissions, penalties, and bonuses |
| **BO-02** | Deliver accurate, policy-compliant monthly payroll calculations with configurable Egyptian HR rules |
| **BO-03** | Enable full double-entry accounting with hierarchical Chart of Accounts, journal entries, and cost centers |
| **BO-04** | Provide treasury management with cash accounts, bank accounts, checks, and access control |
| **BO-05** | Support basic commercial operations — partners, products, warehouses, invoices |
| **BO-06** | Enable manufacturing operations tracking (cut batch → dispatch → receive → pack → finished stock → accounting settlement) |
| **BO-07** | Operate fully offline with zero external service dependencies (except optional WhatsApp for password recovery) |
| **BO-08** | Maintain complete audit trails for employee data changes and salary history |

---

## 4. Success Metrics

| Metric | Target |
|---|---|
| Payroll calculation accuracy | No arithmetic errors in computed gross/net/deductions |
| Attendance import success rate | >95% for properly formatted Excel exports |
| System availability | Works fully offline with no external API dependencies |
| Employee data integrity | All changes tracked in AuditLog; all salary changes in SalaryHistory |
| Loan balance accuracy | Dynamic balance computation matches expected manual calculation |

---

## 5. Scope

### 5.1 In Scope

| Area | Coverage |
|---|---|
| HR Management | Employee lifecycle, departments, documents, photo upload |
| Attendance | Excel import, daily record processing, manual override, payroll integration |
| Payroll | Monthly calculation, attendance deductions, overtime, loans, leaves, permissions, penalties, bonuses, insurance |
| Loans | Permanent/temporary, installment tracking, excluded months, dynamic balance, Excel export |
| Leaves | Annual/sick/casual/emergency leave, balance initialization, payroll integration |
| Permissions | Paid/unpaid work permissions, payroll deduction |
| Penalties & Bonuses | Penalty/bonus entries, payroll deduction/addition |
| Accounting | Chart of Accounts (tree), journal entries (double-entry), cost centers |
| Treasury | Cash accounts (general/subsidiary), bank accounts, check records, access control |
| Commercial | Partners, products, warehouses, invoices (sales/purchase/returns) |
| Fabric Tracking | Serialized rolls, weight/meter tracking, dyeing/printing lifecycle, supplier linking |
| Production Management | Production products, factories, cut batches |
| Manufacturing Operations | Cut batches, dispatch, receiving, factory pricing/payments, packing, finished stock, accounting settlements |
| Authentication | Session-based login, role-based access, granular permissions |
| Audit Trail | Automatic logging of all employee field changes |
| Data Import | Excel import for Chart of Accounts, partners, fabric rolls, manufacturing cut items |
| System Settings | UI-driven configuration of system-wide parameters |

### 5.2 Out of Scope

| Area | Rationale |
|---|---|
| Email notifications | Not found in codebase (Assumption A-005) |
| ERP integration | `ERPService` is placeholder only, `enabled = False` (Assumption A-006) |
| External API authentication (JWT/API keys) | System uses session-based auth only (Assumption A-008) |
| Centralized application logging | No logging framework configured (Assumption A-004) |
| Mobile app / native client | Web-only via browser |
| Multi-company / multi-tenant architecture | Single-organization design |
| Real-time notifications / push alerts | Not implemented |
| Cloud deployment / hosting | Offline-first, SQLite-based |

---

## 6. Target Users

| User Group | Organization Role |
|---|---|
| HR Managers | Manage employees, attendance, leaves, permissions, loans, penalties |
| Payroll Accountants | Run monthly payroll, manage salary history |
| Financial Accountants | Manage COA, journal entries, treasury |
| Store/Inventory Managers | Manage products, warehouses, invoices |
| Production Managers | Manage manufacturing operations (cutting, dispatch, receiving, packing) |
| Factory Accountants | Manage factory payments, accounting settlements |
| System Administrators | Manage users, permissions, system settings, git status |
| Business Owners | View dashboards, reports, high-level statistics |

---

## 7. User Roles

| Role | Identifier | Privileges |
|---|---|---|
| **Admin** | `is_admin = True` | Bypasses all permission checks. Can manage users, assign permissions, access admin panel. Cannot delete own account. |
| **Regular User** | `is_admin = False` | Access limited to assigned `SystemPermission` records (granular, named permissions like `bulk_salary_manage`, `view_loans`, `COA_IMPORT`). Cash account visibility further restricted via `user_cash_account_access` M2M table. |

---

## 8. Personas

### 8.1 Ahmed — HR Manager
- **Background**: 40s, male, Egyptian, manages 120 employees
- **Goals**: Import attendance, process leaves, create loans/penalties, view employee profiles
- **Pain Points**: Wants to edit attendance without losing manual overrides on re-import
- **Usage**: Daily

### 8.2 Mona — Payroll Accountant
- **Background**: 30s, female, Egyptian, responsible for monthly salary calculation
- **Goals**: Accurate payroll with all deductions (loans, penalties, leaves, permissions, insurance)
- **Pain Points**: Needs configurable rules (grace periods, overtime rates, absence penalties)
- **Usage**: Monthly (heavy), weekly (light)

### 8.3 Khaled — Factory Manager
- **Background**: 50s, male, manages 3 outsourcing factories
- **Goals**: Dispatch cut items, receive finished goods, track factory balances
- **Tech Preferences**: Excel imports for bulk data, prefers Arabic UI
- **Usage**: Daily

### 8.4 Mahmoud — Admin
- **Background**: 35s, male, IT administrator
- **Goals**: Manage user accounts, assign permissions, check system health, git status
- **Tech Level**: Technically proficient
- **Usage**: Weekly

---

## 9. User Journeys

### 9.1 Monthly Payroll Run
1. HR manager imports attendance Excel file for the month
2. Reviews and manually corrects any attendance records (overrides preserved)
3. Payroll accountant navigates to Payroll → selects month/year
4. System loads all active employees
5. For each employee: loads attendance, loans, leaves, permissions, penalties, bonuses, salary history
6. Computes gross pay, deductions, additions, net pay
7. Payroll summary displayed with drill-down capability
8. System auto-tracks salary changes via SalaryHistory

### 9.2 Manufacturing Dispatch Flow
1. Production manager creates cut batch (manual or Excel import)
2. Batch items start in "داخل القص" status
3. Manager selects items → sets factory, manufacturing price, dispatch date
4. Price auto-resolved from factory_prices table or user-provided
5. Items dispatched to factory
6. Factory receives items with quality grading (good/repairs/added/remainders)
7. Accounting settlement generated per factory with balance calculation
8. Settlement reversal possible if not yet accounted

### 9.3 Employee Onboarding
1. Admin logs in → navigates to `/employees/create`
2. Fills form: personal info, work details, salary, insurance, schedule
3. Submits → system validates (unique code, national_id format, date checks)
4. Employee record created
5. SQLAlchemy `before_flush` event auto-creates:
   - Initial SalaryHistory entry
   - (On salary change) AuditLog entry
6. Employee appears in list and dashboard statistics

---

## 10. Functional Requirements

### 10.1 Authentication & Authorization (FR-001 to FR-006)

| ID | Requirement | Priority |
|---|---|---|
| FR-001 | System shall authenticate users via username and password using session-based login. Session stores `user_id`, `username`, `full_name`, `is_admin`. | High |
| FR-002 | System shall clear user session on logout. | High |
| FR-003 | System shall allow password reset via WhatsApp OTP (6-digit, 10-minute expiry) or national ID verification as fallback. | Medium |
| FR-004 | Authenticated users shall update their own profile (username, full name, password). | Medium |
| FR-005 | Admin users shall create, edit, list, and delete system users. Admin cannot delete own account. | High |
| FR-006 | Admin shall assign named SystemPermissions and CashAccount access to users. | High |

### 10.2 Dashboard (FR-007)

| ID | Requirement | Priority |
|---|---|---|
| FR-007 | System shall display total employees, active employees, inactive employees, and total departments on the landing page. | Medium |

### 10.3 Department Management (FR-008)

| ID | Requirement | Priority |
|---|---|---|
| FR-008 | System shall allow CRUD operations on departments. | Medium |

### 10.4 Employee Management (FR-009 to FR-013)

| ID | Requirement | Priority |
|---|---|---|
| FR-009 | System shall display a paginated employee list with server-side DataTables, filters for department (include/exclude), status, job title, and date range. | High |
| FR-010 | System shall create employee records with full data fields: personal (name, code, national_id, DOB, mobile, address, city, governorate, marital_status, military_status, num_children), work (job_title, department, category, hire_date, is_active, disruption_date, resignation_reason, schedule, overtime_allowed), financial (basic_salary, transport_allowance, incentive_allowance, regularity_incentive, salary_type), insurance (is_insured, policy, shares). Auto-creates SalaryHistory entry on creation. | High |
| FR-010a | System shall update existing employee records. Changes to `basic_salary` auto-create SalaryHistory entries. All field changes logged in AuditLog. | High |
| FR-011 | System shall display employee details with next/previous navigation. | High |
| FR-012 | System shall permanently delete employee records (hard delete). Cascaded SalaryHistory records removed. | Medium |
| FR-013 | System shall upload, list, and delete employee documents (images, PDF) with type classification, expiry dates, and notes. | Medium |

### 10.5 Attendance Management (FR-014 to FR-015)

| ID | Requirement | Priority |
|---|---|---|
| FR-014 | System shall import raw attendance logs from fingerprint system Excel exports (.xlsx/.xls), process into DailyRecords with status detection (Present/Absent/Vacation/Permission). | High |
| FR-015 | System shall allow manual check-in/check-out editing with `is_manual_override` flag to preserve edits across re-imports. Clearing both check-in and check-out removes the record from payroll calculations. | High |

### 10.6 Payroll (FR-016 to FR-019)

| ID | Requirement | Priority |
|---|---|---|
| FR-016 | System shall calculate monthly payroll for one employee. Loads employee → effective salary via SalaryHistory → daily records → loans → leaves → permissions → penalties → bonuses → public holidays → HRPolicy → returns structured PayrollSummary. | High |
| FR-017 | System shall compute deductions: absence (after grace days), lateness (after grace period), early departure, loan installments (considering excluded months), unpaid leave, unpaid permission hours, penalty amounts. | High |
| FR-018 | System shall compute additions: overtime pay, bonus amounts, regularity incentive. | High |
| FR-019 | System shall automatically track all salary changes via SQLAlchemy `before_flush` event — creates initial SalaryHistory on employee create, entries on every `basic_salary` change. | High |

### 10.7 Loans (FR-020 to FR-023)

| ID | Requirement | Priority |
|---|---|---|
| FR-020 | System shall create loans with type (permanent/temporary), amount, installments_count, date, excluded_months. Installment = amount / count. | High |
| FR-021 | System shall display loans with server-side AJAX DataTable, filters for date range, department (include/exclude), employee code search. | High |
| FR-022 | Loan remaining balance shall be dynamically computed based on payoff cycle (26th → 25th payroll cycle). Excluded months skip deduction. | High |
| FR-023 | System shall export loan data to professionally formatted Excel. | Medium |

### 10.8 Penalties & Bonuses (FR-024 to FR-025)

| ID | Requirement | Priority |
|---|---|---|
| FR-024 | System shall create penalty (خصم) or bonus (مكافأة) entries with date, type, amount, optional days, reason. | High |
| FR-025 | System shall manage bonuses separately with `paid_with_salary` flag, filterable by date range and department. | Medium |

### 10.9 Work Permissions (FR-026)

| ID | Requirement | Priority |
|---|---|---|
| FR-026 | System shall create work permissions (أذونات) with date, from_time, to_time, reason, is_paid flag. Affects DailyRecord status. | High |

### 10.10 Leaves (FR-027 to FR-028)

| ID | Requirement | Priority |
|---|---|---|
| FR-027 | System shall initialize annual leave balances per employee per year. Defaults: annual=21, sick=30, casual=7, emergency=3 days. | High |
| FR-028 | System shall create leave requests with type (annual/sick/casual/emergency/unpaid), date range, reason. Defaults to auto-approved (status='موافق عليها'). Decrements balance. | High |

### 10.11 Accounting (FR-029 to FR-030)

| ID | Requirement | Priority |
|---|---|---|
| FR-029 | System shall manage hierarchical Chart of Accounts (adjacency list with parent_id, level, path, balance_type). Types: Asset, Liability, Equity, Income, Expense, Trading, Production. | High |
| FR-030 | System shall allow double-entry journal entries with multiple debit/credit lines per entry. Statuses: Draft/Posted/Cancelled. | High |

### 10.12 Treasury (FR-031 to FR-032)

| ID | Requirement | Priority |
|---|---|---|
| FR-031 | System shall manage cash accounts with general/subsidiary hierarchy linked to Chart of Accounts. Also supports bank accounts and check records (Pending/Collected/Bounced/Cancelled). | High |
| FR-032 | System shall restrict cash account visibility per user via `user_cash_account_access` M2M table. | High |

### 10.13 Commercial (FR-033 to FR-035)

| ID | Requirement | Priority |
|---|---|---|
| FR-033 | System shall manage partners (Customer/Supplier/Both/Factory). | Medium |
| FR-034 | System shall create invoices (Sales/Purchase/SalesReturn/PurchaseReturn) with line items, amounts, partner, warehouse. | Medium |
| FR-035 | System shall manage products (code, cost_price, sale_price, stock) and warehouses (Raw/Accessory/Finished/General). | Medium |

### 10.14 Fabric Tracking (FR-036 to FR-037)

| ID | Requirement | Priority |
|---|---|---|
| FR-036 | System shall track fabric rolls with unique serial numbers, type, color, gross/net weight (net = gross − 0.450 kg per roll), meters, supplier, warehouse, design, lifecycle status (Raw → Dyed → Printed → Cut → Sold). | Low |
| FR-037 | System shall manage production messages (dyeing/printing orders) to partner factories with weight/meter tracking and loss calculation. | Low |

### 10.15 Manufacturing Operations (FR-038 to FR-044)

| ID | Requirement | Priority |
|---|---|---|
| FR-038 | System shall create cut batches (manual or Excel import) with products (code, name, size, quantity). Batch codes auto-generated as `CUT-YYYYMMDD-NNN`. | High |
| FR-039 | System shall dispatch cut items to factories with manufacturing price (auto-resolved from factory_prices table if available) and dispatch date. | High |
| FR-040 | System shall receive finished goods from factories with quality grading (good, repairs, added, remainders). | High |
| FR-041 | System shall manage per-factory per-product pricing (price per dozen) with Excel import/export. | High |
| FR-042 | System shall generate accounting settlement statements per factory with deduction tracking and balance calculation. | High |
| FR-043 | System shall reverse accounting settlements: unmarks items, deletes related factory payment. | Medium |
| FR-044 | System shall display a manufacturing dashboard with totals for items, quantities, distinct messages, optional pending-only filter. | Medium |

### 10.16 Data Import (FR-045)

| ID | Requirement | Priority |
|---|---|---|
| FR-045 | System shall import Chart of Accounts, Partners, and Fabric Rolls from Excel files (requires `COA_IMPORT` permission). | Medium |

### 10.17 Configuration & User Preferences (FR-046 to FR-048)

| ID | Requirement | Priority |
|---|---|---|
| FR-046 | System shall allow viewing and editing SystemSettings grouped by category. | High |
| FR-047 | System shall provide generic key-value API for per-user preferences (GET/POST). | Medium |
| FR-048 | System shall persist table column widths per user per page via `UserTableSetting`. | Low |

### 10.18 Audit Trail (FR-049)

| ID | Requirement | Priority |
|---|---|---|
| FR-049 | System shall automatically log all Employee field changes to AuditLog (employee_code, field_name, old_value, new_value, timestamp) via SQLAlchemy `before_flush` event. | High |

### 10.19 Admin Panel (FR-050 to FR-051)

| ID | Requirement | Priority |
|---|---|---|
| FR-050 | Admin panel shall display git repository status (branch, recent commits, commit hash). | Low |
| FR-051 | Admin panel shall scan and list all `.db` files in the project directory. | Low |

### 10.20 Interactive AJAX API (FR-052)

| ID | Requirement | Priority |
|---|---|---|
| FR-052 | System shall provide JSON API endpoints for adding loans, penalties, bonuses, and permissions without page reload: POST `/api/interactive/add_loan`, `add_penalty`, `add_bonus`, `add_permission`. Return `{success, message}`. | Medium |

### 10.21 Insurance & Utilities (FR-053 to FR-054)

| ID | Requirement | Priority |
|---|---|---|
| FR-053 | System shall calculate insurance contributions based on policy type (`employee_only` / `both_from_employee` / `company_pays_all`): employee_value = insurance_salary × (employee_share / 100), company_value = insurance_salary × (company_share / 100). | High |
| FR-054 | System shall parse Egyptian National IDs (14 digits, century digit 2=1900s, 3=2000s) to extract birthdate and calculate age. | Low |

---

## 11. Non-Functional Requirements

| ID | Category | Requirement | Priority |
|---|---|---|---|
| NFR-001 | Performance | Server-side DataTables pagination for loans and employee lists | High |
| NFR-002 | Security | All endpoints (except login/static) require active session with `user_id` | High |
| NFR-003 | Security | Passwords stored with Werkzeug `generate_password_hash` | High |
| NFR-004 | Security | All POST requests CSRF-protected via Flask-WTF; token exposed to JS via `<meta>` tag | High |
| NFR-005 | Authorization | Two roles: Admin (bypasses checks) and Regular (limited to assigned SystemPermissions) | High |
| NFR-006 | Authorization | Granular named permissions by category, assignable via M2M | High |
| NFR-007 | Authorization | Cash account access controlled per user via `user_cash_account_access` M2M table | High |
| NFR-008 | Data Integrity | SQLAlchemy ForeignKey constraints with `PRAGMA foreign_keys = ON` on `core/hr.db` | High |
| NFR-009 | Audit | All Employee field changes logged to AuditLog automatically | High |
| NFR-010 | Audit | All salary changes recorded in SalaryHistory with old/new values and effective date | High |
| NFR-011 | Migration | DBManager auto-migrates missing columns/tables on startup via ALTER TABLE (convenience, not full replacement) | Medium |
| NFR-012 | i18n | Entire UI in Arabic with RTL layout (Bootstrap 5.3 RTL, Google Fonts Cairo) | High |
| NFR-013 | Format | All dates in DD/MM/YYYY format with compact format fallback (DDMMYYYY) | High |
| NFR-014 | Performance | System designed for single-user/small-team local SQLite deployment; concurrent writes limited by SQLite locking | Low |
| NFR-015 | Browser | Support modern browsers via CDN-hosted Bootstrap, DataTables, AG-Grid, Flatpickr, Select2 | Medium |
| NFR-016 | Error Handling | User-facing messages via Flask flash with Bootstrap alert classes | Medium |
| NFR-017 | Error Handling | Critical operations wrapped in try/except with rollback and error messages | Medium |
| NFR-018 | Config | Flask configuration centralized in `app/config.py` (SECRET_KEY, DATABASE_PATH, CSRF, ITEMS_PER_PAGE) | High |
| NFR-019 | Config | HR policy values configurable at runtime via `SystemSetting` table, read dynamically by `HRPolicy` metaclass | High |
| NFR-020 | Logging | No centralized logging framework (Assumption A-004) | Low |

---

## 12. Business Rules

| ID | Rule | Description |
|---|---|---|
| BR-001 | Payroll Cycle | Salary month runs 26th of previous month → 25th of current month (configurable) |
| BR-002 | Working Days | 26 working days per month (configurable) |
| BR-003 | Daily Salary | `daily_salary = basic_salary / working_days_per_month` |
| BR-004 | Lateness | 10-minute grace period (configurable), deducted at 1× hourly rate (configurable) |
| BR-005 | Early Departure | No grace period (configurable), deducted at 1× hourly rate (configurable) |
| BR-006 | Absence | 2-day grace period (configurable), then 0.25 day penalty per absence day (configurable) |
| BR-007 | Overtime | Min 60 min to qualify, 1.5× rate (configurable), first hour fixed as 1 hour, HALF_HOUR rounding |
| BR-008 | Loan Installment | Installment = amount / count. Deducted if `as_of` date has passed the 25th of that month. |
| BR-009 | Loan Excluded | Comma-separated months (1-12) skip loan deduction |
| BR-010 | Leave Defaults | Annual=21, Sick=30, Casual=7, Emergency=3 (hardcoded in `leave_service.py`) |
| BR-011 | Leave Approval | Leaves auto-approved on creation (status default = 'موافق عليها' — Assumption A-007) |
| BR-012 | Manual Override | `is_manual_override = True` prevents automatic attendance overwrite on re-import |
| BR-013 | Payroll Removal | Clearing check-in and check-out removes record from payroll |
| BR-014 | Insurance: emp_only | Employee pays share, company pays share (deducted at source) |
| BR-015 | Insurance: both_from_emp | Employee pays both shares (total deducted from salary) |
| BR-016 | Insurance: company_pays_all | Company pays both shares (no employee deduction) |
| BR-017 | Admin Bypass | Admin users bypass all permission checks, see all data |
| BR-018 | Self-Delete | A user cannot delete their own account |
| BR-019 | OTP Expiry | Forgot password OTP expires after 600 seconds |
| BR-020 | Batch Code | Auto-generated: `CUT-YYYYMMDD-NNN` |
| BR-021 | Price Resolution | Manufacturing price auto-resolved from `operation_factory_prices` if available |
| BR-022 | Dispatch Lock | Cannot reverse dispatch of accounted item (`is_accounted=1`); must reverse accounting first |
| BR-023 | Batch Auto-Delete | Deleting all items from a cut batch auto-deletes the batch header |
| BR-024 | Net Weight | Fabric net weight = gross weight − (number_of_rolls × 0.450 kg) |
| BR-025 | Salary Dating | Payroll uses most recent SalaryHistory entry with `effective_date ≤ month end`; falls back to earliest `old_salary`, then `employee.basic_salary` |

---

## 13. Validation Rules

| ID | Rule | Details |
|---|---|---|
| VR-001 | Employee Code | Required, max 50 chars, unique |
| VR-002 | Employee Name | Required, max 200 chars |
| VR-003 | National ID | Exactly 14 chars if provided, unique |
| VR-004 | Date Fields | DD/MM/YYYY format; future dates not allowed for birth/hire/disruption/insurance |
| VR-005 | Mobile | 10-11 numeric digits if provided |
| VR-006 | Numeric Fields | All >= 0 |
| VR-007 | Category | One of: WORKER, EMPLOYEE, SUPERVISOR, DRIVER |
| VR-008 | Salary Type | One of: ثابت, بالساعة, ضيافة |
| VR-009 | Loan Amount | Required, >= 0 |
| VR-010 | Loan Installments | Required, >= 1 |
| VR-011 | Loan Date | Cannot exceed end of current month |
| VR-012 | Excluded Months | Comma-separated integers 1-12 |
| VR-013 | Attendance Excel | .xlsx/.xls extension, required columns present |
| VR-014 | Document Types | Allowed: jpg, jpeg, png, pdf |
| VR-015 | Manufacturing Product | Code, name, size required |
| VR-016 | Manufacturing Quantity | >= 0 |
| VR-017 | Manufacturing Price | >= 0 |
| VR-018 | Excel Import Format | Specific column naming expected (Arabic or English), positional fallback |
| VR-019 | Password Confirmation | New password and confirmation must match |
| VR-020 | Username Uniqueness | Unique across all users |

---

## 13. System Modules

| Module | Blueprint | Files | Database |
|---|---|---|---|
| Auth | `auth_bp` | `core/auth_models.py`, `core/auth_manager.py`, `app/routes/auth.py` | `core/hr.db` |
| Dashboard | (home route) | `app/routes/__init__.py` | `core/hr.db` |
| Departments | `departments_bp` | `app/routes/departments.py` | `core/hr.db` |
| Employees | `employees_bp` | `app/routes/employees.py` | `core/hr.db` |
| Attendance | `attendance_bp` | `core/services/attendance_service.py`, `app/routes/attendance.py` | `core/hr.db` |
| Payroll | `payroll_bp` | `core/services/payroll_processor.py`, `app/routes/payroll.py` | `core/hr.db` |
| Loans | `loans_bp` | `core/services/loans_service.py`, `app/routes/loans.py` | `core/hr.db` |
| Penalties | `penalties_bp` | `app/routes/penalties.py` | `core/hr.db` |
| Bonuses | `bonuses_bp` | `app/routes/bonuses.py` | `core/hr.db` |
| Permissions | `permissions_bp` | `core/services/permissions_service.py`, `app/routes/permissions.py` | `core/hr.db` |
| Leaves | `leaves_bp` | `core/services/leave_service.py`, `app/routes/leaves.py` | `core/hr.db` |
| Accounting | `accounting_bp` | `core/accounting_models.py`, `app/routes/accounting.py` | `core/hr.db` |
| Treasury | `treasury_bp` | `core/treasury_models.py`, `app/routes/treasury.py` | `core/hr.db` |
| Commercial | `commercial_bp` | `core/commercial_models.py`, `app/routes/commercial.py` | `core/hr.db` |
| Fabric | (fabric routes) | `core/fabric_models.py` | `core/hr.db` |
| Production | `manufacturing_bp` | `core/production_models.py`, `app/routes/manufacturing.py` | `core/production.db` (legacy) + `operation.db` |
| Manufacturing Ops | (manufacturing subroutes) | `app/manufacturing_storage/operation_storage.py`, `app/routes/operation_storage.py` | `operation.db` |
| Interactive API | `interactive_api_bp` | `app/routes/interactive_api.py` | `core/hr.db` |
| Universal Importer | `universal_importer_bp` | `app/routes/universal_importer.py` | `core/hr.db` |
| Settings | `settings_bp` | `app/routes/settings.py` | `core/hr.db` |
| Reports | `reports_bp` | `app/routes/reports.py` | `core/hr.db` |
| Admin | `admin_bp` | `app/routes/admin.py` | `core/hr.db` + git |
| Audit | (embedded) | `core/database_models.py` (AuditLog) | `core/hr.db` |
| ERP Service | (no routes) | `core/services/erp_service.py` | Placeholder |

---

## 15. Feature Catalog

| Feature | Module | Priority | Data Entry Mode |
|---|---|---|---|
| User login/logout | Auth | High | Form |
| Forgot password (OTP) | Auth | Medium | Form + WhatsApp |
| User + permission CRUD | Auth | High | Form |
| Dashboard statistics | Dashboard | Medium | Auto-rendered |
| Department CRUD | Departments | Medium | Form |
| Employee CRUD | Employees | High | Form |
| Employee documents | Employees | Medium | Upload |
| Attendance Excel import | Attendance | High | File upload |
| Manual attendance editing | Attendance | High | Form |
| Payroll calculation | Payroll | High | Form |
| Salary history tracking | Payroll | High | Automatic |
| Loan CRUD | Loans | High | Form + AJAX |
| Loan Excel export | Loans | Medium | Export |
| Penalty/bonus entries | Penalties | High | Form + AJAX |
| Bonus management (separate) | Bonuses | Medium | Form |
| Work permissions | Permissions | High | Form + AJAX |
| Leave balance init | Leaves | High | Automatic |
| Leave requests | Leaves | High | Form |
| Chart of Accounts | Accounting | High | Form + Import |
| Journal entries | Accounting | High | Form |
| Cash account hierarchy | Treasury | High | Form |
| Bank accounts | Treasury | Medium | Form |
| Check records | Treasury | Medium | Form |
| Cash access control | Treasury | High | Admin |
| Partner CRUD | Commercial | Medium | Form + Import |
| Invoice management | Commercial | Medium | Form |
| Product/warehouse | Commercial | Medium | Form |
| Fabric roll tracking | Fabric | Low | Form + Import |
| Production messages | Fabric | Low | Form |
| Manufacturing cut batches | Manufacturing | High | Form + Import |
| Dispatch/receiving | Manufacturing | High | Form |
| Factory pricing | Manufacturing | High | Form + Import |
| Accounting settlements | Manufacturing | High | Form |
| Manufacturing dashboard | Manufacturing | Medium | Auto-rendered |
| Factory payments | Manufacturing | Medium | Form |
| Packing/finished stock | Manufacturing | Medium | Form |
| Universal Excel import | Importer | Medium | File upload |
| System settings | Settings | High | Form |
| User preferences | Settings | Medium | API |
| Table width persistence | Settings | Low | JS → API |
| Audit trail | Reports | High | Automatic |
| Admin git/DB scan | Admin | Low | Auto-rendered |
| Interactive API | API | Medium | JSON API |
| Egyptian National ID parse | Utility | Low | Utility function |
| Insurance calculation | Payroll | High | Inside payroll |

---

## 16. Data Model Overview

### 16.1 Database Architecture

Three separate SQLite databases serve distinct subsystems:

| Database | Path | Engine | Entities | Migrations |
|---|---|---|---|---|
| **Primary (HR/ERP)** | `core/hr.db` | SQLAlchemy 2.0 ORM | 30+ entities | Auto-migration via DBManager (add-only ALTER TABLE) |
| **Production** | `core/production.db` | SQLAlchemy | ~6 entities (ProductionProduct, Factory, Cut, etc.) | Manual via `init_production_db.py` |
| **Manufacturing Ops** | `app/manufacturing_storage/data/operation.db` | Raw `sqlite3` | 8 tables (cut batches, items, factories, prices, payments, settings, finished stock, products) | Auto-initialized on module import |

### 16.2 Core HR Entities (38 entities across all databases)

| Entity Group | Entities | Primary Relationships |
|---|---|---|
| **Employees** | Employee, Department | M:1 Department→Employee |
| **Attendance** | AttendanceLog, DailyRecord | 1:M Employee→AttendanceLog, Employee→DailyRecord |
| **Financial** | Loan, PenaltyBonus, Bonus, SalaryHistory | 1:M Employee→each |
| **Time Off** | LeaveBalance, Leave, Permission | 1:M Employee→each |
| **Documents** | DocumentType, EmployeeDocument | 1:M DocumentType→EmployeeDocument, 1:M Employee→EmployeeDocument |
| **Accounting** | Account, CostCenter, JournalEntry, JournalItem | 1:M JournalEntry→JournalItem (cascade delete-orphan), M:1 Account→JournalItem |
| **Treasury** | CashAccount, BankAccount, CheckRecord, CashTransfer | 1:1 CashAccount→Account, M:1 CashTransfer→CashAccount |
| **Commercial** | Partner, Product, Warehouse, Invoice, InvoiceItem, InventoryTransaction | 1:M Invoice→InvoiceItem (cascade delete-orphan) |
| **Fabric** | FabricRoll, FabricDesign, ProductionMessage | M:1 FabricRoll→each |
| **Production** | ProductionProduct, ProductionFactory, ProductionCut, ProductionCutDetail | 1:M ProductionCut→ProductionCutDetail |
| **Auth** | User, SystemPermission, UserPreference, UserTableSetting | M:M User→SystemPermission, M:M User→CashAccount |
| **Config** | SystemSetting, PublicHoliday, AuditLog | Standalone / relationless |
| **Manufacturing** | operation_products, operation_cut_batches, operation_cut_items, operation_factories, operation_factory_prices, operation_factory_payments, operation_settings, operation_finished_stock | 1:M operation_cut_batches→operation_cut_items (ON DELETE CASCADE), M:1 operation_products→operation_cut_items |

### 16.3 Key Constraints

- **Unique**: Employee(code, national_id), User(username), Account(code), Product(code), FabricRoll(serial_number), Invoice(invoice_number), SystemSetting(key), SystemPermission(name), CostCenter(code), operation_products(code), operation_factories(code), operation_cut_batches(batch_code)
- **Composite UNIQUE**: ProductionProduct(description, size), UserPreference(user_id, key), operation_factory_prices(factory_code, product_code), operation_finished_stock(product_code, product_size)
- **Cascade**: Account→children (all, delete-orphan), JournalEntry→JournalItem (all, delete-orphan), Invoice→InvoiceItem (all, delete-orphan), ProductionCut→ProductionCutDetail (all, delete-orphan), Employee→SalaryHistory (all, delete-orphan), operation_cut_batches→operation_cut_items (ON DELETE CASCADE)
- **Soft delete**: Employee(is_active), User(is_active), Account(is_active)
- **Hard delete**: Employee records (permanent DELETE), plus most other entities

---

## 17. System Architecture Overview

### 17.1 Architecture Style

Monolithic Flask application with modular blueprint organization (20 registered blueprints). Layered architecture:

```
Browser (RTL UI)
    ↓ HTTP (Jinja2 + JSON APIs)
Flask Application Server (Werkzeug, port 5000)
    ├── Blueprint Routes (20)
    ├── Jinja2 Templates
    └── WTForms + CSRF
    ↓
Core Layer
    ├── DBManager (SQLAlchemy + Auto-Migrate)
    ├── Services (Payroll, Attendance, Loans, Leaves, Permissions)
    └── AuthManager (Sessions, Permission Checks)
        ↓
SQLAlchemy Models (HR • Auth • Accounting • Treasury • Commercial • Fabric)
    ↓
┌─ core/hr.db ──┬─ core/production.db ──┬─ operation.db ──┐
```

### 17.2 Module Dependencies

```
                    HRPolicy (Constants)
                         ↓
         ┌───────────────┼─────────────────┐
         ↓               ↓                  ↓
    Payroll ←──── Attendance     Permissions
    Service        Service         Service
      |               |                |
      |        ┌──────┴──────┐
      |        ↓              ↓
      |    Loans           Leaves
      |    Service         Service
      ↓
Accounting ────→ Treasury ←─── Commercial

Fabric Tracking (independent)
Production Management (independent)
Manufacturing Ops (fully independent DB, no HR dependencies)
```

### 17.3 Key Architectural Facts

| Aspect | Detail |
|---|---|
| Language | Python 3.11+ |
| Web Framework | Flask 3.0 |
| ORM | SQLAlchemy 2.0 |
| Database | SQLite (all 3 DBs) |
| Frontend | Bootstrap 5.3 RTL, DataTables, AG-Grid, Flatpickr, Select2, jQuery |
| Auth | Session-based, Werkzeug password hashing, CSRF |
| Layout | Monolithic Flask factory pattern |
| UI Language | Arabic (RTL), with English data values |
| Importers | pandas + openpyxl for Excel imports |

---

## 18. External Integrations

| Integration | Status | Detail |
|---|---|---|
| WhatsApp API | Optional | Used for forgot password OTP only. Configurable via `WHATSAPP_API_URL`, `WHATSAPP_API_TOKEN` env vars. System works without it (falls back to national ID verification). |
| ERP Integration | Placeholder | `ERPService` class exists with all methods returning dummy data. `enabled = False` by default. No actual integration. |
| CSRF Protection | Active | Flask-WTF CSRF enabled; token exposed to JS via `<meta name="csrf-token">`. |
| Email | Not implemented | No email notification system (Assumption A-005). |
| GitPython | Internal | Used in admin panel to read git status only (no external repo push/pull). |

---

## 19. Security & Permissions

### 19.1 Authentication

- **Mechanism**: Session-based (Flask signed cookies)
- **Password Hashing**: Werkzeug `generate_password_hash` / `check_password_hash`
- **Session Check**: `before_request` hook checks `session['user_id']` for all routes except `/auth/login` and static files
- **Forgot Password**: Optional WhatsApp OTP (6-digit, 10-minute expiry) or national ID match

### 19.2 Authorization Model

```
session['user_id'] exists?
  ├── No → Redirect to /auth/login
  └── Yes → is_admin?
      ├── Yes → Allow all (bypass all checks)
      └── No → User.has_permission(perm_name)? 
          ├── Yes → Allow
          └── No → Block (403 or hide UI)
```

- **Granular Permissions**: Named `SystemPermission` records (e.g., `bulk_salary_manage`, `view_loans`, `COA_IMPORT`) assigned via M2M `user_system_permissions` table
- **Cash Account Access**: Additional M2M `user_cash_account_access` table restricts cash account visibility
- **Admin Superuser**: `is_admin = True` unconditionally bypasses all permission checks

### 19.3 CSRF

- All POST requests require valid CSRF token
- Token available to JavaScript via `<meta name="csrf-token" content="{{ csrf_token() }}">`

---

## 20. Configuration

| Configuration Source | Purpose | File |
|---|---|---|
| Flask App Config | SECRET_KEY, DATABASE_PATH, CSRF_TIMEOUT, ITEMS_PER_PAGE | `app/config.py` |
| HR Policy Constants (fallback) | Grace periods, overtime rates, absence multipliers | `config.py` (root) — may be stale per A-003 |
| HR Policy (runtime) | Dynamic values from `SystemSetting` DB table, read by `HRPolicy` metaclass | `core/policy/hr_policy.py` |
| System Settings UI | UI for viewing/editing SystemSetting records | `app/routes/settings.py` |
| User Preferences | Key-value per-user settings via JS API | `/settings/user/preferences` |

---

## 21. Constraints

| Constraint | Description |
|---|---|
| **SQLite Concurrency** | SQLite has limited concurrent write support. System designed for single-user/small-team local deployment (NFR-014). |
| **No Centralized Logging** | No logging framework configured beyond Flask flash messages (NFR-020). |
| **No External Auth API** | No JWT, API keys, or token-based authentication for external access (A-008). |
| **No Email Notifications** | No email system; WhatsApp is the only external notification (A-005). |
| **Schema Migration Fragility** | Auto-migration is add-only (ALTER TABLE). Cannot handle column drops or complex schema changes. |
| **EDB Connectivity** | System requires `.db` files to exist at expected relative paths from the project root. |
| **Browser Dependency** | UI built with CDN-dependent libraries; requires internet for first load or offline package. |

---

## 22. Risks

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Schema auto-migration failure on startup | System won't start | Low | Manual SQL intervention required; limited to add-only operations |
| Loss of manual attendance edits | Payroll inaccuracy | Low | `is_manual_override` flag prevents overwrite on re-import |
| Loan balance errors | Payroll errors | Low | Dynamic calculation with 120-iteration safety limit |
| WhatsApp API unavailability | Password recovery broken | Medium | Fallback to national ID verification |
| Dead code (`loans_old.py`, `config.py` staleness) | Developer confusion | Medium | Code cleanup required (out of scope for this document) |
| No test coverage for core modules | Regression bugs | High | Only treasury tests exist; payroll, attendance, loans, leaves untested |

---

## 23. Known Technical Debt

| Item | Description | Impact | Affected Files |
|---|---|---|---|
| Hardcoded leave defaults | 21/30/7/3 days hardcoded in Python, not configurable via UI | Cannot change leave balances without code change | `core/services/leave_service.py` |
| Dynamic HRPolicy metaclass | Reads from DB via Flask `current_app` — fails outside request context | Tight coupling to Flask, hard to test | `core/policy/hr_policy.py` |
| Add-only auto-migration | Can't handle drops, renames, or complex changes | Schema refactoring requires manual SQL | `core/db_manager.py` |
| Dead code duplication | `loans_old.py` not imported but defines same blueprint name | Developer confusion | `app/routes/loans_old.py` |
| Stale static files | JS files exist in both `static/js/` (root) and `app/static/js/` | Which one is authoritative? | Both dirs |
| Stale `config.py` constants | Root `config.py` HR constants may be stale vs `SystemSetting` DB values | Configuration confusion | `config.py` (root) |
| No test coverage | Only treasury tests in `tests/` | High regression risk | Entire codebase except treasury |
| Manufacturing DB independence | `operation_storage.py` is fully standalone (raw SQL, separate DB) | Code duplication for DB operations, no ORM benefits | `app/manufacturing_storage/operation_storage.py` |

---

## 24. Future Roadmap

The following items are potential future enhancements derived from the analysis:

| Item | Rationale | Suggested Priority |
|---|---|---|
| Configure leave balances via SystemSetting UI | Currently hardcoded in Python | High |
| Implement leaves approval workflow | Currently auto-approved only | Medium |
| Implement centralized logging | Flash messages are the only user-facing feedback | Medium |
| Add unit/integration tests for core modules | Currently only treasury tests exist | High |
| Clean up dead code (loans_old.py, stale JS files) | Reduce developer confusion | Low |
| Replace add-only auto-migration with proper migration tool (Alembic) | Schema management | Medium |
| Implement ERP service integration | Placeholder exists, ready for implementation | Low |
| Add token-based auth for API endpoints | API currently uses session-only auth | Low |
| Add employee salary history management UI | Currently backend-only logic | Low |
| Add public holiday management UI | Model exists, no dedicated route observed | Low |

---

## 25. Assumptions

| ID | Assumption |
|---|---|
| A-001 | `core/production.db` and `production_models.py` are legacy/unused. Routes for production entities not confirmed in blueprints. |
| A-002 | `app/routes/loans_old.py` is dead code (conflicting blueprint name, not imported). |
| A-003 | Root `config.py` static constants may be stale — `HRPolicy` metaclass reads from `SystemSetting` DB table at runtime. |
| A-004 | No centralized application logging framework exists beyond Flask defaults and flash messages. |
| A-005 | No email notification system exists. WhatsApp for password recovery is the only external notification. |
| A-006 | `ERPService` is a placeholder class only (`enabled = False`). No real ERP integration exists. |
| A-007 | Leaves are auto-approved on creation (status default = 'موافق عليها'). No PENDING/REJECTED workflow exposed in routes. |
| A-008 | Interactive API endpoints (`/api/interactive/`) rely on the same session-based auth as HTML routes. No token authentication exists. |
| A-009 | Static JS files in both `static/js/` (root) and `app/static/js/` are migration artifacts; root-level ones may be stale. |
| A-010 | No test suite exists for core business logic (payroll, attendance, loans, leaves). Only treasury route tests exist. |

---

## 26. Glossary

| Term | Definition |
|---|---|
| **AttendanceLog** | Raw imported fingerprint record (employee_code, timestamp, IN/OUT type) |
| **DailyRecord** | Processed attendance per employee per day (check_in, check_out, status, late_minutes, overtime) |
| **Blue** | 20+ Flask Blueprints — modular route groups, each with its own URL prefix |
| **COA** | Chart of Accounts — hierarchical account list for double-entry bookkeeping |
| **DailyRecord** | One record per employee per day, derived from AttendanceLogs, used in payroll |
| **ERP** | Enterprise Resource Planning — placeholder module; not yet integrated |
| **HBPolicy** | Class containing HR rules (grace periods, overtime rates, absence penalties) — reads from DB |
| **IsAdmin** | Superuser flag; bypasses all permission checks |
| **M2M** | Many-to-Many (SQLAlchemy relationship) |
| **National ID** | 14-digit Egyptian National ID — parsed for birthdate/age extraction |
| **OTP** | One-Time Password (6-digit, used for forgot password via WhatsApp) |
| **PayrollSummary** | Structured dict returned by PayrollCalculator with all line items |
| **RTL** | Right-to-Left (Arabic UI layout) |
| **SalaryHistory** | Automated record of all salary changes with effective dating for payroll resolution |
| **SystemPermission** | Named permission record (e.g., `view_loans`, `COA_IMPORT`) assigned to users |
| **transaction** | Financial/materials transaction within system (check, cash transfer, inventory movement) |
| **Error** | Error when the manufacturer receives finished goods |

---

## 27. Appendix

### 27.1 Source Documents

| Document | File | Description |
|---|---|---|
| Project Index | `project_index.md` | Project overview, technology stack, directory structure, entry points, important files, initial findings |
| Architecture | `architecture.md` | System architecture diagram, 20 blueprint modules, module dependency map, data flows, frontend structure, database interactions, external services, auth flow, startup sequence, assumptions |
| Features | `features.md` | 26 module descriptions, missing features (8 items), technical notes (10 items) |
| Data Model | `data_model.md` | 38+ business entities across 3 databases with fields, PKs, FKs, relationships, validation, defaults, lifecycle, business constraints, enums, integrity rules, cascade behavior, audit fields, data flows |
| Requirements | `requirements.md` | 54 functional requirements (FR-001 to FR-054), 20 non-functional (NFR-001 to NFR-020), 25 business rules (BR-001 to BR-025), 20 validation rules (VR-001 to VR-020), 10 assumptions (A-001 to A-010) |

### 27.2 Document Dependencies

```
project_index.md (foundation)
     ├── architecture.md (structure)
     │      └── features.md (capabilities)
     │             └── requirements.md (specifications)
     └── data_model.md (entities)
```

All five documents were analyzed to produce this PRD. Any information in this PRD that cannot be traced directly to those five documents is marked as an assumption.

### 27.3 Deleted Files/Dead Code Reference

| File | Reason |
|---|---|
| `app/routes/loans_old.py` | Conflicting blueprint name, not imported in `app/__init__.py` (A-002) |
| `static/js/` (root-level) | Likely stale migration artifacts (A-009) |
| `core/production.db` | Status unclear — may be legacy/unused (A-001) |
| `root/config.py` | Static constants potentially stale vs SystemSetting DB (A-003) |