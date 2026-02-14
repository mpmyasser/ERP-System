from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
import os
import signal
import threading
import time

from flask import Blueprint, current_app, jsonify, render_template
from git import BadName, GitCommandError, InvalidGitRepositoryError, Repo

from app.routes.auth import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
MAX_COMMITS = 15


def _project_root() -> Path:
    return Path(current_app.root_path).resolve().parent


def _get_repo() -> tuple[Repo, Path]:
    project_root = _project_root()
    if not (project_root / '.git').exists():
        raise InvalidGitRepositoryError('Local .git directory not found in project root.')

    repo = Repo(str(project_root))
    if repo.bare or not repo.working_tree_dir:
        raise InvalidGitRepositoryError('Repository is bare or has no working tree.')

    working_tree = Path(repo.working_tree_dir).resolve()
    if working_tree != project_root:
        raise InvalidGitRepositoryError('Resolved repository root does not match project root.')

    return repo, working_tree


def _scan_db_files(project_root: Path) -> list[str]:
    ignored_dirs = {
        '.git',
        '.venv',
        '.pytest_cache',
        '__pycache__',
        'node_modules',
    }

    db_files: list[str] = []
    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in ignored_dirs]
        for filename in files:
            if not filename.lower().endswith('.db'):
                continue
            file_path = Path(root) / filename
            relative_path = file_path.relative_to(project_root).as_posix()
            db_files.append(relative_path)

    return sorted(db_files)


def _is_git_ignored(repo: Repo, relative_path: str) -> bool:
    try:
        output = repo.git.check_ignore(relative_path)
        return bool(output and output.strip())
    except GitCommandError:
        return False


def _validate_db_ignored(repo: Repo, project_root: Path) -> dict[str, Any]:
    db_files = _scan_db_files(project_root)
    not_ignored: list[str] = []

    for rel_path in db_files:
        if not _is_git_ignored(repo, rel_path):
            not_ignored.append(rel_path)

    return {
        'ok': len(not_ignored) == 0,
        'db_files': db_files,
        'not_ignored': not_ignored,
    }


def _schedule_restart(app_obj, project_root: Path) -> None:
    def _restart_worker() -> None:
        # Delay so success response reaches browser first.
        time.sleep(1.5)

        debug_mode = bool(app_obj.debug or os.environ.get('FLASK_DEBUG') == '1')
        if debug_mode:
            # In debug mode, touching a watched python file triggers Werkzeug reload.
            touch_target = project_root / 'run.py'
            if not touch_target.exists():
                touch_target = project_root / 'app' / '__init__.py'
            now = time.time()
            os.utime(touch_target, (now, now))
            return

        # In production, terminate current process and let process manager restart it.
        os.kill(os.getpid(), signal.SIGTERM)

    threading.Thread(target=_restart_worker, daemon=True).start()


@admin_bp.route('/backups', methods=['GET'])
@admin_required
def backups_dashboard():
    commits: list[dict[str, str]] = []
    repo_error = None
    db_check = {'ok': False, 'db_files': [], 'not_ignored': []}

    try:
        repo, project_root = _get_repo()

        for commit in repo.iter_commits('HEAD', max_count=MAX_COMMITS):
            commits.append({
                'id': commit.hexsha,
                'short_id': commit.hexsha[:8],
                'date': datetime.fromtimestamp(commit.committed_date).strftime('%Y-%m-%d %H:%M:%S'),
                'message': commit.message.strip() or '(No message)',
            })

        db_check = _validate_db_ignored(repo, project_root)
    except InvalidGitRepositoryError:
        repo_error = 'Git repository was not found from project root.'
    except Exception as exc:  # pragma: no cover - defensive handling
        repo_error = f'Failed to load backups data: {exc}'

    return render_template(
        'admin/backups.html',
        commits=commits,
        repo_error=repo_error,
        db_check=db_check,
    )


@admin_bp.route('/restore/<string:commit_id>', methods=['POST'])
@admin_required
def restore_commit(commit_id: str):
    commit_id = (commit_id or '').strip()
    if not commit_id:
        return jsonify({'success': False, 'message': 'Commit ID is required.'}), 400

    try:
        repo, project_root = _get_repo()
    except InvalidGitRepositoryError:
        return jsonify({'success': False, 'message': 'Git repository not found.'}), 400
    except Exception as exc:
        return jsonify({'success': False, 'message': f'Failed to access repository: {exc}'}), 500

    db_check = _validate_db_ignored(repo, project_root)
    if not db_check['ok']:
        return jsonify({
            'success': False,
            'message': 'Restore blocked: one or more .db files are not ignored by Git.',
            'not_ignored': db_check['not_ignored'],
        }), 400

    try:
        target_commit = repo.commit(commit_id)
    except (BadName, ValueError):
        return jsonify({'success': False, 'message': 'Invalid commit ID.'}), 404

    try:
        repo.git.reset('--hard', target_commit.hexsha)
    except GitCommandError as exc:
        return jsonify({'success': False, 'message': f'Git reset failed: {exc}'}), 500

    _schedule_restart(current_app._get_current_object(), project_root)

    return jsonify({
        'success': True,
        'message': (
            f'Restored to commit {target_commit.hexsha[:8]} successfully. '
            'Server restart has been triggered.'
        ),
        'commit': target_commit.hexsha,
    })
