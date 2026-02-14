from datetime import date, datetime

class MockLoan:
    def __init__(self, start_date, installments_count, excluded_months=""):
        self.date = start_date
        self.installments_count = installments_count
        self.excluded_months = excluded_months

    @property
    def end_date(self):
        """Logic copied EXACTLY from database_models.py after fix"""
        if not self.date or self.installments_count <= 0:
            return None
            
        excluded = []
        if self.excluded_months:
            for m in self.excluded_months.split(','):
                token = m.strip()
                if not token:
                    continue
                try:
                    excluded.append(int(token))
                except ValueError:
                    try:
                        f = float(token)
                        if f.is_integer():
                            excluded.append(int(f))
                        else:
                            continue
                    except ValueError:
                        continue
        
        current_check_date = self.date
        installments_paid = 0
        
        for _ in range(120):
            if installments_paid >= self.installments_count:
                break
                
            c_month = current_check_date.month
            c_year = current_check_date.year
            
            # The 'deadline' for this installment is the 25th of its month
            deadline = date(c_year, c_month, 25)
            
            if deadline < self.date:
                # Move to next month
                nm = c_month + 1
                ny = c_year
                if nm > 12:
                    nm = 1
                    ny += 1
                current_check_date = date(ny, nm, min(self.date.day, 28))
                continue

            if c_month not in excluded:
                installments_paid += 1
            
            if installments_paid < self.installments_count:
                # Move to next month for next iteration
                nm = c_month + 1
                ny = c_year
                if nm > 12:
                    nm = 1
                    ny += 1
                current_check_date = date(ny, nm, min(self.date.day, 28))
            else:
                # This IS the final month
                return date(c_year, c_month, 25)
                
        return date(current_check_date.year, current_check_date.month, 25)

# Test cases
tests = [
    (date(2025, 12, 10), 1, "2025-12-25"), # Dec 10, 1 inst -> Dec 25
    (date(2025, 12, 28), 1, "2026-01-25"), # Dec 28, 1 inst -> Jan 25
    (date(2025, 12, 6), 2, "2026-01-25"),  # Emp 148: Dec 6, 2 inst -> Jan 25
    (date(2025, 12, 10), 2, "2026-01-25"), # Dec 10, 2 inst -> Jan 25
    (date(2025, 12, 28), 2, "2026-02-25"), # Dec 28, 2 inst -> Feb 25
]

for start, count, expected in tests:
    loan = MockLoan(start, count)
    actual = loan.end_date.strftime("%Y-%m-%d")
    print(f"Start: {start}, Count: {count} | Expected: {expected}, Actual: {actual} | {'OK' if actual == expected else 'FAIL'}")
