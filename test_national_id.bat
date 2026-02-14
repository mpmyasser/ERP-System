@echo off
REM Egyptian National ID Parser Test
REM اختبار نظام استخراج البيانات من الرقم القومي

echo.
echo ======================================================================
echo  Egyptian National ID Parser - Test Suite
echo  اختبار نظام استخراج البيانات من الرقم القومي
echo ======================================================================
echo.

REM Run the test
python test_national_id_parser.py

if %errorlevel% equ 0 (
    echo.
    echo SUCCESS: All tests passed!
    echo.
    pause
) else (
    echo.
    echo ERROR: Some tests failed!
    echo.
    pause
)
