# 🍽️ 在线订餐系统 (Online Ordering System)

一个功能完善的美团风格在线订餐系统，基于 Flask 框架开发，支持 Docker 一键部署。

## ✨ 主要功能

### 👤 用户功能
- **用户注册/登录**：支持用户注册、登录、个人信息管理
- **餐厅浏览**：按分类浏览餐厅，查看餐厅详情和菜品
- **菜品搜索**：搜索和筛选菜品
- **购物车**：添加、修改、删除购物车商品
- **在线下单**：创建订单、查看订单历史
- **订单管理**：查看订单详情、订单状态

### 🔐 管理员功能
- **餐厅管理**：添加、编辑、删除餐厅
- **菜品管理**：管理菜品信息、价格、图片
- **分类管理**：管理餐厅分类和菜品分类
- **订单管理**：查看和处理所有订单
- **用户管理**：管理用户信息和权限

### 🎨 特色功能
- **美团风格 UI**：现代化、响应式界面设计
- **图片上传**：支持餐厅 Logo、菜品图片、横幅图片上传
- **多数据库支持**：支持 SQLite 和 MySQL 数据库
- **Docker 部署**：一键启动完整应用栈

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

1. **克隆项目**
```bash
git clone https://github.com/Curry-RJJ/online_ordering_system.git
cd online_ordering_system
```

2. **启动服务**
```bash
# Windows
docker-compose up -d

# Linux/Mac
docker-compose up -d
```

3. **访问应用**
- 应用地址：http://localhost:5000
- 管理员账号：`admin` / `admin123`
- 测试用户：`testuser` / `123456`

### 方式二：本地开发部署

#### 环境要求
- Python 3.8+
- MySQL 5.7+ (可选，也可使用 SQLite)

#### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/Curry-RJJ/online_ordering_system.git
cd online_ordering_system
```

2. **创建虚拟环境**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **初始化数据库**

**使用 SQLite（推荐开发环境）：**
```bash
python run_meituan.py init
# 选择 1 (SQLite)
```

**使用 MySQL（推荐生产环境）：**
```bash
# 确保 MySQL 服务已启动
python run_meituan.py init
# 选择 2 (MySQL)
```

5. **启动应用**

```bash
# 使用 SQLite
python run_meituan.py

# 使用 MySQL
python run_meituan.py mysql
```

6. **访问应用**
- 访问 http://localhost:5000
- 管理员账号：`admin` / `admin123`
- 测试用户：`testuser` / `123456`

## 📁 项目结构

```
online_ordering_system/
├── app/                        # 应用主目录
│   ├── __init__.py            # 应用初始化
│   ├── models.py              # 数据模型
│   ├── errors.py              # 错误处理
│   ├── utils.py               # 工具函数
│   ├── routes/                # 路由模块
│   │   ├── auth.py           # 用户认证
│   │   ├── restaurant.py     # 餐厅管理
│   │   ├── dish.py           # 菜品管理
│   │   ├── order.py          # 订单管理
│   │   ├── cart.py           # 购物车
│   │   └── category.py       # 分类管理
│   ├── templates/             # HTML 模板
│   └── static/                # 静态资源
│       ├── css/              # 样式文件
│       ├── js/               # JavaScript
│       └── images/           # 图片资源
├── docs/                      # 文档目录
├── migrations/                # 数据库迁移
├── instance/                  # 实例配置（数据库文件）
├── logs/                      # 日志文件
├── config.py                  # SQLite 配置
├── config_mysql.py           # MySQL 配置
├── run.py                     # 基础启动脚本
├── run_meituan.py            # 完整启动脚本
├── init_data.py              # SQLite 数据初始化
├── init_mysql_data.py        # MySQL 数据初始化
├── docker-compose.yml        # Docker 编排配置
├── Dockerfile                 # Docker 镜像配置
├── requirements.txt          # Python 依赖
└── README.md                  # 项目说明

```

## 🛠️ 技术栈

### 后端
- **Flask** - Web 框架
- **SQLAlchemy** - ORM 数据库操作
- **Flask-Login** - 用户认证
- **PyMySQL** - MySQL 数据库驱动
- **Werkzeug** - 密码加密和文件上传

### 前端
- **HTML5/CSS3** - 页面结构和样式
- **Bootstrap 5** - 响应式布局
- **JavaScript** - 交互逻辑
- **Jinja2** - 模板引擎

### 数据库
- **SQLite** - 开发环境（默认）
- **MySQL 8.0** - 生产环境

### 部署
- **Docker** - 容器化部署
- **Docker Compose** - 多容器编排
- **Gunicorn** - WSGI 服务器

## 📊 数据库设计

主要数据表：
- `user` - 用户表
- `restaurant` - 餐厅表
- `restaurant_category` - 餐厅分类表
- `category` - 菜品分类表
- `dish` - 菜品表
- `order` - 订单表
- `order_item` - 订单项表

## 🔧 配置说明

### 环境变量配置

创建 `.env` 文件（参考 `.env.example`）：

```bash
# Flask 配置
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=your-secret-key

# MySQL 配置
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_USER=meituan_user
MYSQL_PASSWORD=your-password
MYSQL_DATABASE=meituan_waimai
MYSQL_ROOT_PASSWORD=root-password

# Web 服务
WEB_PORT=5000
```

### Docker 配置

修改 `docker-compose.yml` 中的环境变量即可。

## 📖 使用说明

详细使用说明请查看：
- [使用说明](docs/使用说明.md)
- [CRUD 功能说明](docs/CRUD功能说明.md)
- [Docker 部署说明](README_DOCKER.md)
- [图片上传功能说明](docs/图片上传功能说明.md)

## 🐛 常见问题

### 1. 端口被占用
```bash
# 修改 docker-compose.yml 中的端口映射
ports:
  - "8080:5000"  # 改为其他端口
```

### 2. MySQL 连接失败
```bash
# 检查 MySQL 服务状态
docker-compose logs mysql

# 重启 MySQL 服务
docker-compose restart mysql
```

### 3. 图片上传失败
确保 `app/static/images/` 目录有写入权限。

## 📝 开发计划

- [ ] 添加支付功能
- [ ] 实时订单通知
- [ ] 外卖配送追踪
- [ ] 用户评价系统
- [ ] 优惠券功能
- [ ] 数据统计分析

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 👨‍💻 作者

Curry-RJJ

## 🔗 相关链接

- [GitHub 仓库](https://github.com/Curry-RJJ/online_ordering_system)
- [问题反馈](https://github.com/Curry-RJJ/online_ordering_system/issues)

---

⭐ 如果这个项目对你有帮助，请给它一个星标！
