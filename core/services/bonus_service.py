"""
Bonus Service
=============
CRUD operations on `Bonus` records (employee bonuses, separate from the
`PenaltyBonus` model used by `PenaltyService`).

Extracted from `core/db_manager.py` (God Class refactor, P1-C02), following
the same pattern established by `AuditLogService` / `PenaltyService`. The
service owns its session lifecycle per call (open / use / commit-or-rollback
/ finally close), matching the original `DBManager` methods' behavior exactly.
`DBManager.add_bonus` / `get_all_bonuses` / `get_bonus_by_id` /
`get_employee_bonuses` / `update_bonus` / `delete_bonus` /
`get_bonuses_by_month` now delegate here.

Import path uses the package style `from core.database_models import Bonus`
to match `db_manager.py` and avoid the `Table already defined` sys.modules
collision seen with flat-style imports (see AI_TEAM_HANDOFF.md 2026-08-07
entry). Note that `db_manager.py`'s separate `check_bonus_exists` method
keeps its own local flat-style `from database_models import Bonus` import
(unchanged, out of scope for this slice).
"""

from datetime import date

from sqlalchemy.orm import joinedload

from core.database_models import Bonus


class BonusService:
    """Service for creating, reading, updating, and deleting `Bonus` records."""

    def __init__(self, session_factory):
        """
        Initialize with a session factory (e.g. ``sessionmaker(bind=engine)``).

        Each public method opens a fresh session from this factory and closes
        it in a ``finally`` block, mirroring the original ``DBManager`` methods.
        """
        self._session_factory = session_factory

    def add_bonus(self, employee_id, amount, reason, date_awarded, paid_with_salary=True):
        """
        إضافة مكافأة جديدة للموظف.

        Parameters:
        - employee_id: معرف الموظف
        - amount: مبلغ المكافأة
        - reason: سبب المكافأة
        - date_awarded: تاريخ منح المكافأة
        - paid_with_salary: هل ستُصرف مع الراتب (True) أم صُرفت مسبقًا (False)

        Returns:
        - كائن Bonus المُنشأ.
        """
        session = self._session_factory()
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
        استرجاع جميع المكافآت مع بيانات الموظفين.

        Returns:
        - قائمة بجميع سجلات Bonus مع تحميل الموظف المرتبط (joinedload).
        """
        session = self._session_factory()
        try:
            return session.query(Bonus).options(joinedload(Bonus.employee)).all()
        finally:
            session.close()

    def get_bonus_by_id(self, bonus_id):
        """
        استرجاع مكافأة محددة حسب المعرف.

        Parameters:
        - bonus_id: معرف المكافأة

        Returns:
        - كائن Bonus (مع تحميل الموظف) أو None إن لم يوجد.
        """
        session = self._session_factory()
        try:
            return session.query(Bonus).options(joinedload(Bonus.employee)).filter_by(id=bonus_id).first()
        finally:
            session.close()

    def get_employee_bonuses(self, employee_id):
        """
        استرجاع جميع مكافآت موظف معين مرتبة تصاعديًا حسب تاريخ المنح.

        Parameters:
        - employee_id: معرف الموظف

        Returns:
        - قائمة بسجلات Bonus للموظف.
        """
        session = self._session_factory()
        try:
            return session.query(Bonus).filter_by(employee_id=employee_id).order_by(Bonus.date_awarded.asc()).all()
        finally:
            session.close()

    def update_bonus(self, bonus_id, **kwargs):
        """
        تحديث بيانات المكافأة.

        Parameters:
        - bonus_id: معرف المكافأة
        - **kwargs: الحقول المراد تحديثها

        Returns:
        - كائن Bonus المُحدث أو None إن لم توجد.
        """
        session = self._session_factory()
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
        حذف مكافأة.

        Parameters:
        - bonus_id: معرف المكافأة

        Returns:
        - True إذا تم الحذف بنجاح، False إذا لم توجد.
        """
        session = self._session_factory()
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
        استرجاع المكافآت لموظف معين في شهر محدد.

        Parameters:
        - employee_id: معرف الموظف
        - month: الشهر (1-12)
        - year: السنة

        Returns:
        - قائمة المكافآت في الشهر المحدد.
        """
        session = self._session_factory()
        try:
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
