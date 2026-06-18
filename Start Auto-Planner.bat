@echo off
title Auto-Planner - Computer Test
cd /d "%~dp0"

echo.
echo   ==========================================
echo     Starting Auto-Planner for this computer
echo   ==========================================
echo.
echo   This opens only on this computer:
echo   http://localhost:8600
echo.
echo   No Wi-Fi IP address is shown or shared in this mode.
echo   Keep this window open while you use the app.
echo   Close this window to stop the app.
echo.

REM Install dependencies only if Streamlit isn't already available (first run)
python -c "import streamlit, pandas" 2>nul
if errorlevel 1 (
    echo   First run: installing dependencies, please wait...
    python -m pip install --disable-pip-version-check -r requirements.txt
)

REM Open the browser once the server has had a moment to boot
start "" /b cmd /c "timeout /t 5 >nul & start http://localhost:8600"

REM Launch the app in computer-only mode
python -m streamlit run student_auto_planner.py --server.address localhost --server.port 8600

echo.
echo   Auto-Planner has stopped. Press any key to close.
pause >nul
