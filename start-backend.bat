@echo off
echo ========================================
echo Starting Digital Watermarking Backend
echo ========================================
echo.

cd backend


echo.
echo Starting Flask API server on http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

python api.py

pause

