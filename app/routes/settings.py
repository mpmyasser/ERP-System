from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session, jsonify
import sys
import os

# Add core to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'core'))

from database_models import SystemSetting

settings_bp = Blueprint('settings', __name__)


def _current_user_id():
    user_id = session.get('user_id')
    return int(user_id) if user_id else None


@settings_bp.route('/', methods=['GET', 'POST'])
def index():
    db_manager = current_app.db
    db_session = db_manager.get_session()

    try:
        if request.method == 'POST':
            # Update system-level settings page (existing behavior)
            form_data = request.form
            for key, value in form_data.items():
                setting = db_session.query(SystemSetting).filter_by(key=key).first()
                if setting:
                    setting.value = value

            db_session.commit()
            flash('?? ????? ??????? ?????? ?????', 'center')
            return redirect(url_for('settings.index'))

        # Get all settings grouped by category
        settings_records = db_session.query(SystemSetting).all()
        categories = {}
        for setting in settings_records:
            if setting.category not in categories:
                categories[setting.category] = []
            categories[setting.category].append(setting)

        return render_template('settings/index.html', categories=categories)
    finally:
        db_session.close()


@settings_bp.route('/user/preferences', methods=['GET'])
def get_user_preferences():
    """Generic key-value retrieval for current logged-in user settings."""
    user_id = _current_user_id()
    if not user_id:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 403

    db = current_app.db
    key = (request.args.get('key') or '').strip()
    prefix = (request.args.get('prefix') or '').strip()

    if key:
        value = db.get_user_setting(user_id, key)
        return jsonify({'success': True, 'settings': {key: value}, 'key': key, 'value': value})

    settings = db.get_user_settings(user_id, prefix=prefix or None)
    return jsonify({'success': True, 'settings': settings})


@settings_bp.route('/user/preferences', methods=['POST'])
def save_user_preferences():
    """Generic key-value save/delete for current logged-in user settings."""
    user_id = _current_user_id()
    if not user_id:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 403

    data = request.get_json(silent=True) or {}
    db = current_app.db

    settings_payload = {}
    provided_settings = data.get('settings')
    if isinstance(provided_settings, dict):
        for raw_key, value in provided_settings.items():
            key = str(raw_key or '').strip()
            if key:
                settings_payload[key] = value

    single_key = str(data.get('key') or '').strip()
    if single_key:
        settings_payload[single_key] = data.get('value')

    remove_keys = data.get('remove_keys') or []
    if not isinstance(remove_keys, list):
        remove_keys = []
    remove_keys = [str(k).strip() for k in remove_keys if str(k).strip()]

    try:
        if settings_payload:
            db.set_user_settings(user_id, settings_payload)
        if remove_keys:
            db.delete_user_settings(user_id, remove_keys)

        return jsonify({
            'success': True,
            'saved_keys': list(settings_payload.keys()),
            'removed_keys': remove_keys
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@settings_bp.route('/table_widths', methods=['GET'])
def get_table_widths():
    """Backward-compatible endpoint backed by centralized user preferences."""
    user_id = _current_user_id()
    if not user_id:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 403

    page = request.args.get('page') or ''
    table_key = request.args.get('table_key')

    db = current_app.db
    key = db._table_setting_key(page, table_key)
    widths = db.get_user_setting(user_id, key)

    return jsonify({'success': True, 'widths': widths})


@settings_bp.route('/table_widths', methods=['POST'])
def save_table_widths():
    """Backward-compatible endpoint backed by centralized user preferences."""
    user_id = _current_user_id()
    if not user_id:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 403

    data = request.get_json(silent=True) or {}
    page = data.get('page') or ''
    table_key = data.get('table_key')
    widths = data.get('widths')

    if not isinstance(widths, (list, dict)):
        return jsonify({'success': False, 'message': 'Invalid widths payload'}), 400

    db = current_app.db
    key = db._table_setting_key(page, table_key)

    try:
        db.set_user_setting(user_id, key, widths)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
