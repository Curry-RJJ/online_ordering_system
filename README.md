# 🍽️ 美团风格在线订餐系统

一个模仿美团外卖的现代化在线订餐平台，支持多商家、购物车、订单管理等完整功能。

## ✨ 项目特色

### 🏪 真实商家数据
- **农耕记（三里屯店）** - 精选湘菜，招牌口水鸡、毛血旺等
- **尊宝披萨（国贸店）** - 意式手工披萨，玛格丽特、至尊披萨等
- **海底捞火锅（王府井店）** - 优质火锅体验
- **麦当劳（中关村店）** - 经典快餐
- **星巴克咖啡（三里屯店）** - 精品咖啡

### 🎨 美团风格UI
- 现代化响应式设计
- 美团经典黄色主题
- 移动端友好界面
- 流畅的用户体验

### 🚀 核心功能
- 🏠 **首页** - 餐厅列表、搜索筛选
- 🛒 **购物车** - 添加商品、数量管理
- 📋 **订单管理** - 下单、支付、配送跟踪
- 👤 **用户系统** - 注册登录、个人资料
- 🏪 **商家管理** - 餐厅信息、菜品管理
- 📍 **地址管理** - 收货地址维护

## 🛠️ 技术栈

- **后端**: Flask + SQLAlchemy + Flask-Login
- **前端**: Bootstrap 5 + Font Awesome + jQuery
- **数据库**: SQLite / MySQL（支持PHPStudy）
- **部署**: Python 3.7+

## 📦 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <项目地址>
cd online_ordering_system

# 创建虚拟环境（推荐）
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

### 2. 数据库初始化

```bash
# 初始化数据库（会提示选择SQLite或MySQL）
python run_meituan.py init
```

**选择1 - SQLite（推荐）**：
- 无需额外配置
- 适合开发和演示

**选择2 - MySQL（PHPStudy）**：
- 需要先启动PHPStudy的MySQL服务
- 需要创建数据库：`CREATE DATABASE meituan_waimai CHARACTER SET utf8mb4;`

### 3. 启动应用

```bash
# 使用SQLite启动
python run_meituan.py

# 使用MySQL启动
python run_meituan.py mysql
```

### 4. 访问系统

打开浏览器访问：http://localhost:5000

**默认账号**：
- 管理员：`admin` / `admin123`
- 测试用户：`testuser` / `123456`

## 📱 功能演示

### 🏠 首页 - 餐厅列表
- 搜索餐厅和美食
- 按分类筛选（中餐、西餐、快餐等）
- 按评分、销量、距离排序
- 餐厅卡片显示评分、配送费、起送价

### 🍽️ 餐厅详情
- 餐厅信息展示
- 菜品分类浏览
- 推荐菜品展示
- 添加到购物车

### 🛒 购物车
- 按餐厅分组显示
- 数量调整和删除
- 实时计算金额
- 选择收货地址

### 📋 订单管理
- 订单状态跟踪
- 订单详情查看
- 历史订单记录

### 👤 用户中心
- 个人资料管理
- 收货地址管理
- 订单历史查看

### 🔧 管理后台
- 餐厅管理（增删改查）
- 菜品管理（增删改查）
- 用户管理
- 订单管理

## 🗄️ 数据库配置

### SQLite配置（默认）
```python
# config.py
SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/database.db'
```

### MySQL配置（PHPStudy）
```python
# config_mysql.py
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'root'  # PHPStudy默认密码
MYSQL_DATABASE = 'meituan_waimai'
```

## 📊 数据模型

### 核心实体
- **User** - 用户（顾客、管理员）
- **Restaurant** - 餐厅
- **Category** - 菜品分类
- **Dish** - 菜品
- **Order** - 订单
- **OrderItem** - 订单项
- **CartItem** - 购物车项
- **Address** - 收货地址
- **Review** - 评价

### 关系设计
- 用户 1:N 订单
- 用户 1:N 地址
- 用户 1:N 购物车项
- 餐厅 1:N 菜品
- 餐厅 1:N 订单
- 订单 1:N 订单项
- 分类 1:N 菜品

## 🎯 项目亮点

### 1. 真实业务场景
- 模拟真实的外卖平台业务流程
- 包含完整的用户下单到配送的全流程
- 支持多商家平台模式

### 2. 现代化技术栈
- 使用Flask最新版本和最佳实践
- 响应式设计，支持移动端
- RESTful API设计

### 3. 完善的功能模块
- 用户认证和授权
- 购物车和订单系统
- 地址管理
- 评价系统
- 管理后台

### 4. 优秀的用户体验
- 美团风格的UI设计
- 流畅的交互动画
- 友好的错误提示
- 直观的操作流程

## 🔧 开发指南

### 项目结构
```
online_ordering_system/
├── app/                    # 应用主目录
│   ├── __init__.py        # 应用初始化
│   ├── models.py          # 数据模型
│   ├── routes/            # 路由模块
│   │   ├── auth.py        # 用户认证
│   │   ├── restaurant.py  # 餐厅管理
│   │   ├── cart.py        # 购物车
│   │   ├── order.py       # 订单管理
│   │   └── dish.py        # 菜品管理
│   └── templates/         # 模板文件
│       ├── base.html      # 基础模板
│       ├── restaurant/    # 餐厅模板
│       ├── cart/          # 购物车模板
│       └── order/         # 订单模板
├── static/                # 静态文件
├── instance/              # 实例文件（数据库）
├── config.py              # SQLite配置
├── config_mysql.py        # MySQL配置
├── init_data.py           # SQLite数据初始化
├── init_mysql_data.py     # MySQL数据初始化
├── run_meituan.py         # 启动脚本
└── requirements.txt       # 依赖文件
```

### 添加新功能
1. 在 `app/models.py` 中定义数据模型
2. 在 `app/routes/` 中创建路由文件
3. 在 `app/templates/` 中创建模板
4. 在 `app/__init__.py` 中注册蓝图

### 数据库迁移
```bash
# 如果修改了模型，需要重新初始化数据库
python run_meituan.py init
```

## 🚀 部署指南

### 开发环境
```bash
python run_meituan.py
```

### 生产环境
1. 修改配置文件中的SECRET_KEY
2. 使用生产级数据库（MySQL/PostgreSQL）
3. 使用WSGI服务器（Gunicorn/uWSGI）
4. 配置反向代理（Nginx）

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

MIT License

## 📞 联系方式

如有问题或建议，请提交Issue或联系开发者。

---

**享受美团风格的订餐体验！** 🍽️✨
