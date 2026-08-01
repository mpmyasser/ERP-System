from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'core'))

try:
    from database_models import DailyRecord
except ImportError:
    # Fallback for IDE linting / different execution contexts
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'core'))
    from core.database_models import DailyRecord

from utils.helpers import parse_date_compact

interactive_api_bp = Blueprint('interactive_api', __name__)

@interactive_api_bp.route('/add_loan', methods=['POST'])
def add_loan():
    db = current_app.db
    data = request.json
    try:
        employee_id = data.get('employee_id')
        amount = float(data.get('amount'))
        loan_type = data.get('loan_type', 'Daily')
        installments = int(data.get('installments', 1))
        date_issued = parse_date_compact(data.get('date')) or datetime.now().date()
        
        db.add_loan(
            employee_id=employee_id,
            amount=amount,
            loan_type=loan_type,
            number_of_installments=installments,
            date_issued=date_issued
        )
        return jsonify({'success': True, 'message': 'تم إضافة السلفة بنجاح'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@interactive_api_bp.route('/delete_loan', methods=['POST'])
def delete_loan():
    db = current_app.db
    data = request.json
    try:
        loan_id = data.get('id')
        db.delete_loan(loan_id)
        return jsonify({'success': True, 'message': 'تم حذف السلفة بنجاح'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@interactive_api_bp.route('/add_penalty', methods=['POST'])
def add_penalty():
    db = current_app.db
    data = request.json
    try:
        employee_id = data.get('employee_id')
        amount = float(data.get('amount', 0))
        days = float(data.get('days', 0))
        reason = data.get('reason', '')
        date_issued = parse_date_compact(data.get('date')) or datetime.now().date()
        
        db.add_penalty_bonus(
            employee_id=employee_id,
            date=date_issued,
            type='Penalty',
            amount=amount,
            days=days,
            reason=reason
        )
        return jsonify({'success': True, 'message': 'تم إضافة الجزاء بنجاح'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@interactive_api_bp.route('/delete_penalty', methods=['POST'])
def delete_penalty():
    db = current_app.db
    data = request.json
    try:
        penalty_id = data.get('id')
        db.delete_penalty(penalty_id)
        return jsonify({'success': True, 'message': 'تم حذف الجزاء بنجاح'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@interactive_api_bp.route('/add_bonus', methods=['POST'])
def add_bonus():
    db = current_app.db
    data = request.json
    try:
        employee_id = data.get('employee_id')
        amount = float(data.get('amount', 0))
        reason = data.get('reason', '')
        date_issued = parse_date_compact(data.get('date')) or datetime.now().date()
        paid_with_salary = data.get('paid_with_salary', True)
        
        db.add_bonus(
            employee_id=employee_id,
            amount=amount,
            reason=reason,
            date_awarded=date_issued,
            paid_with_salary=paid_with_salary
        )
        return jsonify({'success': True, 'message': 'تم إضافة المكافأة بنجاح'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@interactive_api_bp.route('/add_permission', methods=['POST'])
def add_permission():
    db = current_app.db
    data = request.json
    try:
        employee_id = data.get('employee_id')
        date_val = parse_date_compact(data.get('date')) or datetime.now().date()
        from_time_str = data.get('from_time', '08:00')
        to_time_str = data.get('to_time', '10:00')
        reason = data.get('reason', '')
        is_paid = data.get('is_paid', False)
        
        from_h, from_m = map(int, from_time_str.split(':'))
        to_h, to_m = map(int, to_time_str.split(':'))
        
        db.add_permission(
            employee_id=employee_id,
            date=date_val,
            from_time=time(from_h, from_m),
            to_time=time(to_h, to_m),
            reason=reason,
            is_paid=is_paid
        )
        return jsonify({'success': True, 'message': 'تم إضافة التصريح بنجاح'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@interactive_api_bp.route('/update_attendance', methods=['POST'])
def update_attendance():
    db = current_app.db
    data = request.json
    try:
        employee_id = data.get('employee_id')
        date_val = parse_date_compact(data.get('date'))
        check_in_str = data.get('check_in')
        check_out_str = data.get('check_out')
        status = data.get('status', 'Present')
        
        # Check if record exists
        session = db.get_session()
        record = session.query(DailyRecord).filter_by(employee_id=employee_id, date=date_val).first()
        
        cin = None
        if check_in_str:
            h, m = map(int, check_in_str.split(':'))
            cin = time(h, m)
            
        cout = None
        if check_out_str:
            h, m = map(int, check_out_str.split(':'))
            cout = time(h, m)
            
        if record:
            record.check_in = cin
            record.check_out = cout
            record.status = status
            record.is_manual_override = True
        else:
            new_record = DailyRecord(
                employee_id=employee_id,
                date=date_val,
                check_in=cin,
                check_out=cout,
                status=status,
                is_manual_override=True
            )
            session.add(new_record)
            
        session.commit()
        session.close()
        
        # Trigger recalculation if needed (handled by calculator later)
        return jsonify({'success': True, 'message': 'تم تحديث الحضور بنجاح'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
