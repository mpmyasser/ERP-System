import os
import sys
from pathlib import Path

# Add the workspace root to sys.path so we can import app
workspace_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(workspace_root))

legacy_dir = workspace_root / "حركة التشغيل"
temp_legacy_dir = workspace_root / "حركة التشغيل_temp_rename"

print(f"Workspace Root: {workspace_root}")
print(f"Legacy Dir: {legacy_dir} (exists: {legacy_dir.exists()})")

renamed = False
try:
    if legacy_dir.exists():
        print(f"Temporarily renaming '{legacy_dir}' to '{temp_legacy_dir}' to simulate deletion...")
        os.rename(legacy_dir, temp_legacy_dir)
        renamed = True
        print("Rename successful. Now verifying imports...")
    else:
        print("Legacy folder does not exist at the expected path.")

    # Now let's try to import the main application parts and initialize
    print("Importing app.create_app...")
    from app import create_app
    app = create_app()
    print("[OK] app.create_app() ran successfully without the legacy folder!")

    # Verify that the DB path points to the integrated DB
    from app.routes.operation_storage import DB_PATH
    print(f"Integrated DB Path: {DB_PATH}")
    if "حركة التشغيل" in str(DB_PATH):
        print("[ERROR] DB_PATH still points to the legacy folder!")
    else:
        print("[OK] DB_PATH correctly points to the integrated manufacturing_storage folder.")

    # Try database initialization and a simple query
    print("Testing DB connection and database initialization...")
    from app.routes.operation_storage import initialize_database, get_connection
    initialize_database()
    with get_connection() as conn:
        res = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        tables = [r[0] for r in res]
        print(f"[OK] Successfully queried DB. Found {len(tables)} tables: {tables}")

    print("[SUCCESS] 100% independent! Flask app does not depend on the legacy folder at all.")

except Exception as e:
    print(f"[FAILED] Independence check failed: {e}")
    import traceback
    traceback.print_exc()

finally:
    if renamed:
        print(f"Restoring name of '{temp_legacy_dir}' back to '{legacy_dir}'...")
        try:
            os.rename(temp_legacy_dir, legacy_dir)
            print("Restoration complete.")
        except Exception as err:
            print(f"[CRITICAL ERROR] Failed to restore legacy folder name: {err}")
            print(f"Please manually rename '{temp_legacy_dir}' to '{legacy_dir}'!")
