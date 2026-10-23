@echo off
echo ========================================================
echo   CertChain: Blockchain Certificate Verification System
echo   Smart Contract: Solidity 0.8.20 on Ethereum
echo ========================================================
echo.

if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
)

echo [1/2] Verifying Python Environment & Dependencies...
python requirment.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Dependency verification failed!
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [2/2] Launching Flask Blockchain Application...
echo Access the portal at: http://127.0.0.1:5000
echo Default Institution Admin: admin / admin123
echo.
python app.py
pause
