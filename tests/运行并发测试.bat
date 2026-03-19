@echo off
chcp 65001 >nul
echo.
echo ====================================
echo    在线订餐系统 - 并发测试工具
echo ====================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

:menu
echo.
echo 请选择测试方式：
echo.
echo   1. 基础并发测试 - 自定义并发数
echo      可选择 50/100/500/1000 并发用户
echo      生成详细测试报告
echo.
echo   2. 多级别对比测试 - 推荐
echo      自动运行 100/500/1000 并发测试
echo      生成性能对比报告
echo      分析性能趋势
echo.
echo   3. Locust压力测试 - 专业测试
echo      提供Web UI界面
echo      实时监控测试数据
echo      动态调整并发数
echo.
echo   4. 快速并发安全性测试
echo      只测试用户注册的并发安全性
echo      验证唯一性约束
echo.
echo   0. 退出
echo.
set /p choice="请输入选项 (0-4): "

if "%choice%"=="1" goto basic_test
if "%choice%"=="2" goto multi_level_test
if "%choice%"=="3" goto locust_test
if "%choice%"=="4" goto safety_test
if "%choice%"=="0" goto end
echo [错误] 无效的选项，请重新选择
goto menu

:basic_test
echo.
echo ====================================
echo       运行基础并发测试
echo ====================================
echo.
echo 检查服务器连接...
python -c "import requests; requests.get('http://localhost:5000', timeout=3)" 2>nul
if %errorlevel% neq 0 (
    echo [错误] 无法连接到服务器 http://localhost:5000
    echo 请先运行 "快速启动.bat" 启动应用
    pause
    goto menu
)

echo 服务器连接成功！
echo.
echo 请选择并发用户数：
echo   1. 50  并发用户 - 轻量级测试
echo   2. 100 并发用户 - 中等负载
echo   3. 500 并发用户 - 高负载
echo   4. 1000 并发用户 - 压力测试
echo   5. 自定义并发数
echo.
set /p users_choice="请输入选项 (1-5): "

if "%users_choice%"=="1" set concurrent_users=50
if "%users_choice%"=="2" set concurrent_users=100
if "%users_choice%"=="3" set concurrent_users=500
if "%users_choice%"=="4" set concurrent_users=1000
if "%users_choice%"=="5" (
    set /p concurrent_users="请输入并发用户数: "
)

if not defined concurrent_users (
    echo [错误] 无效的选项
    pause
    goto basic_test
)

echo.
echo 开始测试 %concurrent_users% 个并发用户...
echo.
python concurrent_test.py --users %concurrent_users%
echo.
echo 测试完成！
echo.
pause
goto menu

:multi_level_test
echo.
echo ====================================
echo      多级别并发对比测试
echo ====================================
echo.
echo 检查服务器连接...
python -c "import requests; requests.get('http://localhost:5000', timeout=3)" 2>nul
if %errorlevel% neq 0 (
    echo [错误] 无法连接到服务器 http://localhost:5000
    echo 请先运行 "快速启动.bat" 启动应用
    pause
    goto menu
)

echo 服务器连接成功！
echo.
echo 此测试将依次运行：
echo   - 100 并发用户测试
echo   - 500 并发用户测试
echo   - 1000 并发用户测试
echo.
echo 警告：完整测试需要较长时间，约10-20分钟
echo.
set /p confirm="确认开始测试？(Y/N): "
if /i not "%confirm%"=="Y" goto menu

echo.
echo 开始多级别测试...
echo.
python multi_level_test.py
echo.
echo 所有测试完成！
echo.
pause
goto menu

:locust_test
echo.
echo ====================================
echo      运行 Locust 压力测试
echo ====================================
echo.

REM 检查是否安装了locust
python -c "import locust" 2>nul
if %errorlevel% neq 0 (
    echo [提示] 未检测到Locust，正在安装...
    pip install locust
    if %errorlevel% neq 0 (
        echo [错误] Locust安装失败
        pause
        goto menu
    )
)

echo Locust已就绪！
echo.
echo 启动中...
echo.
echo 请在浏览器中访问: http://localhost:8089
echo.
echo 设置建议：
echo   - Number of users: 50-100 (并发用户数)
echo   - Spawn rate: 10 (每秒启动用户数)
echo   - Host: http://localhost:5000
echo.
echo 按 Ctrl+C 可停止测试
echo.

locust -f locust_test.py --host=http://localhost:5000

goto menu

:safety_test
echo.
echo ====================================
echo     并发安全性测试（用户注册）
echo ====================================
echo.
echo 此测试将模拟10个线程同时注册相同用户名
echo 用于验证系统是否正确处理并发冲突
echo.
pause

python -c "from concurrent_test import test_concurrent_registration; test_concurrent_registration()"

echo.
pause
goto menu

:end
echo.
echo 感谢使用！
echo.
exit /b 0
