# 在线订餐系统 - Docker管理工具 (PowerShell版本)
# 编码设置
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Show-Menu {
    Clear-Host
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║          在线订餐系统 - Docker 一键管理工具              ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host " [1] 🚀 首次部署（自动配置环境）" -ForegroundColor Green
    Write-Host " [2] ▶️  启动项目" -ForegroundColor Yellow
    Write-Host " [3] ⏸️  停止项目" -ForegroundColor Yellow
    Write-Host " [4] 🔄 重启项目" -ForegroundColor Yellow
    Write-Host " [5] 📊 查看运行状态" -ForegroundColor Cyan
    Write-Host " [6] 📝 查看实时日志" -ForegroundColor Cyan
    Write-Host " [7] 🌐 打开浏览器访问" -ForegroundColor Magenta
    Write-Host " [8] 🗑️  清理所有数据（危险操作）" -ForegroundColor Red
    Write-Host " [9] ⚙️  高级选项" -ForegroundColor Gray
    Write-Host " [0] 🚪 退出" -ForegroundColor White
    Write-Host ""
    Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
}

function Test-DockerInstalled {
    try {
        docker --version | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

function Test-DockerRunning {
    try {
        docker ps | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

function New-EnvFile {
    $envContent = @"
# Flask配置
FLASK_ENV=production
SECRET_KEY=meituan-secret-key-2024-$(Get-Random -Minimum 10000 -Maximum 99999)

# MySQL配置
MYSQL_ROOT_PASSWORD=root123456
MYSQL_DATABASE=meituan_waimai
MYSQL_USER=meituan_user
MYSQL_PASSWORD=meituan_pass
MYSQL_PORT=3307

# Web端口
WEB_PORT=5000
"@
    
    Set-Content -Path ".env" -Value $envContent -Encoding UTF8
}

function Start-FirstDeploy {
    Clear-Host
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║                      首次部署向导                          ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""

    # 检查Docker
    Write-Host "[1/5] 检查 Docker 是否安装..." -ForegroundColor Yellow
    if (-not (Test-DockerInstalled)) {
        Write-Host "❌ 未检测到 Docker！" -ForegroundColor Red
        Write-Host ""
        Write-Host "请先安装 Docker Desktop:" -ForegroundColor Yellow
        Write-Host "https://www.docker.com/products/docker-desktop/" -ForegroundColor Cyan
        Write-Host ""
        Read-Host "按回车键返回"
        return
    }
    Write-Host "✅ Docker 已安装" -ForegroundColor Green

    Write-Host "[2/5] 检查 Docker 是否运行..." -ForegroundColor Yellow
    if (-not (Test-DockerRunning)) {
        Write-Host "❌ Docker 未运行！" -ForegroundColor Red
        Write-Host ""
        Write-Host "请先启动 Docker Desktop，然后重试。" -ForegroundColor Yellow
        Write-Host ""
        Read-Host "按回车键返回"
        return
    }
    Write-Host "✅ Docker 正在运行" -ForegroundColor Green

    # 创建.env文件
    Write-Host "[3/5] 配置环境变量..." -ForegroundColor Yellow
    if (Test-Path ".env") {
        Write-Host "⚠️  .env 文件已存在，跳过创建" -ForegroundColor Yellow
    }
    else {
        Write-Host "创建 .env 文件..." -ForegroundColor Gray
        New-EnvFile
        Write-Host "✅ .env 文件创建成功" -ForegroundColor Green
    }

    # 设置权限
    Write-Host "[4/5] 设置脚本权限..." -ForegroundColor Yellow
    if (Test-Path "C:\Program Files\Git\bin\bash.exe") {
        & "C:\Program Files\Git\bin\bash.exe" -c "chmod +x entrypoint.sh" 2>$null
        Write-Host "✅ 脚本权限设置完成" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️  未找到 Git Bash，跳过权限设置" -ForegroundColor Yellow
    }

    # 构建并启动
    Write-Host "[5/5] 构建并启动服务..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "⏳ 首次启动需要下载镜像，可能需要 3-5 分钟..." -ForegroundColor Cyan
    Write-Host ""
    
    docker-compose up -d --build
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "║                    🎉 部署成功！                           ║" -ForegroundColor Green
        Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green
        Write-Host ""
        Write-Host "📍 访问地址: http://localhost:5000" -ForegroundColor Cyan
        Write-Host "👤 测试账号: admin / admin123" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "⏳ 等待服务完全启动（约30秒）..." -ForegroundColor Gray
        Start-Sleep -Seconds 5
        Write-Host ""
        
        $openNow = Read-Host "是否现在打开浏览器？ (Y/N)"
        if ($openNow -eq "Y" -or $openNow -eq "y") {
            Start-Process "http://localhost:5000"
        }
    }
    else {
        Write-Host ""
        Write-Host "❌ 启动失败！请查看上方错误信息。" -ForegroundColor Red
    }
    
    Write-Host ""
    Read-Host "按回车键继续"
}

function Start-Project {
    Clear-Host
    Write-Host "启动项目..." -ForegroundColor Yellow
    docker-compose up -d
    Write-Host ""
    Write-Host "✅ 项目已启动！" -ForegroundColor Green
    Write-Host "📍 访问地址: http://localhost:5000" -ForegroundColor Cyan
    Write-Host ""
    Read-Host "按回车键继续"
}

function Stop-Project {
    Clear-Host
    Write-Host "停止项目..." -ForegroundColor Yellow
    docker-compose down
    Write-Host ""
    Write-Host "✅ 项目已停止！" -ForegroundColor Green
    Write-Host ""
    Read-Host "按回车键继续"
}

function Restart-Project {
    Clear-Host
    Write-Host "重启项目..." -ForegroundColor Yellow
    docker-compose restart
    Write-Host ""
    Write-Host "✅ 项目已重启！" -ForegroundColor Green
    Write-Host ""
    Read-Host "按回车键继续"
}

function Show-Status {
    Clear-Host
    Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "                      运行状态" -ForegroundColor Cyan
    Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    docker-compose ps
    Write-Host ""
    Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Read-Host "按回车键继续"
}

function Show-Logs {
    Clear-Host
    Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "                  实时日志（按 Ctrl+C 退出）" -ForegroundColor Cyan
    Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    docker-compose logs -f
}

function Open-Browser {
    Start-Process "http://localhost:5000"
    Write-Host "✅ 已打开浏览器" -ForegroundColor Green
    Start-Sleep -Seconds 2
}

function Remove-AllData {
    Clear-Host
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Red
    Write-Host "║                  ⚠️  危险操作警告                         ║" -ForegroundColor Red
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Red
    Write-Host ""
    Write-Host "此操作将：" -ForegroundColor Yellow
    Write-Host " - 停止并删除所有容器" -ForegroundColor Gray
    Write-Host " - 删除数据库数据" -ForegroundColor Gray
    Write-Host " - 删除所有 Docker 卷" -ForegroundColor Gray
    Write-Host ""
    Write-Host "⚠️  所有数据将永久丢失！" -ForegroundColor Red
    Write-Host ""
    
    $confirm = Read-Host "确认删除所有数据？输入 YES 继续"
    if ($confirm -ne "YES") {
        Write-Host "已取消操作" -ForegroundColor Yellow
        Start-Sleep -Seconds 2
        return
    }

    Write-Host ""
    Write-Host "正在清理..." -ForegroundColor Yellow
    docker-compose down -v
    Write-Host ""
    Write-Host "✅ 清理完成！" -ForegroundColor Green
    Write-Host ""
    Read-Host "按回车键继续"
}

function Show-AdvancedMenu {
    while ($true) {
        Clear-Host
        Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
        Write-Host "║                      高级选项                              ║" -ForegroundColor Cyan
        Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
        Write-Host ""
        Write-Host " [1] 查看 Web 应用日志" -ForegroundColor Gray
        Write-Host " [2] 查看 MySQL 日志" -ForegroundColor Gray
        Write-Host " [3] 进入 Web 容器" -ForegroundColor Gray
        Write-Host " [4] 进入 MySQL 容器" -ForegroundColor Gray
        Write-Host " [5] 重新构建镜像" -ForegroundColor Gray
        Write-Host " [6] 查看资源占用" -ForegroundColor Gray
        Write-Host " [7] 备份数据库" -ForegroundColor Gray
        Write-Host " [0] 返回主菜单" -ForegroundColor White
        Write-Host ""
        
        $choice = Read-Host "请选择操作 [0-7]"
        
        switch ($choice) {
            "1" {
                docker-compose logs web
                Read-Host "按回车键继续"
            }
            "2" {
                docker-compose logs mysql
                Read-Host "按回车键继续"
            }
            "3" {
                Write-Host "进入 Web 容器（输入 exit 退出）..." -ForegroundColor Yellow
                docker-compose exec web bash
            }
            "4" {
                Write-Host "进入 MySQL 容器（输入 exit 退出）..." -ForegroundColor Yellow
                docker-compose exec mysql bash
            }
            "5" {
                Write-Host "重新构建镜像..." -ForegroundColor Yellow
                docker-compose build --no-cache
                Write-Host "✅ 构建完成！" -ForegroundColor Green
                Read-Host "按回车键继续"
            }
            "6" {
                docker stats --no-stream
                Read-Host "按回车键继续"
            }
            "7" {
                $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
                $backupFile = "backup_$timestamp.sql"
                Write-Host "正在备份数据库到 $backupFile..." -ForegroundColor Yellow
                docker-compose exec -T mysql mysqldump -u root -proot123456 meituan_waimai | Out-File -FilePath $backupFile -Encoding UTF8
                Write-Host "✅ 备份完成: $backupFile" -ForegroundColor Green
                Read-Host "按回车键继续"
            }
            "0" {
                return
            }
        }
    }
}

# 主循环
while ($true) {
    Show-Menu
    $choice = Read-Host "请选择操作 [0-9]"
    
    switch ($choice) {
        "1" { Start-FirstDeploy }
        "2" { Start-Project }
        "3" { Stop-Project }
        "4" { Restart-Project }
        "5" { Show-Status }
        "6" { Show-Logs }
        "7" { Open-Browser }
        "8" { Remove-AllData }
        "9" { Show-AdvancedMenu }
        "0" {
            Clear-Host
            Write-Host ""
            Write-Host "感谢使用！再见 👋" -ForegroundColor Cyan
            Write-Host ""
            Start-Sleep -Seconds 2
            exit
        }
    }
}

