@echo off
echo ========================================================
echo   CertChain: Smart Contract Deployment Utility
echo   Solidity: CertificateVerification.sol (0.8.20)
echo ========================================================
echo.

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python deploy.py %*
echo.
pause
