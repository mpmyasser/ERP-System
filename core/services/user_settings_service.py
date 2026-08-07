"""
User Settings Service
====================
Central per-user key-value settings store backed by the `UserPreference` model.

Extracted from `core/db_manager.py` (God Class refactor, P1-C02) to a cohesive,
independently-testable unit. The service owns its session lifecycle per call
(open / commit / rollback / close), matching the original `DBManager` methods'
behavior exactly. `DBManager.user_setting*` / `*_table_setting*` / `_table_setting_key`
methods now delegate here.
"""

import json
from types import SimpleNamespace

from auth_models import UserPreference


class UserSettingsService:
    """
    Service for managing per-user generic key-value preferences.

    Built with a SQLAlchemy ``session_factory`` (a ``sessionmaker``) — *not* a
    live session — so each public call opens its own short-lived session and
    closes it in ``finally``, identical to the original in-DBManager behavior.
    This keeps callers undisturbed (no changes needed in
    ``app/routes/settings.py``) while moving ~157 lines of logic out of the
    God Class.
    """

    def __init__(self, session_factory):
        """Initialize with a session factory (e.g. ``sessionmaker(bind=engine)``)."""
        self._session_factory = session_factory

    # ------------------------------------------------------------------
    # Central key-value store
    # ------------------------------------------------------------------
    def get_user_setting(self, user_id, key, default=None):
        session = self._session_factory()
        try:
            rec = session.query(UserPreference).filter_by(user_id=user_id, key=key).first()
            if not rec or rec.value is None:
                return default
            try:
                return json.loads(rec.value)
            except Exception:
                return rec.value
        finally:
            session.close()

    def get_user_settings(self, user_id, prefix=None):
        session = self._session_factory()
        try:
            q = session.query(UserPreference).filter_by(user_id=user_id)
            if prefix:
                q = q.filter(UserPreference.key.like(f"{prefix}%"))

            out = {}
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
        session = self._session_factory()
        try:
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
        session = self._session_factory()
        try:
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
        session = self._session_factory()
        try:
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
        session = self._session_factory()
        try:
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

    # ------------------------------------------------------------------
    # Compatibility wrappers for table width settings
    # ------------------------------------------------------------------
    @staticmethod
    def table_setting_key(page, table_key=None):
        normalized_page = page or ''
        normalized_table = table_key if table_key is not None else '__default__'
        return f"table_widths:{normalized_page}:{normalized_table}"

    def get_user_table_setting(self, user_id, page, table_key=None):
        key = self.table_setting_key(page, table_key)
        value = self.get_user_setting(user_id, key)
        if value is None:
            return None

        try:
            widths_json = json.dumps(value, ensure_ascii=False)
        except Exception:
            widths_json = None
        return SimpleNamespace(widths=widths_json)

    def save_user_table_setting(self, user_id, page, table_key, widths_json):
        key = self.table_setting_key(page, table_key)
        parsed = widths_json
        if isinstance(widths_json, str):
            try:
                parsed = json.loads(widths_json)
            except Exception:
                parsed = widths_json
        self.set_user_setting(user_id, key, parsed)
        return True

