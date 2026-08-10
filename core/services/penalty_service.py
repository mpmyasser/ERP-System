"""
Penalty Service
===============
CRUD operations on `PenaltyBonus` records (employee penalties).

Extracted from `core/db_manager.py` (God Class refactor, P1-C02), following
the same pattern established by `AuditLogService`. The service owns its
session lifecycle per call (open / use / commit-or-rollback / finally close),
matching the original `DBManager` methods' behavior exactly.
`DBManager.add_penalty_bonus` / `get_penalty_by_id` / `get_all_penalties` /
`add_penalty` / `delete_penalty` now delegate here.

Import path uses the package style `from core.database_models import
PenaltyBonus, Employee` to match `db_manager.py` and avoid the
`Table already defined` sys.modules collision seen with flat-style imports
(see AI_TEAM_HANDOFF.md 2026-08-07 entry).
"""

from datetime import datetime

from sqlalchemy.orm import joinedload

from core.database_models import PenaltyBonus, Employee


class PenaltyService:
    """Service for creating, reading, and deleting `PenaltyBonus` records."""

    def __init__(self, session_factory):
        """
        Initialize with a session factory (e.g. ``sessionmaker(bind=engine)``).

        Each public method opens a fresh session from this factory and closes
        it in a ``finally`` block, mirroring the original ``DBManager`` methods.
        """
        self._session_factory = session_factory

    def add_penalty_bonus(self, employee_id, date, type, amount, reason):
        """
        إضافة سجل عقوبة/مكافأة بأي نوع حر (يُستخدَم من واجهة API التفاعلية).

        Parameters:
        - employee_id: كود الموظف
        - date: تاريخ العقوبة/المكافأة
        - type: نوع السجل (نص حر)
        - amount: المبلغ
        - reason: السبب

        Returns:
        - سجل PenaltyBonus المُنشأ.
        """
        session = self._session_factory()
        try:
            pb = PenaltyBonus(employee_id=employee_id, date=date, type=type, amount=amount, reason=reason)
            session.add(pb)
            session.commit()
            return pb
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_penalty_by_id(self, penalty_id):
        """
        الحصول على عقوبة بمعرّفها مع تحميل بيانات الموظف.

        Parameters:
        - penalty_id: معرّف العقوبة

        Returns:
        - سجل PenaltyBonus أو None إن لم يوجد.
        """
        session = self._session_factory()
        try:
            return session.query(PenaltyBonus).options(joinedload(PenaltyBonus.employee)).filter_by(id=penalty_id).first()
        finally:
            session.close()

    def get_all_penalties(self):
        """
        الحصول على كل العقوبات مع بيانات الموظف والقسم.

        Returns:
        - قائمة بسجلات PenaltyBonus مرتبة حسب كود الموظف والتاريخ.
        """
        session = self._session_factory()
        try:
            return session.query(PenaltyBonus).join(Employee).options(
                joinedload(PenaltyBonus.employee).joinedload(Employee.department)
            ).order_by(Employee.code.asc(), PenaltyBonus.date.asc(), PenaltyBonus.id.asc()).all()
        finally:
            session.close()

    def add_penalty(self, employee_id, penalty_type, amount, reason, date=None):
        """
        إضافة عقوبة جديدة.

        Parameters:
        - employee_id: كود الموظف
        - penalty_type: نوع العقوبة
        - amount: المبلغ
        - reason: السبب
        - date: التاريخ (افتراضي: اليوم)

        Returns:
        - سجل PenaltyBonus المُنشأ.
        """
        session = self._session_factory()
        try:
            if date is None:
                date = datetime.now().date()

            penalty = PenaltyBonus(
                employee_id=employee_id,
                type=penalty_type,
                amount=amount,
                reason=reason,
                date=date
            )
            session.add(penalty)
            session.commit()
            return penalty
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_penalty(self, penalty_id):
        """
        حذف عقوبة بمعرّفها.

        Parameters:
        - penalty_id: معرّف العقوبة

        Returns:
        - True إذا حُذفت بنجاح، False إذا لم توجد.
        """
        session = self._session_factory()
        try:
            penalty = session.query(PenaltyBonus).filter_by(id=penalty_id).first()
            if penalty:
                session.delete(penalty)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
