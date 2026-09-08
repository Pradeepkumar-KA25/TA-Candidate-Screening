@echo off
setlocal

set "ROOT=%~dp0"

where py >nul 2>nul
if errorlevel 1 (
    echo Python Launcher was not found. Install Python 3.11 or later and try again.
    exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
    echo npm was not found. Install Node.js 20 or later and try again.
    exit /b 1
)

echo.
echo Setting up backend...
pushd "%ROOT%backend"

if not exist ".venv\Scripts\python.exe" (
    py -3 -m venv .venv
    if errorlevel 1 goto :error
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
if errorlevel 1 goto :error

python -m pip install -r requirements.txt
if errorlevel 1 goto :error

if not exist ".env" (
    copy /Y ".env.example" ".env" >nul
    echo Created backend\.env from .env.example.
    echo Update DATABASE_URL and optional Zoho settings before continuing if needed.
)

echo Applying database migrations...
python -m alembic -c alembic.ini upgrade head
if errorlevel 1 goto :error

popd

echo.
echo Setting up frontend...
pushd "%ROOT%frontend"
npm ci
if errorlevel 1 goto :error

popd
echo.
echo Setup completed successfully.
echo PostgreSQL must remain running while using the application.
echo Run run.bat to start the backend and frontend.
exit /b 0

:error
set "EXIT_CODE=%errorlevel%"
popd
echo.
echo Setup failed. Confirm PostgreSQL is running and backend\.env has a valid DATABASE_URL.
exit /b %EXIT_CODE%