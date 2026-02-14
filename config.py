"""
Configuration Settings for HR System
"""

# ============ Late & Early Departure Settings ============
LATE_GRACE_PERIOD_MINUTES = 10       # Grace period in minutes
LATE_MULTIPLIER = 1                  # Deduction multiplier after grace period
Early_DEPARTURE_GRACE_PERIOD_MINUTES = 0
EARLY_DEPARTURE_MULTIPLIER = 1

# ============ Overtime Settings ============
OVERTIME_MIN_MINUTES = 60            # Must complete 60 minutes to qualify for OT
OVERTIME_RATE = 1.5                  # Rate is 1.5x after qualifying
