# 在线订餐系统

> 美团外卖风格的全栈在线订餐平台，基于 Flask 构建，实现了完整的前后端分离 RESTful API 层、JWT 无状态认证、Redis 缓存与购物车、Celery 异步任务队列、接口限流等生产级后端特性，全程 Docker 容器化部署。

[![Tests](https://img.shields.io/badge/tests-68%20passed-brightgreen)](./tests)
[![Coverage](https://img.shields.io/badge/coverage-39%25-yellow)](./htmlcov)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://python.org)
[![Docker](https://img.shields.io/badge/docker-compose-2496ED)](./docker-compose.yml)

---

## 目录

- [技术亮点](#技术亮点)
- [系统架构](#系统架构)
- [技术栈](#技术栈)
- [性能数据](#性能数据)
- [API 文档](#api-文档)
- [快速启动](#快速启动)
- [运行测试](#运行测试)
- [项目结构](#项目结构)
- [环境变量](#环境变量)

---

## 技术亮点

### 1. RESTful API + JWT 双层认证

在不破坏原有 Jinja2 服务端渲染的前提下，新增一套 `/api/v1/` 前缀的标准 RESTful 接口层，实现**前后端分离架构**并行共存：

- **Access Token**：1 小时有效期，用于普通请求鉴权
- **Refresh Token**：30 天有效期，静默刷新不打断用户体验
- 统一 JSON 响应格式：`{"code": 200, "message": "...", "data": {...}}`
- 自定义 JWT 错误处理，所有 401/403 均返回一致结构

### 2. Redis 多场景应用

Redis 在本项目承担三个独立职责，形成完整技术闭环：

| 职责 | 实现方式 | 说明 |
|------|----------|------|
| **购物车存储** | Redis Hash + 7 天滑动过期 | 替代 Session，支持横向扩展 |
| **接口缓存** | Flask-Caching + 版本号失效法 | 餐厅列表 5 min、菜单 10 min |
| **限流计数器** | flask-limiter + Redis 后端 | 多实例共享，重启不丢失 |

### 3. Celery 异步任务队列

将耗时操作从请求链路中解耦，**主流程不阻塞**：

| 任务 | 触发时机 | 容错机制 |
|------|----------|----------|
| `notify_new_order` | 用户下单成功 | 最多重试 3 次，间隔 60s |
| `notify_order_status_change` | 订单状态变更 | 最多重试 3 次，间隔 60s |
| `cleanup_expired_orders` | Celery Beat 每小时整点 | 自动取消 30 min 未处理订单 |

Celery 不可用时自动跳过（`try/except` + `_CELERY_ENABLED` 标志），保证主流程零影响。

### 4. 输入校验层（marshmallow）

所有 API 入口通过 Schema 校验，非法请求在业务逻辑前被拦截：

- 手机号格式正则校验
- 价格 / 数量范围校验
- 字段必填性与类型校验
- 统一 `422 Unprocessable Entity` 错误格式

### 5. 数据库性能优化

- **12 个索引**覆盖高频查询字段（`restaurant_id`, `status`, `user_id`, `created_at` 等）
- **2 个复合索引**：`(restaurant_id, available)`、`(status, created_at)` 针对多条件过滤优化
- 使用 `joinedload` 彻底消除评价列表的 N+1 查询问题
- 生产环境数据库连接池：`pool_size=20, max_overflow=10, pool_recycle=3600`

### 6. 接口限流（flask-limiter）

防暴力破解与恶意刷接口：

| 接口 | 限制规则 | 防护目的 |
|------|----------|----------|
| `POST /api/v1/auth/login` | 10 次/分钟 | 防密码暴力破解 |
| `POST /api/v1/auth/register` | 5 次/分钟 | 防批量注册刷号 |
| `POST /api/v1/orders` | 10 次/分钟 | 防重复刷单 |
| `POST /api/v1/cart/items` | 60 次/分钟 | 正常操作宽松限制 |
| 全局兜底 | 200 次/分钟 | 所有接口保底保护 |

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Client                               │
│              Browser / Mobile / API Client                  │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP
┌──────────────────────▼──────────────────────────────────────┐
│                   Flask Application                         │
│  ┌──────────────────────┐  ┌──────────────────────────────┐ │
│  │  Jinja2 Routes       │  │  RESTful API (/api/v1/)      │ │
│  │  (Server Rendering)  │  │  JWT Auth + marshmallow      │ │
│  └──────────────────────┘  │  flask-limiter 限流          │ │
│                            └──────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Service Layer                           │   │
│  │  cart_service  │  Flask-Caching  │  SQLAlchemy ORM  │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────┬────────────────────────┬───────────────────────┘
             │                        │
┌────────────▼──────┐    ┌────────────▼──────────────────────┐
│      MySQL 8.0    │    │           Redis 7.2               │
│  - 业务数据存储   │    │  - 购物车 Hash（7天TTL）          │
│  - 12个查询索引   │    │  - 接口缓存（5~10 min TTL）      │
│  - 连接池复用     │    │  - 限流计数器                     │
└───────────────────┘    │  - Celery Broker / Backend       │
                         └───────────────────────────────────┘
                                        │
                         ┌──────────────▼──────────────────┐
                         │    Celery Worker + Beat         │
                         │  - 异步订单通知（3次重试）      │
                         │  - 定时清理过期订单（每小时）   │
                         └─────────────────────────────────┘
```

---

## 技术栈

| 分类 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **Web 框架** | Flask | 2.3.x | 核心框架 |
| **ORM** | Flask-SQLAlchemy | 3.x | 数据库操作 |
| **认证** | Flask-JWT-Extended | 4.6.0 | JWT 无状态认证 |
| **缓存** | Flask-Caching | 2.1.0 | 接口缓存 |
| **限流** | flask-limiter | 3.5.0 | API 限流 |
| **校验** | marshmallow | 3.20.x | 请求参数校验 |
| **消息队列** | Celery | 5.3.4 | 异步任务 |
| **缓存/队列** | Redis | 7.2 | 多场景存储 |
| **数据库** | MySQL | 8.0 | 生产数据库 |
| **服务器** | Gunicorn | - | WSGI 服务 |
| **容器化** | Docker + Compose | - | 环境编排 |
| **测试** | pytest + pytest-cov | 7.4.3 | 单元/集成测试 |
| **测试辅助** | fakeredis | 2.20.0 | Redis Mock |

---

## 性能数据

### 测试覆盖

```
测试套件：68 个测试用例，全部通过（0 failed）
运行时间：~44 秒（Docker 环境）

覆盖模块：
  app/api/auth.py          78%   ← 认证 API
  app/api/cart.py          84%   ← 购物车 API
  app/api/orders.py        74%   ← 订单 API
  app/api/schemas.py       95%   ← 输入校验
  app/services/cart_service.py  72%   ← 购物车服务
  app/models.py            99%   ← 数据模型
```

### 缓存效果

| 场景 | 无缓存（MySQL直查） | 有缓存（Redis命中） | 提升 |
|------|-------------------|-------------------|------|
| 餐厅列表（50条） | ~80ms | ~3ms | **~27x** |
| 餐厅菜单详情 | ~60ms | ~2ms | **~30x** |

> 数据基于本地 Docker 环境单次请求测量，仅作参考。

### 数据库索引

| 索引 | 类型 | 优化场景 |
|------|------|----------|
| `idx_dish_restaurant_id` | 单列 | 餐厅菜单查询 |
| `idx_dish_restaurant_available` | 复合 | 餐厅上架菜品过滤 |
| `idx_order_user_id` | 单列 | 用户订单历史 |
| `idx_order_status_created` | 复合 | Celery 定时清理过期订单 |
| `idx_review_restaurant_id` | 单列 | 餐厅评价列表 |
| *(共 12 个)* | - | 覆盖所有高频查询路径 |

---

## API 文档

基础地址：`http://localhost:5000/api/v1`

### 认证接口

| 方法 | 路径 | 说明 | 限流 |
|------|------|------|------|
| POST | `/auth/login` | 用户登录，返回 Access + Refresh Token | 10次/min |
| POST | `/auth/register` | 用户注册 | 5次/min |
| GET | `/auth/me` | 获取当前用户信息（需 JWT） | - |
| POST | `/auth/refresh` | 刷新 Access Token（需 Refresh Token） | - |

### 餐厅 & 菜品

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/restaurants` | 餐厅列表（Redis 缓存 5min） |
| GET | `/restaurants/<id>` | 餐厅详情（Redis 缓存 10min） |
| GET | `/restaurants/<id>/menu` | 餐厅菜单（Redis 缓存 10min） |

### 购物车

| 方法 | 路径 | 说明 | 限流 |
|------|------|------|------|
| GET | `/cart` | 查看购物车（按餐厅分组） | - |
| POST | `/cart/items` | 添加商品 | 60次/min |
| PUT | `/cart/items/<dish_id>` | 修改数量 | - |
| DELETE | `/cart/items/<dish_id>` | 移除商品 | - |
| DELETE | `/cart` | 清空购物车 | - |

### 订单

| 方法 | 路径 | 说明 | 限流 |
|------|------|------|------|
| POST | `/orders` | 提交订单（触发 Celery 异步通知） | 10次/min |
| GET | `/orders` | 订单列表（仅自己的订单） | - |
| GET | `/orders/<id>` | 订单详情 | - |
| POST | `/orders/<id>/cancel` | 取消订单（仅 pending 状态可取消） | - |

### 统一响应格式

```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

**错误码一览：**

| code | HTTP 状态 | 含义 |
|------|-----------|------|
| 200 | 200 | 成功 |
| 201 | 201 | 创建成功 |
| 400 | 400 | 业务逻辑错误（如状态不允许） |
| 401 | 401 | 未认证 / Token 过期 |
| 403 | 403 | 无权限 |
| 404 | 404 | 资源不存在 |
| 422 | 422 | 请求参数校验失败 |
| 429 | 429 | 请求过于频繁 |

---

## 快速启动

### Docker（推荐）

```bash
git clone https://github.com/Curry-RJJ/online_ordering_system.git
cd online_ordering_system

# 一键启动（Flask + MySQL + Redis + Celery Worker + Celery Beat）
docker-compose up -d
```

访问 http://localhost:5000

| 账号 | 密码 | 角色 |
|------|------|------|
| admin | admin123 | 管理员 |
| testuser | 123456 | 普通用户 |

### 服务说明

```yaml
web          # Flask 应用（Gunicorn，5 workers）
mysql        # MySQL 8.0（持久化存储）
redis        # Redis 7.2（缓存 + 队列，256MB LRU）
celery_worker # Celery 任务消费者
celery_beat  # Celery 定时任务调度器
```

---

## 运行测试

```bash
# 在 Docker 中运行（隔离环境，不影响生产数据）
docker-compose -f docker-compose.test.yml run --rm test

# 测试策略
# - SQLite 临时文件数据库（每个测试函数独立）
# - fakeredis 模拟 Redis（无需真实连接）
# - RATELIMIT_ENABLED=False 禁用限流干扰
# - _CELERY_ENABLED=False 禁用 Celery 任务
```

预期输出：

```
68 passed in ~44s
```

---

## 项目结构

```
online_ordering_system/
├── app/
│   ├── __init__.py          # 应用工厂：db/jwt/cache/limiter 初始化
│   ├── models.py            # SQLAlchemy 模型（12个查询索引）
│   ├── api/                 # RESTful API 层（/api/v1/）
│   │   ├── auth.py          # JWT 认证接口
│   │   ├── cart.py          # 购物车接口
│   │   ├── orders.py        # 订单接口
│   │   ├── restaurants.py   # 餐厅/菜单接口
│   │   ├── schemas.py       # marshmallow 校验 Schema
│   │   └── errors.py        # 统一响应工具函数
│   ├── routes/              # Jinja2 服务端渲染路由
│   ├── services/
│   │   └── cart_service.py  # 购物车业务逻辑（Redis Hash）
│   └── tasks/
│       ├── __init__.py      # Celery 工厂函数
│       └── order_tasks.py   # 订单异步任务
├── tests/
│   ├── conftest.py          # pytest fixtures（fakeredis/SQLite/monkeypatch）
│   ├── test_auth_api.py     # 认证 API 测试
│   ├── test_cart_api.py     # 购物车 API 测试
│   ├── test_order_api.py    # 订单 API 测试
│   └── test_schemas.py      # 输入校验单元测试
├── database/
│   └── add_indexes.sql      # 生产环境索引迁移脚本
├── docker-compose.yml       # 生产环境编排（5个服务）
├── docker-compose.test.yml  # 测试环境编排（隔离）
├── Dockerfile
├── celery_worker.py         # Celery Worker 入口
├── pytest.ini
└── requirements.txt
```

---

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SECRET_KEY` | *(必填，生产)* | Flask Session 密钥 |
| `JWT_SECRET_KEY` | 同 SECRET_KEY | JWT 签名密钥 |
| `DATABASE_URL` | SQLite | 数据库连接串（生产用 MySQL） |
| `REDIS_URL` | `redis://redis:6379/0` | Redis 连接串 |
| `FLASK_ENV` | `production` | 运行环境 |

---

## 许可证

MIT License
