"""
Migration: add is_manual_override to daily_records
"""

import os
import sys

from sqlalchemy import create_engine, inspect, text


def migrate():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, 'core', 'hr.db')

    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return False

    engine = create_engine(f"sqlite:///{db_path}")

    with engine.connect() as connection:
        inspector = inspect(engine)

        if not inspector.has_table('daily_records'):
            print("Table daily_records does not exist")
            return False

        columns = {col['name'] for col in inspector.get_columns('daily_records')}

        if 'is_manual_override' not in columns:
            connection.execute(
                text("ALTER TABLE daily_records ADD COLUMN is_manual_override BOOLEAN DEFAULT 0")
            )
            connection.commit()
            print("Added daily_records.is_manual_override")
        else:
            print("daily_records.is_manual_override already exists")

        connection.execute(
            text("UPDATE daily_records SET is_manual_override = COALESCE(is_manual_override, 0)")
        )
        connection.commit()

    return True


if __name__ == '__main__':
    ok = migrate()
    sys.exit(0 if ok else 1)
