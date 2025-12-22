@echo off
echo Starting IT Ticket Analytics Dashboard...
echo.
cd /d "%~dp0"
call venv\Scripts\activate.bat
streamlit run src\dashboard.py
pause
