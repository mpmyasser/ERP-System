# PATCH: Add to loans.py after "loans_bp = Blueprint('loans', __name__)"

def _get_loans_data(date_from=None, date_to=None, department_ids=None, dept_filter_mode='include', search_code=''):
    """Shared function to get loans data"""
    db = current_app.db
    if search_code:
        department_ids = []
    return db.search_loans(
        date_from=date_from, 
        date_to=date_to, 
        department_ids=department_ids, 
        dept_filter_mode=dept_filter_mode, 
        code=search_code
    )

@loans_bp.route('/api/data')
def api_data():
    """API endpoint for AJAX DataTable"""
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    department_ids = request.args.getlist('department_ids', type=int)
    if not department_ids and request.args.get('department_id'):
        department_ids = [request.args.get('department_id', type=int)]
    dept_filter_mode = request.args.get('dept_filter_mode', 'include')
    search_code = request.args.get('search_code', '').strip()
    
    loans = _get_loans_data(date_from, date_to, department_ids, dept_filter_mode, search_code)
    
    data = []
    for loan in loans:
        data.append({
            'id': loan.id,
            'code': loan.employee.code if loan.employee else '-',
            'name': loan.employee.name if loan.employee else '-',
            'department': loan.employee.department.name if loan.employee and loan.employee.department else '-',
            'date': loan.date.strftime('%d/%m/%Y') if loan.date else '-',
            'type': loan.type,
            'amount': loan.amount,
            'installment_value': loan.installment_value,
            'installments_count': loan.installments_count,
            'excluded_months': loan.excluded_months or '-',
            'end_date': loan.end_date.strftime('%d/%m/%Y') if loan.end_date else '-',
            'remaining_balance': loan.auto_remaining_balance,
            'status': loan.status
        })
    
    return {'data': data}

# PATCH: Modify list() function - replace the loans query section with:
# loans = _get_loans_data(date_from, date_to, department_ids, dept_filter_mode, search_code)
