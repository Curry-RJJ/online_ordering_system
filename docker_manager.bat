@echo off
chcp 65001 >nul
title 在线订餐系统 - Docker管理工具

:menu
cls
echo ╔════════════════════════════════════════════════════════════╗
echo ║          在线订餐系统 - Docker 一键管理工具              ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo  [1] 🚀 首次部署（自动配置环境）
echo  [2] ▶️  启动项目
echo  [3] ⏸️  停止项目
echo  [4] 🔄 重启项目
echo  [5] 📊 查看运行状态
echo  [6] 📝 查看实时日志
echo  [7] 🌐 打开浏览器访问
echo  [8] 🗑️  清理所有数据（危险操作）
echo  [9] ⚙️  高级选项
echo  [0] 🚪 退出
echo.
echo ════════════════════════════════════════════════════════════
set /p choice=请选择操作 [0-9]: 

if "%choice%"=="1" goto first_deploy
if "%choice%"=="2" goto start
if "%choice%"=="3" goto stop
if "%choice%"=="4" goto restart
if "%choice%"=="5" goto status
if "%choice%"=="6" goto logs
if "%choice%"=="7" goto open_browser
if "%choice%"=="8" goto cleanup
if "%choice%"=="9" goto advanced
if "%choice%"=="0" goto exit
goto menu

:first_deploy
cls
echo ╔════════════════════════════════════════════════════════════╗
echo ║                      首次部署向导                          ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM 检查Docker是否安装
echo [1/5] 检查 Docker 是否安装...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到 Docker！
    echo.
    echo 请先安装 Docker Desktop:
    echo https://www.docker.com/products/docker-desktop/
    echo.
    pause
    goto menu
)
echo ✅ Docker 已安装

REM 检查Docker是否运行
echo [2/5] 检查 Docker 是否运行...
docker ps >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker 未运行！
    echo.
    echo 请先启动 Docker Desktop，然后重试。
    echo.
    pause
    goto menu
)
echo ✅ Docker 正在运行

REM 创建.env文件
echo [3/5] 配置环境变量...
if exist .env (
    echo ⚠️  .env 文件已存在，跳过创建
) else (
    echo 创建 .env 文件...
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
    echo ✅ .env 文件创建成功
)

REM 设置entrypoint.sh权限（Windows下通过git bash或WSL）
echo [4/5] 设置脚本权限...
if exist "C:\Program Files\Git\bin\bash.exe" (
    "C:\Program Files\Git\bin\bash.exe" -c "chmod +x entrypoint.sh" 2>nul
    echo ✅ 脚本权限设置完成
) else (
    echo ⚠️  未找到 Git Bash，跳过权限设置
)

REM 构建并启动
echo [5/5] 构建并启动服务...
echo.
echo ⏳ 首次启动需要下载镜像，可能需要 3-5 分钟...
echo.
docker-compose up -d --build
if errorlevel 1 (
    echo.
    echo ❌ 启动失败！请查看上方错误信息。
    echo.
    pause
    goto menu
)

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                    🎉 部署成功！                           ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 📍 访问地址: http://localhost:5000
echo 👤 测试账号: admin / admin123
echo.
echo ⏳ 等待服务完全启动（约30秒）...
timeout /t 5 /nobreak >nul
echo.
set /p open_now=是否现在打开浏览器？ (Y/N): 
if /i "%open_now%"=="Y" start http://localhost:5000
echo.
pause
goto menu

:start
cls
echo 启动项目...
docker-compose up -d
echo.
echo ✅ 项目已启动！
echo 📍 访问地址: http://localhost:5000
echo.
pause
goto menu

:stop
cls
echo 停止项目...
docker-compose down
echo.
echo ✅ 项目已停止！
echo.
pause
goto menu

:restart
cls
echo 重启项目...
docker-compose restart
echo.
echo ✅ 项目已重启！
echo.
pause
goto menu

:status
cls
echo ════════════════════════════════════════════════════════════
echo                      运行状态
echo ════════════════════════════════════════════════════════════
echo.
docker-compose ps
echo.
echo ════════════════════════════════════════════════════════════
pause
goto menu

:logs
cls
echo ════════════════════════════════════════════════════════════
echo                  实时日志（按 Ctrl+C 退出）
echo ════════════════════════════════════════════════════════════
echo.
docker-compose logs -f
goto menu

:open_browser
start http://localhost:5000
echo ✅ 已打开浏览器
timeout /t 2 /nobreak >nul
goto menu

:cleanup
cls
echo ╔════════════════════════════════════════════════════════════╗
echo ║                  ⚠️  危险操作警告                         ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 此操作将：
echo  - 停止并删除所有容器
echo  - 删除数据库数据
echo  - 删除所有 Docker 卷
echo.
echo ⚠️  所有数据将永久丢失！
echo.
set /p confirm=确认删除所有数据？输入 YES 继续: 
if /i not "%confirm%"=="YES" (
    echo 已取消操作
    timeout /t 2 /nobreak >nul
    goto menu
)

echo.
echo 正在清理...
docker-compose down -v
echo.
echo ✅ 清理完成！
echo.
pause
goto menu

:advanced
cls
echo ╔════════════════════════════════════════════════════════════╗
echo ║                      高级选项                              ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo  [1] 查看 Web 应用日志
echo  [2] 查看 MySQL 日志
echo  [3] 进入 Web 容器
echo  [4] 进入 MySQL 容器
echo  [5] 重新构建镜像
echo  [6] 查看资源占用
echo  [7] 备份数据库
echo  [0] 返回主菜单
echo.
set /p adv_choice=请选择操作 [0-7]: 

if "%adv_choice%"=="1" (
    docker-compose logs web
    pause
    goto advanced
)
if "%adv_choice%"=="2" (
    docker-compose logs mysql
    pause
    goto advanced
)
if "%adv_choice%"=="3" (
    echo 进入 Web 容器（输入 exit 退出）...
    docker-compose exec web bash
    goto advanced
)
if "%adv_choice%"=="4" (
    echo 进入 MySQL 容器（输入 exit 退出）...
    docker-compose exec mysql bash
    goto advanced
)
if "%adv_choice%"=="5" (
    echo 重新构建镜像...
    docker-compose build --no-cache
    echo ✅ 构建完成！
    pause
    goto advanced
)
if "%adv_choice%"=="6" (
    docker stats --no-stream
    pause
    goto advanced
)
if "%adv_choice%"=="7" (
    set backup_file=backup_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.sql
    set backup_file=%backup_file: =0%
    echo 正在备份数据库到 %backup_file%...
    docker-compose exec -T mysql mysqldump -u root -proot123456 meituan_waimai > %backup_file%
    echo ✅ 备份完成: %backup_file%
    pause
    goto advanced
)
if "%adv_choice%"=="0" goto menu
goto advanced

:exit
cls
echo.
echo 感谢使用！再见 👋
echo.
timeout /t 2 /nobreak >nul
exit

:error
echo.
echo ❌ 发生错误，请查看上方信息
echo.
pause
goto menu

