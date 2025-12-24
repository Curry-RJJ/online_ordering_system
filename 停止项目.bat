@echo off
chcp 65001 >nul
title 停止项目 - 在线订餐系统

echo.
echo ════════════════════════════════════════════════════════════
echo              ⏸️  停止在线订餐系统
echo ════════════════════════════════════════════════════════════
echo.
echo ⏳ 正在停止服务...
echo.

docker-compose down

if errorlevel 1 (
    echo.
    echo ❌ 停止失败！
    echo.
) else (
    echo.
    echo ✅ 服务已停止！
    echo.
    echo 💡 提示：数据已保存，下次启动时数据不会丢失
    echo.
)

pause

