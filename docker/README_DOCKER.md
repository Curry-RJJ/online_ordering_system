# Docker 部署指南

## 🎯 告别 PHPStudy，一键启动项目！

使用 Docker 部署后，您再也不需要：
- ❌ 每次手动打开 PHPStudy
- ❌ 担心 MySQL 服务是否启动
- ❌ 配置复杂的开发环境

只需要一条命令，数据库和应用全部启动！

---

## 📋 前置要求

1. **安装 Docker Desktop**
   - 下载地址：https://www.docker.com/products/docker-desktop/
   - Windows 用户下载后直接安装即可

2. **确保 Docker 正在运行**
   - 打开 Docker Desktop
   - 等待左下角显示 "Docker Desktop is running"

---

## 🚀 快速开始

### 1. 创建环境变量文件

在项目根目录创建 `.env` 文件（复制以下内容）：

```env
# Flask配置
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-change-this-in-production

# MySQL数据库配置
MYSQL_ROOT_PASSWORD=root123456
MYSQL_DATABASE=meituan_waimai
MYSQL_USER=meituan_user
MYSQL_PASSWORD=meituan_pass
MYSQL_PORT=3307

# Web服务端口
WEB_PORT=5000
```

### 2. 启动项目（首次启动需要等待3-5分钟）

```bash
# 构建并启动所有服务（包括MySQL）
docker-compose up -d

# 查看启动日志
docker-compose logs -f
```

### 3. 访问应用

打开浏览器访问：http://localhost:5000

**默认测试账号**：
- 管理员账号：admin / admin123
- 普通用户：user / user123

### 4. 停止项目

```bash
# 停止所有服务（数据会保留）
docker-compose down

# 停止并删除所有数据（慎用！）
docker-compose down -v
```

---

## 📝 常用命令

### 查看运行状态
```bash
docker-compose ps
```

### 查看日志
```bash
# 查看所有服务日志
docker-compose logs

# 查看 Web 应用日志
docker-compose logs web

# 查看 MySQL 日志
docker-compose logs mysql

# 实时跟踪日志
docker-compose logs -f web
```

### 重启服务
```bash
# 重启所有服务
docker-compose restart

# 只重启 Web 应用
docker-compose restart web
```

### 进入容器内部
```bash
# 进入 Web 应用容器
docker-compose exec web bash

# 进入 MySQL 容器
docker-compose exec mysql bash

# 连接 MySQL 数据库
docker-compose exec mysql mysql -u meituan_user -pmeituan_pass meituan_waimai
```

### 查看数据库
```bash
# 方法1: 使用命令行
docker-compose exec mysql mysql -u meituan_user -pmeituan_pass meituan_waimai -e "SHOW TABLES;"

# 方法2: 使用 Navicat 等工具连接
# 主机: localhost
# 端口: 3307
# 用户名: meituan_user
# 密码: meituan_pass
# 数据库: meituan_waimai
```

### 重新构建镜像
```bash
# 当修改了 Dockerfile 或依赖后
docker-compose build

# 重新构建并启动
docker-compose up -d --build
```

---

## 🔧 开发模式

如果需要在开发模式下运行（自动重载代码）：

1. 修改 `.env` 文件：
```env
FLASK_ENV=development
```

2. 修改 `docker-compose.yml`，在 web 服务中添加代码挂载：
```yaml
volumes:
  - .:/app  # 挂载整个项目目录
```

3. 重启服务：
```bash
docker-compose down
docker-compose up -d
```

---

## 📂 数据持久化

以下数据会自动保存，即使重启 Docker 也不会丢失：

- ✅ MySQL 数据库数据（存储在 Docker Volume）
- ✅ 上传的图片文件（映射到 `./app/static/images`）
- ✅ 日志文件（映射到 `./logs`）

---

## 🐛 常见问题

### 1. 端口被占用
**错误**：`Error: bind: address already in use`

**解决方案**：
- 修改 `.env` 文件中的端口号：
```env
MYSQL_PORT=3308  # 改成其他端口
WEB_PORT=5001    # 改成其他端口
```

### 2. 无法连接数据库
**错误**：`Can't connect to MySQL server`

**解决方案**：
```bash
# 查看 MySQL 是否启动成功
docker-compose ps

# 查看 MySQL 日志
docker-compose logs mysql

# 重启 MySQL 服务
docker-compose restart mysql
```

### 3. 图片无法显示
**原因**：图片文件路径映射问题

**解决方案**：
- 确保 `./app/static/images` 目录存在
- 检查 docker-compose.yml 中的 volumes 映射是否正确

### 4. 修改代码后不生效
**原因**：生产模式不会自动重载

**解决方案**：
```bash
# 方法1: 重启服务
docker-compose restart web

# 方法2: 切换到开发模式（见上方"开发模式"部分）
```

### 5. 数据库初始化失败
**解决方案**：
```bash
# 进入 Web 容器手动初始化
docker-compose exec web bash
python init_mysql_data.py
```

---

## 🎨 性能优化建议

### 使用 Nginx 反向代理（生产环境推荐）

在 `docker-compose.yml` 中添加 Nginx 服务：

```yaml
  nginx:
    image: nginx:alpine
    container_name: online_ordering_nginx
    restart: always
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./app/static:/usr/share/nginx/html/static:ro
    depends_on:
      - web
    networks:
      - app_network
```

---

## 📊 监控和日志

### 查看应用性能
```bash
# 查看容器资源占用
docker stats

# 查看 Web 容器详细信息
docker-compose exec web top
```

### 日志管理
应用日志会保存在 `./logs` 目录：
- `access.log` - 访问日志
- `error.log` - 错误日志

---

## 🔐 生产环境部署

### 安全建议

1. **修改默认密码**：
```env
SECRET_KEY=使用随机生成的长字符串
MYSQL_ROOT_PASSWORD=强密码
MYSQL_PASSWORD=强密码
```

2. **使用环境变量**：
   - 不要将 `.env` 文件提交到 Git
   - 在服务器上单独配置

3. **启用 HTTPS**：
   - 使用 Nginx + Let's Encrypt 证书
   - 配置防火墙规则

4. **定期备份**：
```bash
# 备份数据库
docker-compose exec mysql mysqldump -u root -proot123456 meituan_waimai > backup.sql

# 备份上传的图片
tar -czf images_backup.tar.gz app/static/images/
```

---

## 🆚 Docker vs PHPStudy 对比

| 特性 | PHPStudy | Docker |
|------|----------|--------|
| 启动方式 | 手动打开软件 | 一条命令 |
| 环境隔离 | ❌ | ✅ |
| 端口冲突 | 易发生 | 可配置 |
| 数据备份 | 复杂 | 简单 |
| 部署一致性 | 依赖环境 | 完全一致 |
| 跨平台 | Windows only | 全平台 |
| 学习曲线 | 简单 | 中等 |

---

## 📞 技术支持

如遇到问题，请：
1. 查看容器日志：`docker-compose logs`
2. 检查容器状态：`docker-compose ps`
3. 查看本文档的"常见问题"部分

---

## 🎉 完成！

现在您可以：
- ✅ 一条命令启动项目：`docker-compose up -d`
- ✅ 一条命令停止项目：`docker-compose down`
- ✅ 不再需要 PHPStudy
- ✅ 随时随地部署到任何服务器

享受 Docker 带来的便利吧！ 🚀

