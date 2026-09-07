@echo off
echo =======================================================
echo Starting Polar EMS Dashboard
echo =======================================================

echo Starting Backend Server (with -B to prevent __pycache__)...
start "Polar EMS Backend" cmd /k "python -B -m backend.app.main"

echo Starting Frontend Server...
start "Polar EMS Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Both servers have been launched in separate windows!
echo You can close those windows to stop the servers.
echo =======================================================
