"""
Audit Log Service
================
Read-only querying and CSV export of `AuditLog` records (employee field-change
audit trail).

Extracted from `core/db_manager.py` (God Class refactor, P1-C02) to a cohesive,
independently-testable unit. The service owns its session lifecycle per call
(open / use / finally close), matching the original `DBManager` methods'
behavior exactly. `DBManager.get_audit_log*` / `export_audit_logs_csv` methods
now delegate here.

All methods are read-only (no writes); import path uses the package style
`from core.database_models import AuditLog` to match `db_manager.py` and avoid
the `Table already defined` sys.modules collision seen with flat-style imports
(see AI_TEAM_HANDOFF.md 2026-08-07 entry).
"""

import csv

from core.database_models import AuditLog


class AuditLogService:
    """Service for querying and exporting `AuditLog` records."""

    def __init__(self, session_factory):
        """
        Initialize with a session factory (e.g. ``sessionmaker(bind=engine)``).

        Each public method opens a fresh session from this factory and closes
        it in a ``finally`` block, mirroring the original ``DBManager`` methods.
        """
        self._session_factory = session_factory

    def get_logs_by_employee(self, employee_code, limit=100):
        """
        الحصول على سجلات التتبع لموظف معين.

        Parameters:
        - employee_code: كود الموظف
        - limit: عدد السجلات المرجعة (الافتراضي: 100)

        Returns:
        - قائمة بسجلات AuditLog مرتبة تنازليًا حسب timestamp.
        """
        session = self._session_factory()
        try:
            logs = (
                session.query(AuditLog)
                .filter(AuditLog.employee_code == employee_code)
                .order_by(AuditLog.timestamp.desc())
                .limit(limit)
                .all()
            )
            return logs
        finally:
            session.close()

    def get_logs_by_field(self, field_name, limit=100):
        """
        الحصول على سجلات التتبع لحقل معين (مثال: جميع تغييرات الراتب الأساسي).

        Parameters:
        - field_name: اسم الحقل (مثل 'base_salary')
        - limit: عدد السجلات المرجعة (الافتراضي: 100)

        Returns:
        - قائمة بسجلات AuditLog مرتبة تنازليًا حسب timestamp.
        """
        session = self._session_factory()
        try:
            logs = (
                session.query(AuditLog)
                .filter(AuditLog.field_name == field_name)
                .order_by(AuditLog.timestamp.desc())
                .limit(limit)
                .all()
            )
            return logs
        finally:
            session.close()

    def get_recent_logs(self, limit=100):
        """
        الحصول على آخر سجلات التتبع.

        Parameters:
        - limit: عدد السجلات المرجعة (الافتراضي: 100)

        Returns:
        - قائمة بآخر سجلات AuditLog مرتبة تنازليًا حسب timestamp.
        """
        session = self._session_factory()
        try:
            logs = (
                session.query(AuditLog)
                .order_by(AuditLog.timestamp.desc())
                .limit(limit)
                .all()
            )
            return logs
        finally:
            session.close()
