# 高德地图 API 集成方案

**项目：** 在线订餐系统  
**文档日期：** 2026-03-27  
**状态：** 🔄 实施中

---

## 已确认决策

| 项目 | 决策 |
|---|---|
| 地理限制 | 无城市限制，全国可用（餐厅数据初期集中在深圳） |
| 首次登录 | 强制选择位置，不允许跳过 |
| 配送推荐范围 | 10km 以内 |
| 餐厅图片 | 统一占位图（`/static/images/logos/placeholder.png`） |
| 菜品图片 | 统一占位图（`/static/images/dishes/placeholder.png`） |
| 菜单生成 | 两级方案：连锁品牌爬官网 / 其他按分类生成模板菜单 |
| 餐厅数量 | 150 家（坪山区 100 家 + 其他区 50 家） |
| 服务器数据库 | 当前为空，全部由爬取脚本初始化，无需迁移旧数据 |

---

## API Key 申请清单

> 申请地址：[高德开放平台控制台](https://console.amap.com/dev/key/app)

| Key 类型 | 用途说明 | 绑定域名白名单 |
|---|---|---|
| **Web端 JS API Key** | 前端地图展示、浏览器定位、地图选点 | `beautyteam.sztu1881.com`、`localhost` |
| **Web服务 Key** | 后端所有 HTTP 接口（搜索、编码、提示、IP定位、区划） | 不需要（后端调用） |

### Web服务 Key 将使用的接口

| 接口 | 用途 |
|---|---|
| 搜索 API（`/v3/place/text`、`/v3/place/around`） | 爬取 150 家真实餐厅 POI 数据 |
| 地理/逆地理编码 API（`/v3/geocode/geo`、`/v3/geocode/regeo`） | 地址文字 ↔ 经纬度互转 |
| 输入提示 API（`/v3/assistant/inputtips`） | 用户输入地址时实时下拉建议 |
| IP 定位（`/v3/ip`） | 浏览器拒绝 GPS 时兜底定位 |
| 行政区域查询（`/v3/config/district`） | 获取各区边界（备用，为后续区域筛选预留） |

### JS API Key 将使用的能力

| 能力 | 用途 |
|---|---|
| `AMap.Geolocation` | 浏览器 GPS 定位 |
| `AMap.Marker` / `AMap.Map` | 地图展示、拖拽选点 |
| `AMap.AutoComplete` | 地址搜索输入提示 |
| `AMap.PlaceSearch` | 前端地点搜索 |

---

## 实施步骤

---

### 第一步：环境变量配置

**状态：** ✅ 已完成（2026-03-27）

**改动文件：**
- `.env.example`：新增 `AMAP_JS_KEY` 和 `AMAP_WEB_KEY` 两个变量
- `app/__init__.py`：注册 `amap_js_key` 为 Jinja2 全局模板变量（`app.jinja_env.globals`）

**说明：**  
JS Key 通过模板全局变量暴露给前端（高德允许配置域名白名单防滥用）；Web服务 Key 只在后端使用，不暴露给前端。

**完成标志：** `.env.example` 包含两个 Key 变量，`flask shell` 中 `current_app.config['AMAP_WEB_KEY']` 有值。

---

### 第二步：数据库模型变更

**状态：** ✅ 已完成（2026-03-27）

**改动文件：**
- `app/models.py`

**具体变更：**

```
User 模型：
  + location_confirmed  Boolean, default=False  # 是否已完成首次位置设置

Restaurant 模型：
  + latitude   Float, nullable=True   # 纬度
  + longitude  Float, nullable=True   # 经度

Address 模型：
  + latitude   Float, nullable=True   # 纬度
  + longitude  Float, nullable=True   # 经度
```

**说明：**  
坐标字段均允许 NULL，确保存量数据（如有）迁移不报错。爬取脚本写入的新餐厅全部带坐标。

**执行命令：**
```bash
flask db migrate -m "add location fields"
flask db upgrade
```

**完成标志：** `flask db upgrade` 无报错，数据库表结构包含新字段。

---

### 第三步：后端工具函数

**状态：** ✅ 已完成（2026-03-27）

**改动文件：**
- `app/utils.py`：追加以下函数

```python
# Haversine 公式计算两点距离（千米）
def haversine(lat1, lng1, lat2, lng2) -> float

# 调高德 IP 定位接口，返回 (lat, lng, city) 或 None
def amap_ip_locate(ip: str) -> tuple | None

# 调高德逆地理编码，坐标 → 地址文字
def amap_regeocode(lat: float, lng: float) -> str | None
```

**说明：**  
`haversine` 纯 Python 实现，无 API 消耗；后两个函数使用 Web服务 Key，调用高德 REST API。

**完成标志：** `pytest tests/` 中新增单元测试通过。

---

### 第四步：首次登录强制选位置

**状态：** ✅ 已完成（2026-03-27）

**改动文件：**
- `app/routes/location.py`（新建）
- `app/__init__.py`：注册蓝图 + `before_request` 拦截钩子
- `app/templates/location/setup_location.html`（新建）

**路由设计：**

```
GET  /setup-location   → 显示地图选位置页面
POST /setup-location   → 保存坐标 + 地址文字
                          → 创建默认 Address 记录（带坐标）
                          → 写入 session['user_lat/lng/address']
                          → User.location_confirmed = True
                          → 重定向首页
```

**拦截逻辑（`before_request`）：**
```
已登录 AND location_confirmed == False
AND 当前 endpoint 不在白名单（logout/static/setup-location）
→ 302 重定向 /setup-location
```

**页面交互流程：**
```
进入页面
  ├─ [自动定位] AMap.Geolocation → 显示当前坐标 + 逆地理编码地址
  │                               → 用户确认 → POST
  └─ [手动搜索] AMap.AutoComplete 输入框
                → 选中后地图 Pin 移动到目标位置
                → 用户确认 → POST
```

**完成标志：** 新注册用户登录后被强制跳转到选位置页面，选完后能正常进入首页，刷新不再跳转。

---

### 第五步：餐厅创建/编辑绑定位置

**状态：** ✅ 已完成（2026-03-27）

**改动文件：**
- `app/routes/restaurant.py`
- `app/templates/restaurant/add.html`
- `app/templates/restaurant/edit.html`

**后端变更：**
- `add_restaurant()` POST：读取 `latitude`、`longitude`，为空则报错拒绝
- `edit_restaurant()` POST：坐标加入 `change_data`（管理员直改 / 商家走审核）
- `_to_restaurant_dict()`：返回值新增 `latitude`、`longitude` 字段
- `approve_change_request()`：审核通过时同步坐标字段到 `Restaurant`

**前端变更：**
- 表单新增地图选点区域（复用第四步的地图组件 `amap_picker.js`）
- 隐藏字段 `<input name="latitude">` 和 `<input name="longitude">`
- 提交前 JS 校验坐标不为空

**完成标志：** 管理员新建餐厅时不选位置无法提交，成功创建后 `Restaurant.latitude/longitude` 有值。

---

### 第六步：按位置推荐附近餐厅

**状态：** ✅ 已完成（2026-03-27）

**改动文件：**
- `app/routes/restaurant.py`：改造 `list_restaurants()` + 新增 `set_user_location()`
- `app/templates/restaurant/list.html`（或首页模板）

**新增路由：**
```
POST /restaurant/set-location
  → 接收 lat, lng, address
  → 写入 session['user_lat'], session['user_lng'], session['user_address']
  → 返回 JSON {success: true}
```

**改造 `list_restaurants()`：**
```
1. 从 session 读取用户坐标
2. 如果有坐标：
   a. 计算每家餐厅距离（haversine）
   b. 过滤 > 10km 的餐厅
   c. sort_by=distance 时按距离升序（修复 BUG-13）
   d. 每个餐厅 dict 追加 distance 字段（km，保留1位小数）
   e. 此情况下不走缓存（用户位置各异）
3. 如果无坐标：按评分排序（保持原有行为）
```

**前端变更（列表页顶部）：**
```
┌─────────────────────────────────────────────┐
│ 📍 坪山区坑梓街道  [切换位置]               │
└─────────────────────────────────────────────┘
```
- 点击「切换位置」弹出高德地图选点弹窗（复用 `amap_picker.js`）
- 每个餐厅卡片显示距离标签：`1.2km`

**完成标志：** 首页显示当前地址，餐厅列表按距离排序，超出 10km 的不显示，切换位置后列表实时更新。

---

### 第七步：爬取 200 家深圳真实连锁餐厅 + 菜单生成

**状态：** ✅ 已完成（2026-03-28）

**新增文件：**
- `scripts/seed_restaurants_amap.py`（主爬取脚本）
- `scripts/menu_templates.py`（35 个品牌精准菜单数据）
- `scripts/chain_scrapers.py`（百度图片爬取工具）

#### 餐厅分布（200 家，全连锁）

| 区域 | 数量 | 搜索方式 |
|---|---|---|
| 福田区 | 100 | 按品牌名搜索，过滤 adname=福田区 |
| 其他区（全深圳自然分布） | 100 | 按品牌名搜索，过滤掉福田结果 |

#### 35 个连锁品牌

| 品类 | 品牌 |
|---|---|
| 西式快餐 | 肯德基、麦当劳、必胜客、汉堡王、赛百味、华莱士 |
| 咖啡 | 星巴克、瑞幸咖啡、Manner、Tim Hortons |
| 奶茶 | 喜茶、奈雪的茶、茶百道、蜜雪冰城、CoCo都可、书亦烧仙草、益禾堂、古茗 |
| 火锅 | 海底捞、呷哺呷哺、小龙坎、凑凑火锅 |
| 日式 | 吉野家、味千拉面、丸龟制面 |
| 意式 | 萨莉亚 |
| 中式快餐 | 真功夫、老乡鸡、大米先生、乡村基 |
| 麻辣烫 | 杨国福麻辣烫、张亮麻辣烫 |
| 面馆 | 和府捞面、遇见小面、五爷拌面 |
| 西北菜 | 西贝莜面村 |
| 烧烤 | 木屋烧烤 |

#### 菜单方案（全精准内置模板）

所有 35 个品牌均使用内置精准菜单（8-12 道菜），无需爬取官网。

#### 图片方案

| 图片类型 | 来源 |
|---|---|
| 餐厅 Logo | 百度图片爬取，每品牌爬取一次，同品牌所有门店复用 |
| 菜品图片 | 百度图片按菜名爬取，同名菜复用同一张 |

#### 高德字段 → 数据库字段映射

| 高德 POI 字段 | 映射到 Restaurant 字段 |
|---|---|
| `name` | `name` |
| `address` | `address` |
| `location`（`lng,lat`） | `longitude`, `latitude` |
| `tel` | `phone` |
| `type` / `typecode` | `cuisine_type`（转换映射） |
| `business_area` | `description` 中附加说明 |

**完成标志：** 脚本运行完毕，数据库中有 150 家餐厅，每家有 8-12 道菜，所有餐厅/菜品图片均为占位图路径。

---

### 第八步：占位图准备

**状态：** ✅ 已完成（2026-03-27）

**文件路径与规格：**

| 用途 | 路径 | 尺寸 | 格式 | 引用方式 |
|---|---|---|---|---|
| 餐厅 Logo 占位 | `app/static/images/logos/placeholder.png` | 200×200px | PNG | `/static/images/logos/placeholder.png` |
| 菜品图片占位 | `app/static/images/dishes/placeholder.png` | 400×300px | PNG | `/static/images/dishes/placeholder.png` |

**源文件（原始高分辨率，勿删）：**
- `app/static/images/logos/restaurantsplaceolder.png`（2048×2048px，餐厅占位图源文件）
- `app/static/images/logos/foodplaceorder.png`（2364×1773px，菜品占位图源文件）

**完成标志：** 两个文件存在，浏览器访问路径不报 404。

---

## 实施顺序说明

```
【前置条件】
  拿到高德 JS Key + Web服务 Key
         ↓
【第一步】.env 配置（10分钟）
         ↓
【第二步】模型变更 + 数据库迁移（20分钟）
         ↓
【第三步】工具函数（15分钟）
         ↓
【第八步】准备占位图（5分钟）← 早点做，后续脚本依赖
         ↓
【第四步】首次登录选位置（60分钟，含前端页面）
         ↓
【第五步】餐厅创建绑定位置（45分钟）
         ↓
【第六步】按位置推荐（45分钟）
         ↓
【第七步】爬取脚本 + 数据入库（120分钟）
         ↓
【完成】本地验收 → 服务器部署
```

---

## 完成进度追踪

| 步骤 | 状态 | 完成日期 | 备注 |
|---|---|---|---|
| 第一步：环境变量配置 | ✅ 已完成 | 2026-03-27 | .env 填入3个Key，__init__.py注册Jinja2全局变量 |
| 第二步：模型变更 | ✅ 已完成 | 2026-03-27 | User/Restaurant/Address新增坐标字段，迁移已执行 |
| 第三步：工具函数 | ✅ 已完成 | 2026-03-27 | haversine/amap_ip_locate/amap_regeocode 已追加至 utils.py |
| 第四步：首次登录选位置 | ✅ 已完成 | 2026-03-27 | location蓝图+before_request拦截+地图选点页面 |
| 第五步：餐厅位置绑定 | ✅ 已完成 | 2026-03-27 | 新建必填坐标，编辑可更新坐标，地图选点组件复用 |
| 第六步：按位置推荐 | ✅ 已完成 | 2026-03-27 | 10km过滤+距离排序+位置栏+切换位置弹窗 |
| 第七步：爬取脚本 | ✅ 已完成 | 2026-03-28 | 200家连锁+百度图片+精准菜单，服务器Docker容器内执行 |
| 第八步：占位图 | ✅ 已完成 | 2026-03-27 | logos/placeholder.png + dishes/placeholder.png |

---

## 改动文件总览

| 文件 | 类型 | 涉及步骤 |
|---|---|---|
| `.env.example` | 修改 | 第一步 |
| `app/__init__.py` | 修改 | 第一步、第四步 |
| `app/models.py` | 修改 | 第二步 |
| `app/utils.py` | 修改 | 第三步 |
| `app/routes/location.py` | **新建** | 第四步 |
| `app/routes/restaurant.py` | 修改 | 第五步、第六步 |
| `app/templates/location/setup_location.html` | **新建** | 第四步 |
| `app/templates/restaurant/add.html` | 修改 | 第五步 |
| `app/templates/restaurant/edit.html` | 修改 | 第五步 |
| `app/templates/restaurant/list.html` | 修改 | 第六步 |
| `app/static/js/amap_picker.js` | **新建** | 第四步（复用于第五步） |
| `app/static/images/logos/placeholder.png` | **新建** | 第八步 |
| `app/static/images/dishes/placeholder.png` | **新建** | 第八步 |
| `scripts/seed_restaurants_amap.py` | **新建** | 第七步 |
| `scripts/menu_templates.py` | **新建** | 第七步 |
| `scripts/chain_scrapers.py` | **新建** | 第七步 |

---

*文档由开发团队维护，每完成一个步骤立即更新对应状态和完成日期。*
