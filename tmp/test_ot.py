OVERTIME_MIN_MINUTES = 60
OVERTIME_FIRST_HOUR_FIXED = True
OVERTIME_ROUNDING_MODE = 'HALF_HOUR'
OVERTIME_ROUND_THRESHOLD_MINUTES = 30

def calculate_overtime_hours_rounded(total_minutes):
    if total_minutes < OVERTIME_MIN_MINUTES:
        return 0.0
    threshold = OVERTIME_ROUND_THRESHOLD_MINUTES
    def _round_rem(rem):
        if rem < threshold: return 0.0
        elif rem == threshold: return 0.5
        else: return 1.0
    if OVERTIME_FIRST_HOUR_FIXED:
        remaining = total_minutes - 60.0
        return 1.0 + _round_rem(remaining)
    else:
        full = int(total_minutes // 60)
        rem = total_minutes % 60
        return full + _round_rem(rem)

# salary = 2500, work_hours = 10, days = 26, ot_rate = 1.5
salary = 2500
work_hours = 10
days = 26
ot_rate = 1.5
hourly = (salary / days) / work_hours
ot_hourly = hourly * ot_rate

cases = [
    ('19:29', 89),  # expected: 1 hour
    ('19:30', 90),  # expected: 1.5 hours
    ('19:31', 91),  # expected: 2 hours
    ('20:00', 120), # expected: 2 hours
    ('20:02', 122), # expected: 2 hours (< 30 remainder)
    ('18:30', 30),  # expected: 0 (below min)
    ('18:59', 59),  # expected: 0 (below min)
]

for label, minutes in cases:
    h = calculate_overtime_hours_rounded(minutes)
    pay = h * ot_hourly
    print("Exit %s: %d min => %.1f hrs => %.2f gineh" % (label, minutes, h, pay))
