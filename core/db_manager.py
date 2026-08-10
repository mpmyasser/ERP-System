from sqlalchemy import create_engine, inspect, text, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker, joinedload
from core.database_models import Base, Department, Employee, AttendanceLog, DailyRecord, Loan, EmployeeDocument, Bonus, DocumentType, Permission, Leave, SalaryHistory, BulkSalaryUpdateRequest
from core.treasury_models import CashAccount, BankAccount, CheckRecord
from core.auth_models import User, SystemPermission
from core.accounting_models import Account, CostCenter, JournalEntry, JournalItem
from core.commercial_models import Partner, Invoice, InvoiceItem, Warehouse, Product
from core.fabric_models import FabricRoll, ProductionMessage, FabricDesign
import os
from datetime import date, datetime, time

class DBManager:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), 'hr.db')
        
        self.db_path = os.path.abspath(db_path)
        self.engine = create_engine(f'sqlite:///{self.db_path}', echo=False)
        
        # --- ظ…ظ†ط·ظ‚ ط§ظ„طھط­ظ‚ظ‚ ظ…ظ† ظˆط¬ظˆط¯ ط§ظ„ط¹ظ…ظˆط¯ ---
        # ط§ظ„ظ‡ط¯ظپ: ط§ظ„طھط£ظƒط¯ ظ…ظ† ظˆط¬ظˆط¯ ط¹ظ…ظˆط¯ `excluded_months` ظپظٹ ط¬ط¯ظˆظ„ `loans`
        # ظ‡ط°ط§ ط§ظ„ط­ظ„ ظٹطھط¬ط§ظˆط² ط§ظ„ط­ط§ط¬ط© ط¥ظ„ظ‰ ظ…ظ„ظپط§طھ ط§ظ„طھط±ط­ظٹظ„ ط§ظ„طھظٹ ظ‚ط¯ طھظپط´ظ„ ط¨ط³ط¨ط¨ ظ‚ظٹظˆط¯ ط§ظ„ط¨ظٹط¦ط©
        try:
            with self.engine.connect() as connection:
                inspector = inspect(self.engine)
                # ط§ظ„طھط­ظ‚ظ‚ ط£ظˆظ„ط§ظ‹ ظ…ظ† ظˆط¬ظˆط¯ ط¬ط¯ظˆظ„ `loans`
                if inspector.has_table('loans'):
                    columns = inspector.get_columns('loans')
                    column_names = [c['name'] for c in columns]
                    # ط¥ط°ط§ ظƒط§ظ† ط§ظ„ط¹ظ…ظˆط¯ ط؛ظٹط± ظ…ظˆط¬ظˆط¯طŒ ظ‚ظ… ط¨ط¥ط¶ط§ظپطھظ‡
                    if 'excluded_months' not in column_names:
                        print("INFO: ظ„ظ… ظٹطھظ… ط§ظ„ط¹ط«ظˆط± ط¹ظ„ظ‰ ط¹ظ…ظˆط¯ 'excluded_months' ظپظٹ ط¬ط¯ظˆظ„ 'loans'. طھطھظ… ط§ظ„ط¢ظ† ط¥ط¶ط§ظپطھظ‡...")
                        connection.execute(text("ALTER TABLE loans ADD COLUMN excluded_months VARCHAR(255)"))
                        connection.commit()
                        print("INFO: طھظ…طھ ط¥ط¶ط§ظپط© ط¹ظ…ظˆط¯ 'excluded_months' ط¥ظ„ظ‰ ط¬ط¯ظˆظ„ 'loans' ط¨ظ†ط¬ط§ط­.")
                    
                    if 'status' not in column_names:
                        print("INFO: ظ„ظ… ظٹطھظ… ط§ظ„ط¹ط«ظˆط± ط¹ظ„ظ‰ ط¹ظ…ظˆط¯ 'status' ظپظٹ ط¬ط¯ظˆظ„ 'loans'. طھطھظ… ط§ظ„ط¢ظ† ط¥ط¶ط§ظپطھظ‡...")
                        connection.execute(text("ALTER TABLE loans ADD COLUMN status VARCHAR(20) DEFAULT 'Approved'"))
                        connection.commit()
                    
                    if 'cost_center' not in column_names:
                        print("INFO: ظ„ظ… ظٹطھظ… ط§ظ„ط¹ط«ظˆط± ط¹ظ„ظ‰ ط¹ظ…ظˆط¯ 'cost_center' ظپظٹ ط¬ط¯ظˆظ„ 'loans'. طھطھظ… ط§ظ„ط¢ظ† ط¥ط¶ط§ظپطھظ‡...")
                        connection.execute(text("ALTER TABLE loans ADD COLUMN cost_center VARCHAR(50)"))
                        connection.commit()

                    if 'disbursed_at' not in column_names:
                        connection.execute(text("ALTER TABLE loans ADD COLUMN disbursed_at DATETIME"))
                        connection.commit()

                    if 'disbursed_by' not in column_names:
                        connection.execute(text("ALTER TABLE loans ADD COLUMN disbursed_by INTEGER"))
                        connection.commit()

                # Ensure 'cost_centers' table exists
                if not inspector.has_table('cost_centers'):
                    print("INFO: ط¬ط¯ظˆظ„ 'cost_centers' ط؛ظٹط± ظ…ظˆط¬ظˆط¯. ظٹطھظ… ط¥ظ†ط´ط§ط¤ظ‡ ط§ظ„ط¢ظ†...")
                    from core.accounting_models import CostCenter
                    CostCenter.__table__.create(connection)
                    connection.commit()
                    print("INFO: طھظ… ط¥ظ†ط´ط§ط، ط¬ط¯ظˆظ„ 'cost_centers' ط¨ظ†ط¬ط§ط­.")

                # Ensure 'is_required' column exists on document_types (backwards compatibility)
                if inspector.has_table('document_types'):
                    columns_dt = inspector.get_columns('document_types')
                    col_names_dt = [c['name'] for c in columns_dt]
                    if 'is_required' not in col_names_dt:
                        print("INFO: ظ„ظ… ظٹطھظ… ط§ظ„ط¹ط«ظˆط± ط¹ظ„ظ‰ ط¹ظ…ظˆط¯ 'is_required' ظپظٹ ط¬ط¯ظˆظ„ 'document_types'. طھطھظ… ط§ظ„ط¢ظ† ط¥ط¶ط§ظپطھظ‡...")
                        connection.execute(text("ALTER TABLE document_types ADD COLUMN is_required BOOLEAN DEFAULT 1"))
                        connection.commit()
                        print("INFO: طھظ…طھ ط¥ط¶ط§ظپط© ط¹ظ…ظˆط¯ 'is_required' ط¥ظ„ظ‰ ط¬ط¯ظˆظ„ 'document_types' ط¨ظ†ط¬ط§ط­.")

                # Ensure 'display_order' exists for Departments
                if inspector.has_table('departments'):
                    columns_dept = inspector.get_columns('departments')
                    col_names_dept = [c['name'] for c in columns_dept]
                    if 'display_order' not in col_names_dept:
                        connection.execute(text("ALTER TABLE departments ADD COLUMN display_order INTEGER DEFAULT 0"))
                        connection.commit()

                # Ensure 'display_order' exists for Cost Centers
                if inspector.has_table('cost_centers'):
                    columns_cc = inspector.get_columns('cost_centers')
                    col_names_cc = [c['name'] for c in columns_cc]
                    if 'display_order' not in col_names_cc:
                        connection.execute(text("ALTER TABLE cost_centers ADD COLUMN display_order INTEGER DEFAULT 0"))
                        connection.commit()

                # Ensure 'display_order' exists for Accounts
                if inspector.has_table('accounts'):
                    columns_acc = inspector.get_columns('accounts')
                    col_names_acc = [c['name'] for c in columns_acc]
                    if 'display_order' not in col_names_acc:
                        connection.execute(text("ALTER TABLE accounts ADD COLUMN display_order INTEGER DEFAULT 0"))
                        connection.commit()

                # Ensure 'display_order' exists for Cash Accounts
                if inspector.has_table('cash_accounts'):
                    columns_ca = inspector.get_columns('cash_accounts')
                    col_names_ca = [c['name'] for c in columns_ca]
                    if 'display_order' not in col_names_ca:
                        connection.execute(text("ALTER TABLE cash_accounts ADD COLUMN display_order INTEGER DEFAULT 0"))
                        connection.commit()

                # Ensure 'display_order' exists for Bank Accounts
                if inspector.has_table('bank_accounts'):
                    columns_ba = inspector.get_columns('bank_accounts')
                    col_names_ba = [c['name'] for c in columns_ba]
                    if 'display_order' not in col_names_ba:
                        connection.execute(text("ALTER TABLE bank_accounts ADD COLUMN display_order INTEGER DEFAULT 0"))
                        connection.commit()

                # Ensure 'insurance_start_date' and 'insurance_end_date' exist for Employees
                if inspector.has_table('employees'):
                    columns_emp = inspector.get_columns('employees')
                    col_names_emp = [c['name'] for c in columns_emp]
                    
                    if 'insurance_start_date' not in col_names_emp:
                        print("INFO: ظ„ظ… ظٹطھظ… ط§ظ„ط¹ط«ظˆط± ط¹ظ„ظ‰ ط¹ظ…ظˆط¯ 'insurance_start_date' ظپظٹ ط¬ط¯ظˆظ„ 'employees'. طھطھظ… ط§ظ„ط¢ظ† ط¥ط¶ط§ظپطھظ‡...")
                        connection.execute(text("ALTER TABLE employees ADD COLUMN insurance_start_date DATE"))
                        connection.commit()
                        print("INFO: طھظ…طھ ط¥ط¶ط§ظپط© ط¹ظ…ظˆط¯ 'insurance_start_date' ط¨ظ†ط¬ط§ط­.")

                    if 'insurance_end_date' not in col_names_emp:
                        print("INFO: ظ„ظ… ظٹطھظ… ط§ظ„ط¹ط«ظˆط± ط¹ظ„ظ‰ ط¹ظ…ظˆط¯ 'insurance_end_date' ظپظٹ ط¬ط¯ظˆظ„ 'employees'. طھطھظ… ط§ظ„ط¢ظ† ط¥ط¶ط§ظپطھظ‡...")
                        connection.execute(text("ALTER TABLE employees ADD COLUMN insurance_end_date DATE"))
                        connection.commit()
                        print("INFO: طھظ…طھ ط¥ط¶ط§ظپط© ط¹ظ…ظˆط¯ 'insurance_end_date' ط¨ظ†ط¬ط§ط­.")

                    if 'salary_updated_at' not in col_names_emp:
                        print("INFO: ظ„ظ… ظٹطھظ… ط§ظ„ط¹ط«ظˆط± ط¹ظ„ظ‰ ط¹ظ…ظˆط¯ 'salary_updated_at' ظپظٹ ط¬ط¯ظˆظ„ 'employees'. طھطھظ… ط§ظ„ط¢ظ† ط¥ط¶ط§ظپطھظ‡...")
                        connection.execute(text("ALTER TABLE employees ADD COLUMN salary_updated_at DATETIME"))
                        connection.commit()
                        print("INFO: طھظ…طھ ط¥ط¶ط§ظپط© ط¹ظ…ظˆط¯ 'salary_updated_at' ط¨ظ†ط¬ط§ط­.")

                # Ensure manual override flag exists for DailyRecord
                if inspector.has_table('daily_records'):
                    columns_dr = inspector.get_columns('daily_records')
                    col_names_dr = [c['name'] for c in columns_dr]
                    if 'is_manual_override' not in col_names_dr:
                        connection.execute(text("ALTER TABLE daily_records ADD COLUMN is_manual_override BOOLEAN DEFAULT 0"))
                        connection.commit()
                # Ensure 'effective_date' exists for SalaryHistory
                if inspector.has_table('salary_history'):
                    columns_hist = inspector.get_columns('salary_history')
                    col_names_hist = [c['name'] for c in columns_hist]
                    
                    if 'effective_date' not in col_names_hist:
                        print("INFO: ظ„ظ… ظٹطھظ… ط§ظ„ط¹ط«ظˆط± ط¹ظ„ظ‰ ط¹ظ…ظˆط¯ 'effective_date' ظپظٹ ط¬ط¯ظˆظ„ 'salary_history'. ظٹطھظ… ط§ظ„ط¢ظ† ط¥ط¶ط§ظپطھظ‡...")
                        connection.execute(text("ALTER TABLE salary_history ADD COLUMN effective_date DATETIME"))
                        connection.commit()
                        print("INFO: طھظ…طھ ط¥ط¶ط§ظپط© ط¹ظ…ظˆط¯ 'effective_date' ط¨ظ†ط¬ط§ط­.")

        except Exception as e:
            # ظپظٹ ط­ط§ظ„ط© ط­ط¯ظˆط« ط£ظٹ ط®ط·ط£طŒ ظٹطھظ… ط·ط¨ط§ط¹طھظ‡ ظ„ظ„ظ…ط³ط§ط¹ط¯ط© ظپظٹ ط§ظ„طھط´ط®ظٹطµ
            print(f"ERROR: ظپط´ظ„ ط§ظ„طھط­ظ‚ظ‚: {e}")

        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)

    def get_session(self):
        return self.Session()

    def add_department(self, **kwargs):
        session = self.get_session()
        try:
            dept = Department(**kwargs)
            session.add(dept)
            session.commit()
            return dept
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_departments(self):
        session = self.get_session()
        try:
            return session.query(Department).options(joinedload(Department.employees)).order_by(Department.display_order).all()
        finally:
            session.close()

    def get_department_by_id(self, dept_id):
        """Get department by ID with employees loaded"""
        session = self.get_session()
        try:
            return session.query(Department).options(joinedload(Department.employees)).filter_by(id=dept_id).first()
        finally:
            session.close()

    def update_department(self, dept_id, **kwargs):
        session = self.get_session()
        try:
            dept = session.query(Department).filter_by(id=dept_id).first()
            if dept:
                for key, value in kwargs.items():
                    if hasattr(dept, key):
                        setattr(dept, key, value)
                session.commit()
                return dept
            return None
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_department(self, dept_id):
        session = self.get_session()
        try:
            dept = session.query(Department).options(joinedload(Department.employees)).filter_by(id=dept_id).first()
            if dept:
                # Check for employees
                if dept.employees:
                    raise Exception("ظ„ط§ ظٹظ…ظƒظ† ط­ط°ظپ ط§ظ„ظ‚ط³ظ… ظ„ظˆط¬ظˆط¯ ظ…ظˆط¸ظپظٹظ† ظ…ط³ط¬ظ„ظٹظ† ط¨ظ‡")
                session.delete(dept)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def add_employee(self, **kwargs):
        session = self.get_session()
        try:
            emp = Employee(**kwargs)
            session.add(emp)
            session.commit()
            return emp
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def bulk_update_salaries(self, updates, effective_date, idempotency_key):
        """
        Update multiple employee salaries at once.
        updates: list of dicts [{'employee_id': 1, 'basic_salary': 5000}, ...]
        effective_date: datetime for the change to take effect
        idempotency_key: UUID generated by the client for this save request

        Returns True when the request is processed and False when the same
        request was already committed.
        """
        session = self.get_session()
        try:
            session.add(BulkSalaryUpdateRequest(idempotency_key=idempotency_key))
            session.flush()
            self._apply_bulk_salary_changes(session, updates, effective_date)
            session.commit()
            return True
        except IntegrityError:
            session.rollback()
            if session.query(BulkSalaryUpdateRequest).filter_by(idempotency_key=idempotency_key).first():
                return False
            raise
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _apply_bulk_salary_changes(self, session, updates, effective_date):
        for salary_update in updates:
            self._apply_bulk_salary_change(session, salary_update, effective_date)

    def _apply_bulk_salary_change(self, session, salary_update, effective_date):
        employee_id = salary_update.get('employee_id')
        new_salary = salary_update.get('basic_salary')
        if not employee_id or new_salary is None:
            return

        employee = session.query(Employee).filter_by(id=employee_id).first()
        if not employee:
            return

        effective_datetime = self._effective_salary_datetime(effective_date)
        if effective_datetime:
            employee._effective_date = effective_datetime
        employee._change_reason = "تعديل جماعي للمرتبات"
        new_salary_value = float(new_salary)

        if float(employee.basic_salary or 0) == new_salary_value:
            self._record_effective_salary_change(session, employee, new_salary_value, effective_datetime)
            return

        employee.basic_salary = new_salary_value

    @staticmethod
    def _effective_salary_datetime(effective_date):
        if isinstance(effective_date, date) and not isinstance(effective_date, datetime):
            return datetime.combine(effective_date, datetime.min.time())
        return effective_date

    @staticmethod
    def _record_effective_salary_change(session, employee, new_salary, effective_date):
        if not effective_date:
            return

        previous_change = session.query(SalaryHistory).filter(
            SalaryHistory.employee_id == employee.id,
            SalaryHistory.effective_date <= effective_date
        ).order_by(
            SalaryHistory.effective_date.desc(),
            SalaryHistory.change_date.desc()
        ).first()

        if not previous_change or float(previous_change.new_salary) == new_salary:
            return

        session.add(SalaryHistory(
            employee=employee,
            old_salary=float(previous_change.new_salary),
            new_salary=new_salary,
            salary_change=new_salary - float(previous_change.new_salary),
            change_date=datetime.now(),
            effective_date=effective_date,
            reason="تعديل جماعي للمرتبات"
        ))
        employee.salary_updated_at = datetime.now()
    def attach_effective_salaries(self, employees, target_date=None):
        """
        Attach effective_salary to each employee object based on SalaryHistory and target_date.
        If no history exists, fallback to current basic_salary.
        """
        if not employees:
            return employees

        if target_date is None:
            target_date = date.today()

        target_dt = datetime.combine(target_date, time.max)

        emp_ids = [e.id for e in employees if getattr(e, 'id', None)]
        if not emp_ids:
            return employees

        session = self.get_session()
        try:
            subq = session.query(
                SalaryHistory.employee_id.label('emp_id'),
                func.max(SalaryHistory.effective_date).label('max_eff')
            ).filter(
                SalaryHistory.employee_id.in_(emp_ids),
                SalaryHistory.effective_date <= target_dt
            ).group_by(SalaryHistory.employee_id).subquery()

            rows = session.query(
                SalaryHistory.employee_id,
                SalaryHistory.new_salary,
                SalaryHistory.effective_date
            ).join(
                subq,
                (SalaryHistory.employee_id == subq.c.emp_id) &
                (SalaryHistory.effective_date == subq.c.max_eff)
            ).all()

            effective_map = {r.employee_id: (r.new_salary, r.effective_date) for r in rows}
        finally:
            session.close()

        for emp in employees:
            if emp.id in effective_map:
                emp.effective_salary = effective_map[emp.id][0]
                emp.effective_salary_date = effective_map[emp.id][1]
            else:
                emp.effective_salary = emp.basic_salary or 0
                emp.effective_salary_date = None

        return employees

    def delete_salary_history_record(self, record_id):
        """
        ط­ط°ظپ ط³ط¬ظ„ ظ…ط­ط¯ط¯ ظ…ظ† طھط§ط±ظٹط® ط§ظ„ط±ظˆط§طھط¨.
        ط¥ط°ط§ ظƒط§ظ† ط§ظ„ط³ط¬ظ„ ط§ظ„ظ…ط­ط°ظˆظپ ظ‡ظˆ ط§ظ„ط£ط­ط¯ط«طŒ ظٹطھظ… ط¥ط±ط¬ط§ط¹ ط±ط§طھط¨ ط§ظ„ظ…ظˆط¸ظپ ظ„ظ„ط­ط§ظ„ط© ط§ظ„طھظٹ طھط³ط¨ظ‚ظ‡.
        """
        session = self.get_session()
        try:
            record = session.query(SalaryHistory).filter_by(id=record_id).first()
            if not record:
                return False, "ط§ظ„ط³ط¬ظ„ ط؛ظٹط± ظ…ظˆط¬ظˆط¯"
            
            emp = session.query(Employee).filter_by(id=record.employee_id).first()
            
            # ط§ظ„طھط£ظƒط¯ ظ…ظ…ط§ ط¥ط°ط§ ظƒط§ظ† ظ‡ط°ط§ ظ‡ظˆ ط§ظ„ط³ط¬ظ„ ط§ظ„ط£ط­ط¯ط«
            latest = session.query(SalaryHistory).filter_by(employee_id=emp.id).order_by(SalaryHistory.effective_date.desc()).first()
            
            if latest and latest.id == record.id:
                # ط¥ط°ط§ ظƒط§ظ† ظ‡ظˆ ط§ظ„ط£ط­ط¯ط«طŒ ظ†ط­طھط§ط¬ ظ„ظ„ط¨ط­ط« ط¹ظ† ط§ظ„ط³ط¬ظ„ ط§ظ„ط°ظٹ ظ‚ط¨ظ„ظ‡ (ط¥ظ† ظˆط¬ط¯) ظ„ط¥ط±ط¬ط§ط¹ ط§ظ„ط±ط§طھط¨ ط¥ظ„ظٹظ‡
                previous = session.query(SalaryHistory).filter(
                    SalaryHistory.employee_id == emp.id,
                    SalaryHistory.id != record.id
                ).order_by(SalaryHistory.effective_date.desc()).first()
                
                emp._skip_audit = True
                if previous:
                    emp.basic_salary = previous.new_salary
                    
                    # ط§ظ„طھط­ظ‚ظ‚ ظ…ظ…ط§ ط¥ط°ط§ ظƒط§ظ† ط§ظ„ط³ط¬ظ„ ط§ظ„ظ…طھط¨ظ‚ظٹ ظ‡ظˆ ط³ط¬ظ„ ظˆط­ظٹط¯ (ط؛ط§ظ„ط¨ط§ظ‹ ط³ظٹظƒظˆظ† ط³ط¬ظ„ ط§ظ„طھط¹ظٹظٹظ†)
                    # ط¥ط°ط§ ظƒط§ظ† ظ‡ظˆ ط§ظ„ظˆط­ظٹط¯طŒ ظ†ظ‚ظˆظ… ط¨طھطµظپظٹط± طھط§ط±ظٹط® ط§ظ„طھط­ط¯ظٹط«
                    remaining_count = session.query(SalaryHistory).filter(
                        SalaryHistory.employee_id == emp.id,
                        SalaryHistory.id != record.id
                    ).count()
                    
                    if remaining_count <= 1:
                        emp.salary_updated_at = None
                    else:
                        emp.salary_updated_at = previous.change_date
                else:
                    emp.basic_salary = record.old_salary
                    emp.salary_updated_at = None
            
            session.delete(record)
            session.commit()
            return True, "طھظ… ط­ط°ظپ ط§ظ„ط³ط¬ظ„ ظˆطھط­ط¯ظٹط« ط§ظ„ط¨ظٹط§ظ†ط§طھ ط¨ظ†ط¬ط§ط­"
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

    def get_all_employees(self, only_active=False):
        session = self.get_session()
        try:
            query = session.query(Employee).options(
                joinedload(Employee.department),
                joinedload(Employee.salary_history)
            )
            if only_active:
                query = query.filter(Employee.is_active == True)
            return query.order_by(Employee.code.asc()).all()
        finally:
            session.close()

    def get_employees_optimized(self, only_active=False, department_ids=None, job_title=None, search=None, 
                                load_full=False, load_salary_history=False):
        """
        جلب الموظفين بطريقة محسنة مع دعم الفلترة في SQL
        
        Args:
            only_active (bool): جلب النشطين فقط
            department_ids (list): قائمة بمعرفات الأقسام
            job_title (str): المسمى الوظيفي
            search (str): نص البحث (اسم أو كود)
            load_full (bool): إذا كان False، يحمل الحقول الأساسية فقط (Selective Fetching)
            load_salary_history (bool): تحميل تاريخ الرواتب
        """
        session = self.get_session()
        try:
            query = session.query(Employee)
            
            # Selective Fetching logic
            if not load_full:
                from sqlalchemy.orm import load_only
                # Load only the fields needed by the employees list view/template
                # so that accessing them after the session is closed does not trigger
                # deferred loads (which would cause DetachedInstanceError).
                query = query.options(
                    load_only(
                        Employee.id,
                        Employee.code,
                        Employee.name,
                        Employee.job_title,
                        Employee.department_id,
                        Employee.basic_salary,
                        Employee.is_active,
                        Employee.hire_date,
                        Employee.is_insured,
                        Employee.regularity_incentive,
                        Employee.overtime_allowed,
                        Employee.salary_updated_at,
                        Employee.daily_work_hours,
                    )
                )
            
            # Eager Loading
            options = [joinedload(Employee.department)]
            if load_salary_history:
                options.append(joinedload(Employee.salary_history))
            query = query.options(*options)
            
            # SQL Filtering
            if only_active:
                query = query.filter(Employee.is_active == True)
            
            if department_ids:
                # Ensure ids are integers
                ids = [int(i) for i in department_ids if str(i).isdigit()]
                if ids:
                    query = query.filter(Employee.department_id.in_(ids))
            
            if job_title:
                query = query.filter(Employee.job_title == job_title)
            
            if search:
                search_filter = f"%{search}%"
                query = query.filter(
                    (Employee.name.like(search_filter)) | 
                    (Employee.code.like(search_filter))
                )
            
            return query.order_by(Employee.code.asc()).all()
        finally:
            session.close()

    # --- User settings CRUD (central key-value store) ---
    def get_user_setting(self, user_id, key, default=None):
        session = self.get_session()
        try:
            from core.auth_models import UserPreference
            rec = session.query(UserPreference).filter_by(user_id=user_id, key=key).first()
            if not rec or rec.value is None:
                return default
            try:
                import json
                return json.loads(rec.value)
            except Exception:
                return rec.value
        finally:
            session.close()

    def get_user_settings(self, user_id, prefix=None):
        session = self.get_session()
        try:
            from core.auth_models import UserPreference
            q = session.query(UserPreference).filter_by(user_id=user_id)
            if prefix:
                q = q.filter(UserPreference.key.like(f"{prefix}%"))

            out = {}
            import json
            for rec in q.all():
                if rec.value is None:
                    out[rec.key] = None
                    continue
                try:
                    out[rec.key] = json.loads(rec.value)
                except Exception:
                    out[rec.key] = rec.value
            return out
        finally:
            session.close()

    def set_user_setting(self, user_id, key, value):
        session = self.get_session()
        try:
            from core.auth_models import UserPreference
            import json

            rec = session.query(UserPreference).filter_by(user_id=user_id, key=key).first()
            payload = json.dumps(value, ensure_ascii=False)

            if not rec:
                rec = UserPreference(user_id=user_id, key=key, value=payload)
                session.add(rec)
            else:
                rec.value = payload

            session.commit()
            return rec
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def set_user_settings(self, user_id, settings_dict):
        session = self.get_session()
        try:
            from core.auth_models import UserPreference
            import json

            if not settings_dict:
                return True

            keys = list(settings_dict.keys())
            existing = {
                rec.key: rec
                for rec in session.query(UserPreference).filter(
                    UserPreference.user_id == user_id,
                    UserPreference.key.in_(keys)
                ).all()
            }

            for key, value in settings_dict.items():
                payload = json.dumps(value, ensure_ascii=False)
                if key in existing:
                    existing[key].value = payload
                else:
                    session.add(UserPreference(user_id=user_id, key=key, value=payload))

            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete_user_setting(self, user_id, key):
        session = self.get_session()
        try:
            from core.auth_models import UserPreference
            rec = session.query(UserPreference).filter_by(user_id=user_id, key=key).first()
            if rec:
                session.delete(rec)
                session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete_user_settings(self, user_id, keys):
        session = self.get_session()
        try:
            from core.auth_models import UserPreference
            if not keys:
                return True
            session.query(UserPreference).filter(
                UserPreference.user_id == user_id,
                UserPreference.key.in_(keys)
            ).delete(synchronize_session=False)
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # --- Compatibility wrappers for table width settings ---
    def _table_setting_key(self, page, table_key=None):
        normalized_page = page or ''
        normalized_table = table_key if table_key is not None else '__default__'
        return f"table_widths:{normalized_page}:{normalized_table}"

    def get_user_table_setting(self, user_id, page, table_key=None):
        from types import SimpleNamespace
        key = self._table_setting_key(page, table_key)
        value = self.get_user_setting(user_id, key)
        if value is None:
            return None

        try:
            import json
            widths_json = json.dumps(value, ensure_ascii=False)
        except Exception:
            widths_json = None
        return SimpleNamespace(widths=widths_json)

    def save_user_table_setting(self, user_id, page, table_key, widths_json):
        import json
        key = self._table_setting_key(page, table_key)
        parsed = widths_json
        if isinstance(widths_json, str):
            try:
                parsed = json.loads(widths_json)
            except Exception:
                parsed = widths_json
        self.set_user_setting(user_id, key, parsed)
        return True

    def get_employee_by_id(self, emp_id):
        session = self.get_session()
        try:
            return session.query(Employee).options(
                joinedload(Employee.department),
                joinedload(Employee.salary_history)
            ).filter_by(id=emp_id).first()
        finally:
            session.close()

    def get_unique_job_titles(self):
        session = self.get_session()
        try:
            # Get distinct job titles that are not None/empty
            titles = session.query(Employee.job_title).distinct().filter(Employee.job_title != None, Employee.job_title != '').all()
            return [t[0] for t in titles]
        except Exception as e:
            print(f"Error getting job titles: {e}")
            return []
        finally:
            session.close()

    def update_employee(self, emp_id, **kwargs):
        session = self.get_session()
        try:
            emp = session.query(Employee).filter_by(id=emp_id).first()
            if emp:
                if 'code' in kwargs and kwargs['code'] != emp.code:
                    existing = session.query(Employee).filter(
                        (Employee.code == kwargs['code']) & (Employee.id != emp_id)
                    ).first()
                    if existing:
                        raise Exception(f"ط§ظ„ظƒظˆط¯ {kwargs['code']} ظ…ط³طھط®ط¯ظ… ط¨ط§ظ„ظپط¹ظ„ ظ…ظ† ظ‚ط¨ظ„ ظ…ظˆط¸ظپ ط¢ط®ط±")
                
                for key, value in kwargs.items():
                    if hasattr(emp, key):
                        setattr(emp, key, value)
                session.commit()
                return emp
            return None
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_employee(self, emp_id):
        session = self.get_session()
        try:
            emp = session.query(Employee).filter_by(id=emp_id).first()
            if emp:
                session.delete(emp)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def search_employees(self, query):
        session = self.get_session()
        try:
            # Search by name or code
            return session.query(Employee).options(joinedload(Employee.department)).filter(
                (Employee.name.like(f"%{query}%")) | (Employee.code.like(f"%{query}%"))
            ).order_by(Employee.code.asc()).all()
        finally:
            session.close()

    def get_next_employee_code(self):
        """
        Get the next available employee code.
        Assumes codes are numeric strings.
        """
        session = self.get_session()
        try:
            from sqlalchemy import cast, Integer
            # فلترة الأكواد الرقمية بالكامل فقط (مطابق لسلوك c.isdigit() السابق)،
            # وحساب الأكبر عبر SQL MAX بدل تحميل كل الأكواد إلى الذاكرة
            max_code = session.query(func.max(cast(Employee.code, Integer))).filter(
                Employee.code.isnot(None),
                Employee.code != '',
                ~Employee.code.op('GLOB')('*[^0-9]*')
            ).scalar()

            if max_code is None:
                return "1"

            return str(max_code + 1)
        except Exception:
            return ""
        finally:
            session.close()

    def check_employee_exists(self, code, national_id=None):
        """Check if employee exists by code or national_id. Returns dict with details."""
        session = self.get_session()
        result = {'exists': False, 'code_exists': False, 'nid_exists': False}
        try:
            if code:
                emp_code = session.query(Employee).filter(Employee.code == code).first()
                if emp_code:
                    result['exists'] = True
                    result['code_exists'] = True
            
            if national_id:
                emp_nid = session.query(Employee).filter(Employee.national_id == national_id).first()
                if emp_nid:
                    result['exists'] = True
                    result['nid_exists'] = True
            
            return result
        finally:
            session.close()

    def get_next_employee(self, current_id):
        session = self.get_session()
        try:
            return session.query(Employee).options(joinedload(Employee.department)).filter(Employee.id > current_id).order_by(Employee.id.asc()).first()
        finally:
            session.close()

    def get_previous_employee(self, current_id):
        session = self.get_session()
        try:
            return session.query(Employee).options(joinedload(Employee.department)).filter(Employee.id < current_id).order_by(Employee.id.desc()).first()
        finally:
            session.close()

    def add_attendance_log(self, employee_code, timestamp, type):
        session = self.get_session()
        try:
            log = AttendanceLog(employee_code=employee_code, timestamp=timestamp, type=type)
            session.add(log)
            session.commit()
            return log
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_daily_records_by_date(self, date):
        session = self.get_session()
        try:
            return session.query(DailyRecord).filter_by(date=date).all()
        finally:
            session.close()

    def add_loan(self, employee_id, amount, loan_type, number_of_installments, date_issued=None, excluded_months=None, status='Pending', cost_center=None):
        # Force correct type based on installments
        if number_of_installments == 1:
            loan_type = 'temporary'
        elif number_of_installments > 1:
            loan_type = 'permanent'
            
        session = self.get_session()
        try:
            loan = Loan(
                employee_id=employee_id, 
                amount=amount, 
                type=loan_type, 
                installments_count=number_of_installments,
                date=date_issued,
                excluded_months=excluded_months,
                remaining_balance=amount,
                status=status,
                cost_center=cost_center
            )
            session.add(loan)
            session.commit()
            return loan
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def check_loan_exists(self, employee_id, date_issued):
        """Check if a loan already exists for an employee on a specific date"""
        session = self.get_session()
        try:
            return session.query(Loan).filter(
                Loan.employee_id == employee_id,
                Loan.date == date_issued
            ).first() is not None
        finally:
            session.close()

    def check_permission_exists(self, employee_id, date):
        """Check if a permission already exists for an employee on a specific date"""
        session = self.get_session()
        try:
            return session.query(Permission).filter(
                Permission.employee_id == employee_id,
                Permission.date == date
            ).first() is not None
        finally:
            session.close()

    def check_penalty_bonus_exists(self, employee_id, date, type):
        """Check if a penalty/bonus already exists for an employee on a specific date"""
        session = self.get_session()
        try:
            from database_models import PenaltyBonus
            return session.query(PenaltyBonus).filter(
                PenaltyBonus.employee_id == employee_id,
                PenaltyBonus.date == date,
                PenaltyBonus.type == type
            ).first() is not None
        finally:
            session.close()

    def check_bonus_exists(self, employee_id, date_awarded):
        """Check if a bonus already exists for an employee on a specific date"""
        session = self.get_session()
        try:
            from database_models import Bonus
            return session.query(Bonus).filter(
                Bonus.employee_id == employee_id,
                Bonus.date_awarded == date_awarded
            ).first() is not None
        finally:
            session.close()

    def check_attendance_exists(self, employee_id, date):
        """Check if attendance already exists for an employee on a specific date"""
        session = self.get_session()
        try:
            from database_models import DailyRecord
            return session.query(DailyRecord).filter(
                DailyRecord.employee_id == employee_id,
                DailyRecord.date == date
            ).first() is not None
        finally:
            session.close()

    def check_leave_exists(self, employee_id, start_date):
        """Check if a leave already exists for an employee starting on a specific date"""
        session = self.get_session()
        try:
            return session.query(Leave).filter(
                Leave.employee_id == employee_id,
                Leave.start_date == start_date
            ).first() is not None
        finally:
            session.close()

    def search_loans(self, date_from=None, date_to=None, department_ids=None, dept_filter_mode='include', code=None, status=None):
        """Search loans with filters including multi-department include/exclude and status"""
        session = self.get_session()
        try:
            from utils.helpers import parse_date_compact
            
            query = session.query(Loan).join(Employee).options(joinedload(Loan.employee).joinedload(Employee.department))
            
            if status:
                query = query.filter(Loan.status == status)
            
            # Parse date filters
            if date_from:
                parsed_date_from = parse_date_compact(date_from)
                if parsed_date_from:
                    query = query.filter(Loan.date >= parsed_date_from)
                    
            if date_to:
                parsed_date_to = parse_date_compact(date_to)
                if parsed_date_to:
                    query = query.filter(Loan.date <= parsed_date_to)
            
            if department_ids and len(department_ids) > 0:
                if dept_filter_mode == 'exclude':
                    query = query.filter(Employee.department_id.notin_(department_ids))
                else: # default include
                    query = query.filter(Employee.department_id.in_(department_ids))
            
            if code:
                from sqlalchemy import or_
                query = query.filter(or_(
                    Employee.code == code,
                    Employee.name.ilike(f"%{code}%")
                ))
                
            # Always exclude inactive employees from loan reports as per user request
            query = query.filter(Employee.is_active == True)
                
            return query.order_by(Employee.code.asc(), Loan.date.asc(), Loan.id.asc()).all()
        finally:
            session.close()


    # ===== Penalty Functions (دوال العقوبات) =====

    @property
    def _penalty_service(self):
        """Lazy-initialized `PenaltyService` bound to this manager's session
        factory, following the same pattern as `_audit_log_service` (P1-C02
        slice, 2026-08-10). Instantiated on first access and cached on the
        instance via a private attribute so subsequent calls reuse it.
        """
        svc = getattr(self, '_penalty_service_instance', None)
        if svc is None:
            from core.services.penalty_service import PenaltyService
            svc = PenaltyService(self.Session)
            self._penalty_service_instance = svc
        return svc

    def add_penalty_bonus(self, employee_id, date, type, amount, reason):
        """Compatibility wrapper delegating to `PenaltyService.add_penalty_bonus`."""
        return self._penalty_service.add_penalty_bonus(employee_id, date, type, amount, reason)

    def get_employee_attendance(self, employee_id):
        session = self.get_session()
        try:
            return session.query(DailyRecord).filter_by(employee_id=employee_id).options(joinedload(DailyRecord.employee)).order_by(DailyRecord.date.desc()).all()
        finally:
            session.close()

    def get_penalty_by_id(self, penalty_id):
        """Compatibility wrapper delegating to `PenaltyService.get_penalty_by_id`."""
        return self._penalty_service.get_penalty_by_id(penalty_id)

    def update_loan(self, loan_id, **kwargs):
        """Update loan"""
        session = self.get_session()
        try:
            loan = session.query(Loan).filter_by(id=loan_id).first()
            if loan:
                for key, value in kwargs.items():
                    if hasattr(loan, key):
                        setattr(loan, key, value)
                
                # Force correct type based on installments if updated
                if loan.installments_count == 1:
                    loan.type = 'temporary'
                elif loan.installments_count > 1:
                    loan.type = 'permanent'
                session.commit()
                return loan
            return None
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_all_loans(self):
        """Get all loans with employee data"""
        session = self.get_session()
        try:
            return session.query(Loan).join(Employee).options(
                joinedload(Loan.employee).joinedload(Employee.department)
            ).order_by(Employee.code.asc(), Loan.date.asc(), Loan.id.asc()).all()
        finally:
            session.close()

    def get_loan_by_id(self, loan_id):
        """Get loan by ID"""
        session = self.get_session()
        try:
            return session.query(Loan).options(joinedload(Loan.employee).joinedload(Employee.department)).filter_by(id=loan_id).first()
        finally:
            session.close()

    def get_all_penalties(self):
        """Compatibility wrapper delegating to `PenaltyService.get_all_penalties`."""
        return self._penalty_service.get_all_penalties()

    def add_penalty(self, employee_id, penalty_type, amount, reason, date=None):
        """Compatibility wrapper delegating to `PenaltyService.add_penalty`."""
        return self._penalty_service.add_penalty(employee_id, penalty_type, amount, reason, date=date)
    
    # =====================================
    # Permissions Methods
    # =====================================
    
    def get_all_permissions(self):
        """Get all permissions"""
        session = self.get_session()
        try:
            return session.query(Permission).join(Employee).order_by(
                Employee.code.asc(),
                Permission.date.asc(),
                Permission.id.asc()
            ).all()
        finally:
            session.close()
    
    def add_permission(self, employee_id, date, from_time, to_time, reason=None, is_paid=False):
        """Add a new permission"""
        session = self.get_session()
        try:
            from datetime import datetime
            
            # Convert time strings to time objects if needed
            if isinstance(from_time, str):
                from_time = datetime.strptime(from_time, '%H:%M').time()
            if isinstance(to_time, str):
                to_time = datetime.strptime(to_time, '%H:%M').time()
            
            permission = Permission(
                employee_id=employee_id,
                date=date,
                from_time=from_time,
                to_time=to_time,
                reason=reason,
                is_paid=is_paid
            )
            session.add(permission)
            session.commit()
            return permission
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def delete_permission(self, permission_id):
        """Delete a permission"""
        session = self.get_session()
        try:
            permission = session.query(Permission).filter_by(id=permission_id).first()
            if permission:
                session.delete(permission)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_permission_by_id(self, permission_id):
        """Get a permission by ID"""
        session = self.get_session()
        try:
            from sqlalchemy.orm import joinedload
            return session.query(Permission).options(joinedload(Permission.employee)).filter_by(id=permission_id).first()
        finally:
            session.close()

    def update_permission(self, permission_id, **kwargs):
        """Update an existing permission"""
        session = self.get_session()
        try:
            from datetime import datetime
            
            permission = session.query(Permission).filter_by(id=permission_id).first()
            if not permission:
                return None
            
            for key, value in kwargs.items():
                if hasattr(permission, key):
                    # Handle time strings if they are passed as kwargs
                    if key in ['from_time', 'to_time'] and isinstance(value, str):
                        value = datetime.strptime(value, '%H:%M').time()
                    setattr(permission, key, value)
            
            session.commit()
            return permission
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def delete_penalty(self, penalty_id):
        """Compatibility wrapper delegating to `PenaltyService.delete_penalty`."""
        return self._penalty_service.delete_penalty(penalty_id)
    
    def delete_loan(self, loan_id):
        """Delete a loan"""
        session = self.get_session()
        try:
            loan = session.query(Loan).filter_by(id=loan_id).first()
            if loan:
                session.delete(loan)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_attendance_by_date(self, date):
        """Get attendance records for a specific date"""
        session = self.get_session()
        try:
            # Use joinedload to ensure employee relationship is eager-loaded
            # and verify data is loaded before session close
            records = session.query(DailyRecord).filter_by(date=date).options(joinedload(DailyRecord.employee)).all()
            for record in records:
                # Access the attribute to force load if joinedload fails silently
                _ = record.employee
            return records
        finally:
            session.close()

    def get_employee_attendance_range(self, emp_id, start_date=None, end_date=None):
        """Get attendance records for an employee within date range"""
        session = self.get_session()
        try:
            from utils.helpers import parse_date_compact
            
            query = session.query(DailyRecord).filter_by(employee_id=emp_id)
            
            if start_date:
                # Parse if string
                if isinstance(start_date, str):
                    start_date = parse_date_compact(start_date)
                if start_date:
                    query = query.filter(DailyRecord.date >= start_date)
                    
            if end_date:
                # Parse if string
                if isinstance(end_date, str):
                    end_date = parse_date_compact(end_date)
                if end_date:
                    query = query.filter(DailyRecord.date <= end_date)
                    
            return query.order_by(DailyRecord.date.asc()).all()
        finally:
            session.close()

    def process_attendance_for_date(self, target_date, source='system'):
        """Process raw logs into DailyRecords for a specific date"""
        session = self.get_session()
        try:
            from core.services.attendance_service import AttendanceService

            service = AttendanceService(session)

            # Create date range for the entire day
            start_of_day = datetime.combine(target_date, time.min)
            end_of_day = datetime.combine(target_date, time.max)

            # Get all logs for this date using range (works for all DBs)
            logs = session.query(AttendanceLog).filter(
                AttendanceLog.timestamp >= start_of_day,
                AttendanceLog.timestamp <= end_of_day
            ).all()

            # Group by employee
            emp_logs = {}
            for log in logs:
                if log.employee_code not in emp_logs:
                    emp_logs[log.employee_code] = []
                emp_logs[log.employee_code].append(log)

            processed_count = 0

            for emp_code, logs in emp_logs.items():
                employee = session.query(Employee).filter_by(code=emp_code).first()
                if not employee:
                    continue

                check_in = None
                check_out = None

                logs.sort(key=lambda x: x.timestamp)
                ins = [l.timestamp for l in logs if l.type == 'IN']
                outs = [l.timestamp for l in logs if l.type == 'OUT']

                if ins:
                    check_in = min(ins).time()
                elif logs:
                    check_in = logs[0].timestamp.time()

                if outs:
                    check_out = max(outs).time()
                elif logs and len(logs) > 1:
                    check_out = logs[-1].timestamp.time()

                _, updated = service.upsert_daily_record(
                    employee_id=employee.id,
                    attendance_date=target_date,
                    check_in=check_in,
                    check_out=check_out,
                    source=source,
                    commit=False
                )
                if updated:
                    processed_count += 1

            session.commit()
            return processed_count
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_attendance_report(self, date_from=None, date_to=None):
        """Get attendance report data with eager loading"""
        session = self.get_session()
        try:
            from utils.helpers import parse_date_compact
            
            # Use joinedload to eagerly load employee and their department
            query = session.query(DailyRecord).options(
                joinedload(DailyRecord.employee).joinedload(Employee.department)
            )
            query = query.join(Employee)
            
            if date_from:
                parsed_date_from = parse_date_compact(date_from)
                if parsed_date_from:
                    query = query.filter(DailyRecord.date >= parsed_date_from)
            if date_to:
                parsed_date_to = parse_date_compact(date_to)
                if parsed_date_to:
                    query = query.filter(DailyRecord.date <= parsed_date_to)
                
            results = query.order_by(Employee.code.asc(), DailyRecord.date.asc()).all()
            
            # Filter inactive employees if needed (User requested for reports)
            # Since DailyRecord is linked to Employee, we check employee status
            results = [r for r in results if r.employee and r.employee.is_active]
            
            # Access attributes to ensure they are loaded in the session
            for record in results:
                if record.employee:
                    _ = record.employee.name
                    if record.employee.department:
                        _ = record.employee.department.name
            
            return results
        finally:
            session.close()

    # =====================================
    # Documents Methods
    # =====================================
    
    def get_document_types(self):
        """ط¬ظ„ط¨ ط¬ظ…ظٹط¹ ط£ظ†ظˆط§ط¹ ط§ظ„ظ…ط³طھظ†ط¯ط§طھ ط§ظ„ظ…ط¹ط±ظپط©"""
        session = self.get_session()
        try:
            return session.query(DocumentType).order_by(DocumentType.name).all()
        finally:
            session.close()

    def add_employee_document_advanced(self, employee_id, filename, file_path, type_id, expiry_date=None, notes=None):
        """ط¥ط¶ط§ظپط© ظ…ط³طھظ†ط¯ ظ…ظˆط¸ظپ ظ…ط¹ طھظپط§طµظٹظ„ ظ…طھظ‚ط¯ظ…ط©"""
        session = self.get_session()
        try:
            doc = EmployeeDocument(
                employee_id=employee_id,
                filename=filename,
                file_path=file_path,
                type_id=type_id,
                expiry_date=expiry_date,
                notes=notes
            )
            session.add(doc)
            session.commit()
            return doc
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_employee_documents(self, employee_id):
        """ط¬ظ„ط¨ ط¬ظ…ظٹط¹ ظ…ط³طھظ†ط¯ط§طھ ط§ظ„ظ…ظˆط¸ظپ ظ…ط¹ ظ…ط¹ظ„ظˆظ…ط§طھ ط§ظ„ظ†ظˆط¹"""
        session = self.get_session()
        try:
            from sqlalchemy.orm import joinedload
            return session.query(EmployeeDocument).options(
                joinedload(EmployeeDocument.type_info)
            ).filter_by(employee_id=employee_id).order_by(EmployeeDocument.upload_date.desc()).all()
        finally:
            session.close()

    def delete_employee_document(self, doc_id):
        session = self.get_session()
        try:
            doc = session.query(EmployeeDocument).filter_by(id=doc_id).first()
            if doc:
                session.delete(doc)
                session.commit()
                return doc
            return None
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def clear_attendance_records(self, date):
        """Delete all DailyRecord AND AttendanceLog entries for a specific date"""
        session = self.get_session()
        try:
            # Delete processed records
            session.query(DailyRecord).filter(DailyRecord.date == date).delete()
            
            # Delete raw logs for that day to prevent auto-reprocess from bringing them back
            from datetime import datetime, time
            start = datetime.combine(date, time.min)
            end = datetime.combine(date, time.max)
            
            session.query(AttendanceLog).filter(
                AttendanceLog.timestamp >= start,
                AttendanceLog.timestamp <= end
            ).delete(synchronize_session=False)
            
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_logs_by_date(self, date):
        """Get all AttendanceLog entries for a specific date"""
        session = self.get_session()
        try:
            from datetime import datetime, time
            # logs store timestamp (datetime). Filter by date range for better SQLite compatibility.
            start_of_day = datetime.combine(date, time.min)
            end_of_day = datetime.combine(date, time.max)
            return session.query(AttendanceLog).filter(
                AttendanceLog.timestamp >= start_of_day,
                AttendanceLog.timestamp <= end_of_day
            ).all()
        finally:
            session.close()

    def get_employee_by_code(self, code):
        session = self.get_session()
        try:
            return session.query(Employee).filter_by(code=code).first()
        finally:
            session.close()

    def update_daily_record(self, record_id, check_in_time, check_out_time):
        """Update an existing DailyRecord manually"""
        session = self.get_session()
        try:
            from core.services.attendance_service import AttendanceService

            record = session.query(DailyRecord).get(record_id)
            if record:
                service = AttendanceService(session)
                service.process_attendance_record(
                    employee_id=record.employee_id,
                    attendance_date=record.date,
                    check_in=check_in_time,
                    check_out=check_out_time,
                    source='manual',
                    commit=False
                )
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    # ===== Audit Log Functions (ط³ط¬ظ„ط§طھ ط§ظ„طھطھط¨ط¹) =====
    
    @property
    def _audit_log_service(self):
        """Lazy-initialized `AuditLogService` bound to this manager's session
        factory. The service is instantiated on first access and cached on the
        instance via a private attribute so subsequent calls reuse it.

        NOTE (P1-C02 slice, 2026-08-07): unlike the earlier `UserSettingsService`
        extraction which only created the service file but left the
        `DBManager.user_setting*` methods with their original inline logic (so
        that service is currently unused -- see AI_TEAM_HANDOFF.md today's
        entry), this audit-log slice wires the `DBManager.get_audit_log*` /
        `export_audit_logs_csv` methods to actually delegate here, keeping the
        public method signatures unchanged for backwards compatibility with
        `app/routes/reports.py`.
        """
        svc = getattr(self, '_audit_log_service_instance', None)
        if svc is None:
            from core.services.audit_log_service import AuditLogService
            svc = AuditLogService(self.Session)
            self._audit_log_service_instance = svc
        return svc


    def get_audit_logs_by_employee(self, employee_code, limit=100):
        """Compatibility wrapper delegating to `AuditLogService.get_logs_by_employee`."""
        return self._audit_log_service.get_logs_by_employee(employee_code, limit=limit)

    def get_audit_logs_by_field(self, field_name, limit=100):
        """Compatibility wrapper delegating to `AuditLogService.get_logs_by_field`."""
        return self._audit_log_service.get_logs_by_field(field_name, limit=limit)

    def get_audit_logs_recent(self, limit=100):
        """Compatibility wrapper delegating to `AuditLogService.get_recent_logs`."""
        return self._audit_log_service.get_recent_logs(limit=limit)

    def get_audit_log_summary(self, employee_code):
        """Compatibility wrapper delegating to `AuditLogService.get_summary`."""
        return self._audit_log_service.get_summary(employee_code)

    def get_audit_log_history(self, employee_code, field_name):
        """Compatibility wrapper delegating to `AuditLogService.get_field_history`."""
        return self._audit_log_service.get_field_history(employee_code, field_name)

    def export_audit_logs_csv(self, filename="audit_logs.csv"):
        """Compatibility wrapper delegating to `AuditLogService.export_csv`."""
        return self._audit_log_service.export_csv(filename=filename)
    def add_bonus(self, employee_id, amount, reason, date_awarded, paid_with_salary=True):
        """
        ط¥ط¶ط§ظپط© ظ…ظƒط§ظپط£ط© ط¬ط¯ظٹط¯ط© ظ„ظ„ظ…ظˆط¸ظپ
        
        Args:
            employee_id: ظ…ط¹ط±ظپ ط§ظ„ظ…ظˆط¸ظپ
            amount: ظ…ط¨ظ„ط؛ ط§ظ„ظ…ظƒط§ظپط£ط©
            reason: ط³ط¨ط¨ ط§ظ„ظ…ظƒط§ظپط£ط©
            date_awarded: طھط§ط±ظٹط® ظ…ظ†ط­ ط§ظ„ظ…ظƒط§ظپط£ط©
            paid_with_salary: ظ‡ظ„ ط³طھظڈطµط±ظپ ظ…ط¹ ط§ظ„ط±ط§طھط¨ (True) ط£ظ… طµظڈط±ظپطھ ظ…ط³ط¨ظ‚ط§ظ‹ (False)
            
        Returns:
            Bonus: ظƒط§ط¦ظ† ط§ظ„ظ…ظƒط§ظپط£ط© ط§ظ„ظ…ط¶ط§ظپط©
        """
        session = self.get_session()
        try:
            bonus = Bonus(
                employee_id=employee_id,
                amount=amount,
                reason=reason,
                date_awarded=date_awarded,
                paid_with_salary=paid_with_salary
            )
            session.add(bonus)
            session.commit()
            return bonus
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_all_bonuses(self):
        """
        ط§ط³طھط±ط¬ط§ط¹ ط¬ظ…ظٹط¹ ط§ظ„ظ…ظƒط§ظپط¢طھ ظ…ط¹ ط¨ظٹط§ظ†ط§طھ ط§ظ„ظ…ظˆط¸ظپظٹظ†
        
        Returns:
            list: ظ‚ط§ط¦ظ…ط© ط¨ط¬ظ…ظٹط¹ ط§ظ„ظ…ظƒط§ظپط¢طھ
        """
        session = self.get_session()
        try:
            return session.query(Bonus).options(joinedload(Bonus.employee)).all()
        finally:
            session.close()

    def get_bonus_by_id(self, bonus_id):
        """
        ط§ط³طھط±ط¬ط§ط¹ ظ…ظƒط§ظپط£ط© ظ…ط­ط¯ط¯ط© ط­ط³ط¨ ط§ظ„ظ…ط¹ط±ظپ
        
        Args:
            bonus_id: ظ…ط¹ط±ظپ ط§ظ„ظ…ظƒط§ظپط£ط©
            
        Returns:
            Bonus: ظƒط§ط¦ظ† ط§ظ„ظ…ظƒط§ظپط£ط©
        """
        session = self.get_session()
        try:
            return session.query(Bonus).options(joinedload(Bonus.employee)).filter_by(id=bonus_id).first()
        finally:
            session.close()

    def get_employee_bonuses(self, employee_id):
        """
        ط§ط³طھط±ط¬ط§ط¹ ط¬ظ…ظٹط¹ ظ…ظƒط§ظپط¢طھ ظ…ظˆط¸ظپ ظ…ط¹ظٹظ†
        
        Args:
            employee_id: ظ…ط¹ط±ظپ ط§ظ„ظ…ظˆط¸ظپ
            
        Returns:
            list: ظ‚ط§ط¦ظ…ط© ط¨ظ…ظƒط§ظپط¢طھ ط§ظ„ظ…ظˆط¸ظپ
        """
        session = self.get_session()
        try:
            return session.query(Bonus).filter_by(employee_id=employee_id).order_by(Bonus.date_awarded.asc()).all()
        finally:
            session.close()

    def update_bonus(self, bonus_id, **kwargs):
        """
        طھط­ط¯ظٹط« ط¨ظٹط§ظ†ط§طھ ط§ظ„ظ…ظƒط§ظپط£ط©
        
        Args:
            bonus_id: ظ…ط¹ط±ظپ ط§ظ„ظ…ظƒط§ظپط£ط©
            **kwargs: ط§ظ„ط­ظ‚ظˆظ„ ط§ظ„ظ…ط±ط§ط¯ طھط­ط¯ظٹط«ظ‡ط§
            
        Returns:
            Bonus: ظƒط§ط¦ظ† ط§ظ„ظ…ظƒط§ظپط£ط© ط§ظ„ظ…ط­ط¯ط«ط©
        """
        session = self.get_session()
        try:
            bonus = session.query(Bonus).filter_by(id=bonus_id).first()
            if bonus:
                for key, value in kwargs.items():
                    if hasattr(bonus, key):
                        setattr(bonus, key, value)
                session.commit()
                return bonus
            return None
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_bonus(self, bonus_id):
        """
        ط­ط°ظپ ظ…ظƒط§ظپط£ط©
        
        Args:
            bonus_id: ظ…ط¹ط±ظپ ط§ظ„ظ…ظƒط§ظپط£ط©
            
        Returns:
            bool: True ط¥ط°ط§ طھظ… ط§ظ„ط­ط°ظپ ط¨ظ†ط¬ط§ط­
        """
        session = self.get_session()
        try:
            bonus = session.query(Bonus).filter_by(id=bonus_id).first()
            if bonus:
                session.delete(bonus)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_bonuses_by_month(self, employee_id, month, year):
        """
        ط§ط³طھط±ط¬ط§ط¹ ط§ظ„ظ…ظƒط§ظپط¢طھ ظ„ظ…ظˆط¸ظپ ظ…ط¹ظٹظ† ظپظٹ ط´ظ‡ط± ظ…ط­ط¯ط¯
        
        Args:
            employee_id: ظ…ط¹ط±ظپ ط§ظ„ظ…ظˆط¸ظپ
            month: ط§ظ„ط´ظ‡ط± (1-12)
            year: ط§ظ„ط³ظ†ط©
            
        Returns:
            list: ظ‚ط§ط¦ظ…ط© ط§ظ„ظ…ظƒط§ظپط¢طھ ظپظٹ ط§ظ„ط´ظ‡ط± ط§ظ„ظ…ط­ط¯ط¯
        """
        session = self.get_session()
        try:
            from datetime import date
            start_date = date(year, month, 1)
            
            if month == 12:
                end_date = date(year + 1, 1, 1)
            else:
                end_date = date(year, month + 1, 1)
            
            return session.query(Bonus).filter(
                Bonus.employee_id == employee_id,
                Bonus.date_awarded >= start_date,
                Bonus.date_awarded < end_date
            ).all()
        finally:
            session.close()

    # ===== Salary History Functions (ط³ط¬ظ„ طھط§ط±ظٹط® ط§ظ„ط±ظˆط§طھط¨) =====
    
    def add_salary_history(self, employee_id, old_salary, new_salary, reason=None, notes=None, modified_by=None):
        """
        طھط³ط¬ظٹظ„ طھط¹ط¯ظٹظ„ ط¹ظ„ظ‰ ط±ط§طھط¨ ط§ظ„ظ…ظˆط¸ظپ ظپظٹ ط§ظ„ط³ط¬ظ„ ط§ظ„طھط§ط±ظٹط®ظٹ
        """
        session = self.get_session()
        try:
            from datetime import datetime
            
            salary_change = new_salary - old_salary
            
            history = SalaryHistory(
                employee_id=employee_id,
                old_salary=old_salary,
                new_salary=new_salary,
                salary_change=salary_change,
                change_date=datetime.now(),
                reason=reason,
                notes=notes,
                modified_by=modified_by
            )
            
            session.add(history)
            session.commit()
            return history
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_employee_salary_history(self, employee_id):
        """
        ط§ظ„ط­طµظˆظ„ ط¹ظ„ظ‰ ط§ظ„ط³ط¬ظ„ ط§ظ„طھط§ط±ظٹط®ظٹ ط§ظ„ظƒط§ظ…ظ„ ظ„طھط¹ط¯ظٹظ„ط§طھ ط±ط§طھط¨ ط§ظ„ظ…ظˆط¸ظپ
        """
        session = self.get_session()
        try:
            return session.query(SalaryHistory).options(
                joinedload(SalaryHistory.employee)
            ).filter(
                SalaryHistory.employee_id == employee_id
            ).order_by(SalaryHistory.effective_date.desc(), SalaryHistory.change_date.desc()).all()
        finally:
            session.close()
    
    def get_salary_history_report(self, employee_id=None, from_date=None, to_date=None):
        """
        ط§ظ„ط­طµظˆظ„ ط¹ظ„ظ‰ طھظ‚ط±ظٹط± ط§ظ„ط³ط¬ظ„ ط§ظ„طھط§ط±ظٹط®ظٹ ظ„ظ„ط±ظˆط§طھط¨ ظ…ط¹ ط§ظ„ظپظ„طھط±ط©
        """
        session = self.get_session()
        try:
            query = session.query(SalaryHistory).join(Employee).options(
                joinedload(SalaryHistory.employee)
            )
            
            if employee_id:
                query = query.filter(SalaryHistory.employee_id == employee_id)
            
            if from_date:
                query = query.filter(SalaryHistory.change_date >= from_date)
            
            if to_date:
                from datetime import datetime, time
                # طھط´ظ…ظ„ ط§ظ„ظٹظˆظ… ظƒط§ظ…ظ„ط§ظ‹
                query = query.filter(SalaryHistory.change_date < datetime.combine(to_date, time.max))
            
            return query.order_by(SalaryHistory.effective_date.desc(), SalaryHistory.change_date.desc()).all()
        finally:
            session.close()
    
    def get_salary_history_with_employee(self, employee_id):
        """
        ط§ظ„ط­طµظˆظ„ ط¹ظ„ظ‰ ط§ظ„ط³ط¬ظ„ ط§ظ„طھط§ط±ظٹط®ظٹ ظ…ط¹ ط¨ظٹط§ظ†ط§طھ ط§ظ„ظ…ظˆط¸ظپ
        """
        session = self.get_session()
        try:
            return session.query(SalaryHistory).options(
                joinedload(SalaryHistory.employee)
            ).filter(
                SalaryHistory.employee_id == employee_id
            ).order_by(SalaryHistory.change_date.desc()).all()
        finally:
            session.close()

    def get_documents_status_all_employees(self, department_id=None, only_missing=False, only_expired=False, include_optional=True):
        """
        Build a per-employee document status report.
        Returns a list of dicts: { employee, provided: [{type_name, expiry_date, filename, is_expired}], missing: [{name, is_required}] }
        If department_id is provided, only employees in that department are included.

        Filters:
        - only_missing: if True, only return employees who have missing required documents (or missing when include_optional=True)
        - only_expired: if True, only return employees who have at least one expired provided document
        - include_optional: if False, exclude optional document types from the "missing" list
        """
        session = self.get_session()
        try:
            # Load all document types
            doc_types = session.query(DocumentType).all()

            # Base employee query
            emp_q = session.query(Employee).options(joinedload(Employee.documents), joinedload(Employee.department))
            if department_id:
                emp_q = emp_q.filter(Employee.department_id == department_id)

            employees = emp_q.order_by(Employee.code).all()

            results = []
            from datetime import date as _date

            for emp in employees:
                provided = []
                provided_type_ids = set()

                for doc in emp.documents or []:
                    # determine type name
                    tname = None
                    if doc.type_info:
                        tname = doc.type_info.name
                        dt_needs_expiry = doc.type_info.needs_expiry
                    elif doc.document_type:
                        tname = doc.document_type
                        dt_needs_expiry = False
                    else:
                        tname = 'ط؛ظٹط± ظ…ط¹ط±ظˆظپ'
                        dt_needs_expiry = False

                    is_expired = False
                    if doc.expiry_date and isinstance(doc.expiry_date, _date):
                        try:
                            is_expired = doc.expiry_date < _date.today()
                        except Exception:
                            is_expired = False

                    provided.append({
                        'type_name': tname,
                        'expiry_date': doc.expiry_date,
                        'filename': doc.filename,
                        'upload_date': doc.upload_date,
                        'is_expired': is_expired,
                        'needs_expiry': dt_needs_expiry
                    })
                    if doc.type_id:
                        provided_type_ids.add(doc.type_id)

                # Determine missing types (by DocumentType.id) and include is_required flag
                missing = []
                for dt in doc_types:
                    if dt.id not in provided_type_ids:
                        if (not include_optional) and (dt.is_required == False):
                            # skip optional types when requested
                            continue
                        missing.append({'name': dt.name, 'is_required': bool(dt.is_required)})

                row = {
                    'employee': emp,
                    'provided': provided,
                    'missing': missing
                }

                # Apply top-level filters
                if only_missing:
                    if not missing:
                        continue
                if only_expired:
                    has_expired = any(p.get('is_expired') for p in provided)
                    if not has_expired:
                        continue

                results.append(row)

            return results
        finally:
            session.close()
