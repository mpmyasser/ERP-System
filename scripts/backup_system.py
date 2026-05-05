import os
import shutil
import datetime
from pathlib import Path
import json

def run_backup(project_root: str):
    project_root = Path(project_root).resolve()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = project_root / "backups" / f"backup_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    db_files = []
    # Scan for .db files
    for root, dirs, files in os.walk(project_root):
        # Skip some dirs
        if any(ignored in root for ignored in [".git", ".venv", "__pycache__", "backups", "node_modules"]):
            continue
        for file in files:
            if file.lower().endswith(".db"):
                db_files.append(Path(root) / file)

    # Copy DB files
    copied_files = []
    for db_file in db_files:
        rel_path = db_file.relative_to(project_root)
        dest_path = backup_dir / "data" / rel_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(db_file, dest_path)
        copied_files.append(str(rel_path))

    # Try Git commit for code
    git_success = False
    git_msg = f"Manual System Backup: {timestamp}"
    try:
        import git
        repo = git.Repo(project_root)
        if repo.is_dirty(untracked_files=True):
            repo.git.add(A=True)
            repo.index.commit(git_msg)
            git_success = True
            print(f"Git commit created: {git_msg}")
        else:
            print("No code changes to commit.")
            git_success = True
    except Exception as e:
        print(f"Git backup failed: {e}")

    # Create manifest
    manifest = {
        "timestamp": timestamp,
        "git_commit": git_msg if git_success else None,
        "db_files": copied_files,
        "status": "Success"
    }
    (backup_dir / "manifest.json").write_text(json.dumps(manifest, indent=4), encoding="utf-8")
    
    print(f"Backup completed successfully in: {backup_dir}")
    return backup_dir

if __name__ == "__main__":
    import sys
    root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    run_backup(root)
