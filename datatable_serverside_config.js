# UPDATED DataTable initialization with server-side pagination
# Replace the AJAX config in app/templates/loans/list.html

        const loansTable = $('#loans-table').DataTable({
            ...defaultDataTableConfig,
            serverSide: true,
            processing: true,
            ajax: {
                url: "{{ url_for('loans.api_data') }}",
                data: function(d) {
                    d.date_from = $('#date-from').val();
                    d.date_to = $('#date-to').val();
                    d.department_ids = $('#dept-filter').val() || [];
                    d.search_code = $('#search-code').val();
                }
            },
            columns: [
                { data: 'code', width: '10%' },
                { data: 'name', width: '15%' },
                { data: 'department', width: '10%' },
                { data: 'date', width: '10%' },
                { 
                    data: 'type', 
                    width: '10%',
                    render: function(data) {
                        if (data === 'monthly' || data === 'permanent') {
                            return '<span class="badge bg-primary">مستديمة</span>';
                        } else if (data === 'emergency' || data === 'temporary') {
                            return '<span class="badge bg-warning text-dark">مؤقتة</span>';
                        }
                        return '<span class="badge bg-secondary">' + data + '</span>';
                    }
                },
                { data: 'amount', width: '10%', render: function(data) { return data.toLocaleString() + ' جنيه'; } },
                { 
                    data: 'status', 
                    width: '8%',
                    render: function(data) {
                        if (data === 'Pending') {
                            return '<span class="badge bg-secondary"><i class="fas fa-clock"></i> بانتظار</span>';
                        } else if (data === 'Approved') {
                            return '<span class="badge bg-success"><i class="fas fa-check"></i> تم الصرف</span>';
                        }
                        return '<span class="badge bg-dark">' + data + '</span>';
                    }
                },
                { data: 'installment_value', width: '10%', render: function(data) { return data.toLocaleString() + ' جنيه'; } },
                { data: 'installments_count', width: '5%' },
                { data: 'excluded_months', width: '10%' },
                { data: 'end_date', width: '10%' },
                { data: 'remaining_balance', width: '12%', render: function(data) { return '<strong class="text-danger">' + data.toLocaleString() + ' جنيه</strong>'; } },
                { 
                    data: 'id', 
                    width: '10%', 
                    orderable: false,
                    render: function(data) {
                        return '<a href="/loans/' + data + '" class="btn btn-sm btn-info" title="عرض"><i class="fas fa-eye"></i></a> ' +
                               '<a href="/loans/' + data + '/edit" class="btn btn-sm btn-warning" title="تعديل"><i class="fas fa-edit"></i></a> ' +
                               '<button class="btn btn-sm btn-danger delete-record-btn" data-module="loans" data-id="' + data + '" data-confirm="هل أنت متأكد من حذف هذه السلفة؟" title="حذف"><i class="fas fa-trash"></i></button>';
                    }
                }
            ],
            order: [[0, 'asc']]
        });
