@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   Online Ordering System - Concurrent Test
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)

:menu
echo.
echo Select Test Mode:
echo.
echo   1. Basic Test - Custom Users
echo   2. Multi-Level Test - 100/500/1000 users (Recommended)
echo   3. Locust Test - Professional
echo   4. Safety Test
echo   0. Exit
echo.
set /p choice="Enter option (0-4): "

if "%choice%"=="1" goto basic_test
if "%choice%"=="2" goto multi_level_test
if "%choice%"=="3" goto locust_test
if "%choice%"=="4" goto safety_test
if "%choice%"=="0" goto end
echo [ERROR] Invalid option
goto menu

:basic_test
echo.
echo ========================================
echo   Basic Concurrent Test
echo ========================================
echo.
echo Checking server...
python -c "import requests; requests.get('http://localhost:5000', timeout=3)" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Cannot connect to http://localhost:5000
    echo Please start the application first
    pause
    goto menu
)

echo Server OK!
echo.
echo Select concurrent users:
echo   1. 50 users
echo   2. 100 users
echo   3. 500 users
echo   4. 1000 users
echo   5. Custom
echo.
set /p users_choice="Enter option (1-5): "

if "%users_choice%"=="1" set concurrent_users=50
if "%users_choice%"=="2" set concurrent_users=100
if "%users_choice%"=="3" set concurrent_users=500
if "%users_choice%"=="4" set concurrent_users=1000
if "%users_choice%"=="5" (
    set /p concurrent_users="Enter number of users: "
)

if not defined concurrent_users (
    echo [ERROR] Invalid option
    pause
    goto basic_test
)

echo.
echo Starting test with %concurrent_users% concurrent users...
echo.
python concurrent_test.py --users %concurrent_users%
echo.
echo Test completed!
echo.
pause
goto menu

:multi_level_test
echo.
echo ========================================
echo   Multi-Level Comparison Test
echo ========================================
echo.
echo Checking server...
python -c "import requests; requests.get('http://localhost:5000', timeout=3)" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Cannot connect to http://localhost:5000
    echo Please start the application first
    pause
    goto menu
)

echo Server OK!
echo.
echo This test will run:
echo   - 100 concurrent users
echo   - 500 concurrent users
echo   - 1000 concurrent users
echo.
echo WARNING: This will take 10-20 minutes
echo.
set /p confirm="Confirm? (Y/N): "
if /i not "%confirm%"=="Y" goto menu

echo.
echo Starting multi-level test...
echo.
python multi_level_test.py
echo.
echo All tests completed!
echo.
pause
goto menu

:locust_test
echo.
echo ========================================
echo   Locust Stress Test
echo ========================================
echo.

REM Check if locust is installed
python -c "import locust" 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Locust not found, installing...
    pip install locust
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install Locust
        pause
        goto menu
    )
)

echo Locust ready!
echo.
echo Starting Locust...
echo.
echo Open browser: http://localhost:8089
echo.
echo Settings:
echo   - Number of users: 50-100
echo   - Spawn rate: 10
echo   - Host: http://localhost:5000
echo.
echo Press Ctrl+C to stop
echo.

locust -f locust_test.py --host=http://localhost:5000

goto menu

:safety_test
echo.
echo ========================================
echo   Concurrent Safety Test
echo ========================================
echo.
echo This test will simulate 10 threads registering
echo the same username to verify conflict handling
echo.
pause

python -c "from concurrent_test import test_concurrent_registration; test_concurrent_registration()"

echo.
pause
goto menu

:end
echo.
echo Thank you!
echo.
exit /b 0
