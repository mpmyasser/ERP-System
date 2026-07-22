"""
Form Helpers
============
Shared helpers for building WTForms field data that was previously duplicated
across route modules.
"""


def employee_choices(db, active_only=True, extra_ids=None):
    """Build ``(id, "name (code)")`` choices for an employee select field.

    Args:
        db: DBManager instance exposing ``get_all_employees()``.
        active_only: when True, only active employees are included.
        extra_ids: iterable of employee ids to include even if inactive
            (e.g. the employee already linked to the record being edited).
    """
    extra_ids = set(extra_ids or [])
    return [
        (e.id, f"{e.name} ({e.code})")
        for e in db.get_all_employees()
        if (not active_only) or e.is_active or e.id in extra_ids
    ]
