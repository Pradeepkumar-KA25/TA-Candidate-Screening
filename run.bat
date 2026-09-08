@echo off
setlocal

set "ROOT=%~dp0"

if not exist "%ROOT%backend\.venv\Scripts\python.exe" (
    echo Backend environment is missing. Run setup.bat first.
    exit /b 1
)

if not exist "%ROOT%frontend\node_modules" (
    echo Frontend dependencies are missing. Run setup.bat first.
    exit /b 1
)

if not exist "%ROOT%backend\.env" (
    echo Backend configuration is missing. Run setup.bat first and update backend\.env.
    exit /b 1
)

echo Starting backend at http://127.0.0.1:8000...
start "Talent Acquisition Backend" /D "%ROOT%backend" cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --reload"

echo Starting frontend at http://localhost:4200...
start "Talent Acquisition Frontend" /D "%ROOT%frontend" cmd /k "npm run start"

echo.
echo Application launch commands sent. Keep both new terminal windows open while using the application.
echo Open http://localhost:4200 in your browser.
endlocal