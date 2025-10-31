@echo off
echo ========================================
echo Digital Watermarking Application
echo Starting Both Backend and Frontend
echo ========================================
echo.

echo Starting Backend (Flask API)...
start cmd /k "cd backend && python api.py"

timeout /t 3 /nobreak > nul

echo.
echo Starting Frontend (React App)...
start cmd /k "cd frontend && npm start"

echo.
echo Both servers are starting...
echo Backend: http://localhost:5000
echo Frontend: http://localhost:3000
echo.
echo Close this window or the opened command windows to stop the servers.
echo.

pause

