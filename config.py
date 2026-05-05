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
OVERTIME_FIRST_HOUR_FIXED = True     # First qualifying hour counts as exactly 1 full hour
OVERTIME_ROUNDING_MODE = "HALF_HOUR" # Rounding mode for time beyond first hour
OVERTIME_ROUND_THRESHOLD_MINUTES = 30 # Minutes needed to round up to next 0.5 hour
