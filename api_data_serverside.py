# UPDATED api_data() function with server-side pagination
# Replace the existing api_data() in app/routes/loans.py

@loans_bp.route('/api/data')
def api_data():
    """API endpoint for AJAX DataTable with server-side pagination"""
    # DataTable parameters
    draw = request.args.get('draw', 1, type=int)
    start = request.args.get('start', 0, type=int)
    length = request.args.get('length', 25, type=int)
    
    # Filter parameters
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    department_ids = request.args.getlist('department_ids', type=int)
    if not department_ids and request.args.get('department_id'):
        department_ids = [request.args.get('department_id', type=int)]
    dept_filter_mode = request.args.get('dept_filter_mode', 'include')
    search_code = request.args.get('search_code', '').strip()
    
    # Get all matching loans
    loans = _get_loans_data(date_from, date_to, department_ids, dept_filter_mode, search_code)
    records_filtered = len(loans)
    
    # Apply pagination
    loans_page = loans[start:start + length]
    
    # Format data
    data = []
    for loan in loans_page:
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
    
    return {
        'draw': draw,
        'recordsTotal': records_filtered,
        'recordsFiltered': records_filtered,
        'data': data
    }
