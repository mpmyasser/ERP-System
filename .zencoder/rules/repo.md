---
description: Repository Information Overview
alwaysApply: true
---

# HR System Application Information

## Summary

This is a **Python-based Human Resources Management System** built with Streamlit, providing a comprehensive web interface for managing employees, attendance tracking, payroll processing, loans, and penalties/bonuses. The system uses SQLAlchemy ORM with SQLite database backend and supports bulk employee imports from Excel files. It includes QR code generation and features a localized interface (Arabic/English). The application is primarily designed for HR departments to manage employee data, calculate payroll, and track attendance records.

## Structure

```
H.R/
├── app.py                 # Main Streamlit web application (36.6 KB)
├── database_models.py     # SQLAlchemy ORM models for all database entities
├── db_manager.py          # Database connection and session management
├── payroll_processor.py   # Payroll calculation engine
├── utils.py               # Utility functions for common operations
├── update_schema.py       # Database schema migrations
├── test_calculations.py   # Unit tests for payroll calculations
├── requirements.txt       # Python dependencies
├── run_app.bat           # Windows batch startup script
├── style.css             # Custom CSS styling for Streamlit UI
├── hr_system.db          # Production SQLite database
├── test_hr.db            # Test SQLite database
├── cleanup_dbs.py        # Database cleanup utility
├── Bulk Import.xlsx      # Excel template for bulk employee import
└── Bulk Import - Copy.xlsx  # Backup bulk import template
```

## Language & Runtime

**Language**: Python 3 (specifically 3.11 based on compiled bytecode)  
**Web Framework**: Streamlit  
**Database**: SQLite with SQLAlchemy ORM  
**Build System**: No explicit build system; runs as interpreted Python  
**Package Manager**: pip

## Dependencies

**Main Dependencies**:
- **streamlit** - Web application framework for the UI
- **sqlalchemy** - SQL Object-Relational Mapping (ORM)
- **pandas** - Data processing and analysis, Excel handling
- **openpyxl** - Excel file read/write operations for bulk imports
- **qrcode** - QR code generation for employee identification
- **Pillow** - Image processing and manipulation

**Development Dependencies**:
- **unittest** (built-in) - Test framework for payroll calculations

## Build & Installation

**Installation**:
```bash
pip install -r requirements.txt
```

**Running the Application**:
```bash
streamlit run app.py
```

Or use the provided Windows batch script:
```bash
run_app.bat
```

## Main Files & Resources

### Application Entry Point
- **app.py**: Main Streamlit application containing the `HRSystemApp` class with all UI components and user interactions

### Core Modules
- **database_models.py**: Defines all SQLAlchemy ORM models:
  - Employee, Department
  - AttendanceLog, DailyRecord
  - Loan, PenaltyBonus
  - Enums: EmployeeCategory, AttendanceType, DailyStatus, LoanType, PenaltyBonusType, MaritalStatus, MilitaryStatus, WeeklyHoliday, SalaryType

- **db_manager.py**: Database connection management and session handling

- **payroll_processor.py**: PayrollProcessor class for salary calculations, attendance processing, and deduction/bonus calculations

- **utils.py**: Shared utility functions used across the application

- **update_schema.py**: Database migration function for schema updates

### Configuration
- **style.css**: Custom CSS styling for Streamlit components
- **requirements.txt**: Python package dependencies

### Data Files
- **hr_system.db**: Production SQLite database with employee, attendance, and payroll data
- **test_hr.db**: Test database for unit testing
- **Bulk Import.xlsx**: Excel template for importing multiple employees at once

## Testing

**Framework**: unittest (Python built-in)

**Test Location**: `test_calculations.py`

**Test Coverage**: `TestPayrollCalculations` class with payroll calculation logic tests

**Naming Convention**: Test methods follow the `test_*` naming pattern per unittest conventions

**Run Command**:
```bash
python -m unittest test_calculations.py
```

## Features & Capabilities

- **Employee Management**: Create, update, and manage employee records with detailed personal information
- **Attendance Tracking**: Log employee attendance with various attendance types and daily status tracking
- **Payroll Processing**: Automated salary calculations based on employee category and attendance records
- **Loan Management**: Track and process employee loans with flexible loan types
- **Penalties & Bonuses**: Apply penalties and bonuses with customizable types and amounts
- **Bulk Import**: Import multiple employees from Excel files with validation
- **QR Code Generation**: Generate QR codes for employee identification
- **Multi-language Support**: Interface supports both Arabic and English
- **Database Migrations**: Automatic schema updates via migration system
