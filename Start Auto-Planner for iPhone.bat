@echo off
title Auto-Planner - iPhone Test
cd /d "%~dp0"

echo.
echo   ==========================================
echo     Starting Auto-Planner for iPhone testing
echo   ==========================================
echo.
echo   Use this only when your iPhone and computer are on the same Wi-Fi.
echo   Your Wi-Fi IP is shown below only so your phone can reach this computer.
echo   It does not publish the app to the internet.
echo.

for /f "tokens=2 delims=:" %%i in ('ipconfig ^| findstr /C:"IPv4 Address"') do if not defined LOCAL_IP set LOCAL_IP=%%i
if defined LOCAL_IP set LOCAL_IP=%LOCAL_IP: =%

echo   Computer: http://localhost:8600
if defined LOCAL_IP (
    echo   iPhone:   http://%LOCAL_IP%:8600
) else (
    echo   iPhone:   Could not find Wi-Fi IP automatically. Run ipconfig and use your IPv4 Address.
)
echo.
echo   Keep this window open while you test.
echo   Close this window to stop the app.
echo.

REM Install dependencies only if Streamlit isn't already available (first run)
python -c "import streamlit, pandas" 2>nul
if errorlevel 1 (
    echo   First run: installing dependencies, please wait...
    python -m pip install --disable-pip-version-check -r requirements.txt
)

REM Open the computer browser too, so you can confirm the app is running
start "" /b cmd /c "timeout /t 5 >nul & start http://localhost:8600"

REM Launch the app on the local network for phone testing
python -m streamlit run student_auto_planner.py --server.address 0.0.0.0 --server.port 8600

echo.
echo   Auto-Planner has stopped. Press any key to close.
pause >nul
