@echo off
echo ========================================================
echo   CertChain: Production WSGI Server (Waitress)
echo   Smart Contract: Solidity 0.8.20 on Ethereum
echo ========================================================
echo.

if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
)

echo [INFO] Starting production WSGI server on port 5000...
echo Portal accessible at: http://127.0.0.1:5000
echo.
python prod.py
pause
