"""
Loans Service
=============
CRUD operations on `Loan` records (employee loans / سلف).

Extracted from `core/db_manager.py` (God Class refactor, P1-C02), following the
same pattern established by `AuditLogService` / `PenaltyService` / `BonusService`.
The service owns its session lifecycle per call (open / use / commit-or-rollback
/ finally close), matching the original `DBManager` methods' behavior exactly.
`DBManager.add_loan` / `check_loan_exists` / `update_loan` / `get_all_loans` /
`get_loan_by_id` / `delete_loan` now delegate here.

Import path uses the package style `from core.database_models import Loan` to
match `db_manager.py` and avoid the `Table already defined` sys.modules
collision seen with flat-style imports (see AI_TEAM_HANDOFF.md 2026-08-07
entry).

NOTE: this file replaces an earlier partial draft (`LoansService(db_session)`
shared-session variant with different method names like `get_active_loans` /
`deduct_installment`). Those draft methods had NO callers in `app/routes/` or
`scripts/` (verified via grep before refactor) and were unused dead code; the
active callers all use the DBManager-level CRUD names below. The draft is
therefore replaced wholesale (not extended) per the BonusService pattern.
"""

from sqlalchemy.orm import joinedload

from core.database_models import Loan


class LoansService:
    """Service for creating, reading, updating, and deleting `Loan` records."""

    def __init__(self, session_factory):
        """
        Initialize with a session factory (e.g. ``sessionmaker(bind=engine)``).

        Each public method opens a fresh session from this factory and closes
        it in a ``finally`` block, mirroring the original ``DBManager`` methods.
        """
        self._session_factory = session_factory

    def add_loan(self, employee_id, amount, loan_type, number_of_installments,
                 date_issued=None, excluded_months=None, status='Pending',
                 cost_center=None):
        """
        إضافة سلفة جديدة لموظف.

        Notes:
        - يُعاد ضبط ``loan_type`` تلقائيًا بناءً على عدد الأقساط (نفس منطق
          ``DBManager.add_loan`` الأصلي): قسط واحد => 'temporary'، أكثر => 'permanent'.
        """
        # Force correct type based on installments (preserve original behavior)
        if number_of_installments == 1:
            loan_type = 'temporary'
        elif number_of_installments > 1:
            loan_type = 'permanent'

        session = self._session_factory()
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
        """Check if a loan already exists for an employee on a specific date."""
        session = self._session_factory()
        try:
            return session.query(Loan).filter(
                Loan.employee_id == employee_id,
                Loan.date == date_issued
            ).first() is not None
        finally:
            session.close()

    def update_loan(self, loan_id, **kwargs):
        """Update loan."""
        session = self._session_factory()
        try:
            loan = session.query(Loan).filter_by(id=loan_id).first()
            if loan:
                for key, value in kwargs.items():
                    if hasattr(loan, key):
                        setattr(loan, key, value)

                # Force correct type based on installments if updated
                # (preserve original behavior)
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
        """Get all loans with employee data."""
        # NOTE: Employee / Department are referenced indirectly via joinedload
        # (the relationship is defined on the Loan model), so no direct import
        # is needed here -- the ORM resolves the join at query time.
        session = self._session_factory()
        try:
            from core.database_models import Employee
            return session.query(Loan).join(Employee).options(
                joinedload(Loan.employee).joinedload(Employee.department)
            ).order_by(Employee.code.asc(), Loan.date.asc(), Loan.id.asc()).all()
        finally:
            session.close()

    def get_loan_by_id(self, loan_id):
        """Get loan by ID."""
        session = self._session_factory()
        try:
            from core.database_models import Employee
            return session.query(Loan).options(
                joinedload(Loan.employee).joinedload(Employee.department)
            ).filter_by(id=loan_id).first()
        finally:
            session.close()

    def delete_loan(self, loan_id):
        """Delete a loan."""
        session = self._session_factory()
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
