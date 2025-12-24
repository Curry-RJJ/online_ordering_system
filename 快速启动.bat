@echo off
chcp 65001 >nul
title 快速启动 - 在线订餐系统

echo.
echo ════════════════════════════════════════════════════════════
echo              🚀 在线订餐系统 - 快速启动
echo ════════════════════════════════════════════════════════════
echo.

REM 检查是否首次运行
if not exist .env (
    echo 检测到首次运行，正在初始化...
    echo.
    
    REM 检查Docker
    docker --version >nul 2>&1
    if errorlevel 1 (
        echo ❌ 未检测到 Docker！
        echo.
        echo 请先安装 Docker Desktop:
        echo https://www.docker.com/products/docker-desktop/
        echo.
        pause
        exit
    )
    
    REM 检查Docker是否运行
    docker ps >nul 2>&1
    if errorlevel 1 (
        echo ❌ Docker 未运行！
        echo.
        echo 请先启动 Docker Desktop，然后重试。
        echo.
        pause
        exit
    )
    
    REM 创建.env文件
    (
        echo # Flask配置
        echo FLASK_ENV=production
        echo SECRET_KEY=meituan-secret-key-2024-%RANDOM%%RANDOM%
        echo.
        echo # MySQL配置
        echo MYSQL_ROOT_PASSWORD=root123456
        echo MYSQL_DATABASE=meituan_waimai
        echo MYSQL_USER=meituan_user
        echo MYSQL_PASSWORD=meituan_pass
        echo MYSQL_PORT=3307
        echo.
        echo # Web端口
        echo WEB_PORT=5000
    ) > .env
    
    echo ✅ 配置完成！
    echo.
    echo ⏳ 首次启动需要 3-5 分钟下载镜像...
    echo.
    docker-compose up -d --build
) else (
    echo ⏳ 启动服务中...
    echo.
    docker-compose up -d
)

if errorlevel 1 (
    echo.
    echo ❌ 启动失败！请查看上方错误信息。
    echo.
    pause
    exit
)

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                    ✅ 启动成功！                           ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 📍 访问地址: http://localhost:5000
echo 👤 测试账号: admin / admin123
echo.
echo 💡 提示：
echo    - 双击 "docker_manager.bat" 可使用完整管理功能
echo    - 双击 "停止项目.bat" 可停止服务
echo.

timeout /t 3 /nobreak >nul
start http://localhost:5000

echo ✅ 已自动打开浏览器
echo.
pause

