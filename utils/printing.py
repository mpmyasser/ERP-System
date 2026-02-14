"""
Printing Module
===============
Functions for generating printable HTML documents (payslips, employee cards, etc.)
"""


def generate_payslip_html(salary_data, month, year):
    """
    Generate HTML for payslip printing
    
    Args:
        salary_data: Dictionary containing salary information
        month: Month number
        year: Year number
        
    Returns:
        str: HTML string ready for printing
    """
    html = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>Payslip</title>
        <style>
            body {{ font-family: 'Tajawal', sans-serif; direction: rtl; text-align: right; padding: 20px; }}
            .header {{ text-align: center; margin-bottom: 20px; border-bottom: 2px solid #333; padding-bottom: 10px; }}
            .details {{ width: 100%; margin-bottom: 20px; }}
            .details td {{ padding: 5px; }}
            .salary-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            .salary-table th, .salary-table td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
            .salary-table th {{ background-color: #f2f2f2; }}
            .total {{ font-weight: bold; font-size: 1.2em; margin-top: 20px; text-align: left; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>قسيمة راتب</h1>
            <h3>شهر: {month} / {year}</h3>
        </div>
        
        <table class="details">
            <tr>
                <td><strong>اسم الموظف:</strong> {salary_data['Employee']}</td>
                <td><strong>الراتب الأساسي:</strong> {salary_data['Basic Salary']:.2f}</td>
            </tr>
        </table>
        
        <table class="salary-table">
            <thead>
                <tr>
                    <th>البند</th>
                    <th>القيمة</th>
                    <th>ملاحظات</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>قيمة الإضافي</td>
                    <td>{salary_data['OT Value']:.2f}</td>
                    <td></td>
                </tr>
                <tr>
                    <td>المكافآت</td>
                    <td>{salary_data['Bonuses']:.2f}</td>
                    <td></td>
                </tr>
                <tr>
                    <td>خصم التأخير</td>
                    <td>{salary_data['Late Penalty']:.2f}</td>
                    <td></td>
                </tr>
                <tr>
                    <td>خصم الغياب</td>
                    <td>{salary_data['Absence Deduction']:.2f}</td>
                    <td></td>
                </tr>
                <tr>
                    <td>خصم القروض</td>
                    <td>{salary_data['Loan Deduction']:.2f}</td>
                    <td></td>
                </tr>
                <tr>
                    <td>جزاءات أخرى</td>
                    <td>{salary_data['Other Penalties']:.2f}</td>
                    <td></td>
                </tr>
                <tr>
                    <td>تأمين اجتماعي</td>
                    <td>{salary_data['Insurance']:.2f}</td>
                    <td></td>
                </tr>
            </tbody>
        </table>
        
        <div class="total">
            صافي الراتب: {salary_data['Net Salary']:.2f} جنيه
        </div>
        
        <script>
            window.print();
        </script>
    </body>
    </html>
    """
    return html


def generate_employee_card_html(emp, qr_code_b64):
    """
    Generate HTML for employee card printing
    
    Args:
        emp: Employee object
        qr_code_b64: Base64 encoded QR code string
        
    Returns:
        str: HTML string ready for printing
    """
    html = f"""
    <div style="display: flex; justify-content: center; align-items: center; min-height: 300px;">
        <div style="
            border: 2px solid #333;
            padding: 12px;
            width: 335px;
            height: 215px;
            text-align: center;
            direction: rtl;
            font-family: 'Tajawal', Arial, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            font-size: 12px;
        ">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px;">
                <div style="flex: 1; text-align: right;">
                    <h4 style="margin: 0; color: #2c3e50; font-size: 11px; font-weight: bold;">بطاقة موظف</h4>
                    <p style="margin: 3px 0; font-size: 10px;"><strong>الكود:</strong> {emp.code}</p>
                    <p style="margin: 3px 0; font-size: 10px;"><strong>الاسم:</strong> {emp.name}</p>
                    <p style="margin: 3px 0; font-size: 9px;"><strong>الوظيفة:</strong> {emp.job_title}</p>
                    <p style="margin: 3px 0; font-size: 9px;"><strong>القسم:</strong> {emp.department.name if emp.department else 'غير محدد'}</p>
                </div>
                <img src="data:image/png;base64,{qr_code_b64}" alt="QR Code" style="width: 80px; height: 80px; flex-shrink: 0;">
            </div>
        </div>
    </div>
    <style>
        @media print {{
            body {{ margin: 0; padding: 0; }}
            div[style*="min-height: 300px"] {{ display: flex; justify-content: center; page-break-inside: avoid; }}
        }}
    </style>
    <script>
        setTimeout(() => window.print(), 500);
    </script>
    """
    return html
