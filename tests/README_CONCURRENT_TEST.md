# 并发测试说明文档

## 概述

本目录包含三个并发测试脚本，用于测试在线订餐系统在高并发场景下的性能和稳定性。

## 测试脚本说明

### 1. concurrent_test.py - 基础并发测试（支持自定义并发数）

使用Python标准库实现的并发测试脚本，支持命令行参数自定义并发数量。

**特点：**
- ✅ 无需额外安装依赖包
- ✅ 测试完整的用户工作流程
- ✅ 包含并发安全性测试
- ✅ 生成详细的测试报告

**测试场景：**
1. **用户注册** - 测试高并发注册，验证用户名唯一性约束
2. **用户登录** - 测试并发登录性能
3. **浏览餐厅** - 测试餐厅列表页面的并发访问
4. **购物车操作** - 测试购物车的并发添加操作
5. **并发安全性** - 专门测试10个线程同时注册相同用户名

**运行方式：**

```bash
# 1. 确保应用正在运行
cd d:\projects\online_ordering_system

# 2. 运行默认测试（50并发用户）
python tests/concurrent_test.py

# 3. 运行指定并发数测试
python tests/concurrent_test.py --users 100    # 100并发
python tests/concurrent_test.py --users 500    # 500并发
python tests/concurrent_test.py --users 1000   # 1000并发

# 4. 更多选项
python tests/concurrent_test.py --help
```

**命令行参数：**

```
-u, --users NUMBER      并发用户数量（默认: 50）
-H, --host URL          目标服务器地址（默认: http://localhost:5000）
--skip-safety           跳过并发安全性测试
-o, --output FILE       指定输出文件名
```

**输出结果：**

测试完成后会显示：
- 各项操作的统计数据（成功率、响应时间等）
- 错误详情
- 生成 `concurrent_test_report_XXXusers.json` 详细报告

### 2. multi_level_test.py - 多级别对比测试（新增）

自动运行多个并发级别的测试，并生成性能对比报告和趋势分析。

**特点：**
- ✅ 自动运行多个并发级别测试（默认：100、500、1000）
- ✅ 生成详细的性能对比表格
- ✅ 分析性能趋势和瓶颈
- ✅ 支持自定义测试级别

**运行方式：**

```bash
# 运行默认级别测试（100、500、1000）
python tests/multi_level_test.py

# 自定义测试级别
python tests/multi_level_test.py --levels 50 100 500

# 指定服务器地址
python tests/multi_level_test.py --host http://localhost:5000
```

**输出报告示例：**

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         测试结果汇总                                          │
├───────────────┬───────────────┬───────────────┬───────────────┬──────────────┤
│ 并发用户数    │  总请求数     │   成功率      │ 平均响应时间  │   测试用时   │
├───────────────┼───────────────┼───────────────┼───────────────┼──────────────┤
│          100  │          400  │       99.75%  │      0.287s   │    45.23s    │
│          500  │         2000  │       98.50%  │      0.523s   │   125.67s    │
│         1000  │         4000  │       96.25%  │      1.156s   │   268.45s    │
└───────────────┴───────────────┴───────────────┴───────────────┴──────────────┘
```

### 3. locust_test.py - 专业压力测试

使用Locust框架实现的专业压力测试脚本，提供Web界面和更强大的功能。

**特点：**
- ✅ 提供友好的Web UI界面
- ✅ 实时监控测试进度和统计数据
- ✅ 支持动态调整并发数
- ✅ 模拟真实用户行为（等待时间）
- ✅ 生成图表和详细报告

**安装依赖：**

```bash
pip install locust
```

**运行方式：**

```bash
# 启动 Locust（使用普通用户模式）
locust -f tests/locust_test.py --host=http://localhost:5000

# 启动 Locust（使用商家管理员模式）
locust -f tests/locust_test.py --host=http://localhost:5000 --class=MerchantAdminUser
```

**访问Web UI：**

打开浏览器访问: http://localhost:8089

在界面上可以设置：
- Number of users (total): 总用户数（建议：50-500）
- Spawn rate: 每秒启动用户数（建议：5-20）
- Host: 目标服务器地址

**测试场景：**

`OrderingSystemUser` 类 - 普通用户行为：
- 浏览餐厅（权重：10）
- 查看餐厅详情（权重：8）
- 添加购物车（权重：5）
- 搜索餐厅（权重：3）
- 查看购物车（权重：3）
- 更新购物车（权重：2）
- 查看订单（权重：1）
- 查看个人资料（权重：1）

`MerchantAdminUser` 类 - 商家管理员行为：
- 查看商家后台（权重：5）
- 查看修改请求（权重：2）

## 快速开始指南

### 方式一：使用快速启动脚本（最简单）

1. **启动应用**
```bash
快速启动.bat
```

2. **运行并发测试**
```bash
运行并发测试.bat
```

3. **选择测试方式**
- 选项1：基础并发测试（可选择50/100/500/1000并发）
- 选项2：多级别对比测试（自动运行100/500/1000并发）
- 选项3：Locust压力测试（Web UI界面）
- 选项4：并发安全性测试

### 方式二：命令行直接运行

```bash
# 运行100并发测试
python tests/concurrent_test.py --users 100

# 运行500并发测试
python tests/concurrent_test.py --users 500

# 运行1000并发测试
python tests/concurrent_test.py --users 1000

# 运行多级别对比测试
python tests/multi_level_test.py
```

## 测试前准备

### 1. 确保应用正在运行

```bash
# 使用快速启动脚本
快速启动.bat

# 或使用 docker-compose
docker-compose up -d
```

### 2. 验证服务可访问

在浏览器中访问: http://localhost:5000

### 3. 准备测试数据（可选）

如果需要测试商家管理员功能，需要预先创建测试账号：

```sql
-- 登录数据库创建测试账号
INSERT INTO user (username, password, role, restaurant_id) 
VALUES ('merchant_test', '$2b$12$...', 'merchant', 1);
```

## 测试建议

### 性能基准测试

1. **低负载测试** (10-20并发用户)
   - 建立性能基线
   - 验证功能正确性

2. **中等负载测试** (50-100并发用户)
   - 测试正常业务场景
   - 观察响应时间变化

3. **高负载测试** (200-500并发用户)
   - 测试系统承载能力
   - 识别性能瓶颈

4. **压力测试** (>500并发用户)
   - 找出系统极限
   - 观察系统崩溃点

### 关键指标

监控以下指标：

- **响应时间**
  - 平均响应时间 < 200ms（优秀）
  - 平均响应时间 < 500ms（良好）
  - 95%响应时间 < 1000ms（可接受）

- **成功率**
  - 成功率 > 99.5%（优秀）
  - 成功率 > 99%（良好）
  - 成功率 > 95%（可接受）

- **吞吐量（RPS）**
  - 根据业务需求设定目标值

### 测试场景建议

#### 场景1：注册并发安全性测试

```bash
python tests/concurrent_test.py
```

重点关注：
- 是否只有一个相同用户名注册成功
- 是否正确返回"用户名已存在"错误
- 数据库是否出现IntegrityError

#### 场景2：购物车并发测试

使用Locust运行50个并发用户，持续5分钟：

```bash
locust -f tests/locust_test.py --host=http://localhost:5000 \
  --users 50 --spawn-rate 10 --run-time 5m
```

重点关注：
- 购物车数据一致性
- 是否出现重复添加
- 响应时间是否稳定

#### 场景3：商家管理员并发操作

```bash
locust -f tests/locust_test.py --host=http://localhost:5000 \
  --class=MerchantAdminUser --users 10 --spawn-rate 2 --run-time 3m
```

重点关注：
- 权限控制是否正确
- 修改请求是否冲突
- 数据是否一致

## 常见问题

### Q1: 测试时出现大量连接超时

**原因：** 数据库连接池过小或系统资源不足

**解决：**
1. 增加数据库连接池大小（config.py中的`pool_size`和`max_overflow`）
2. 降低并发用户数
3. 增加服务器资源（CPU、内存）

### Q2: 测试结果不稳定

**原因：** 系统缓存、网络波动等因素

**解决：**
1. 多次运行取平均值
2. 清理数据库和缓存后重新测试
3. 使用固定的测试环境

### Q3: Locust Web UI无法访问

**原因：** 端口被占用或防火墙拦截

**解决：**
```bash
# 使用不同端口
locust -f tests/locust_test.py --host=http://localhost:5000 --web-port=8090
```

### Q4: 测试时数据库数据过多

**解决：**
```bash
# 测试后清理数据
docker-compose exec db mysql -u root -p123456 -e "
  DELETE FROM user WHERE username LIKE 'testuser_%' OR username LIKE 'locust_%';
  DELETE FROM cart_item WHERE user_id NOT IN (SELECT id FROM user);
"
```

## 测试报告解读

### concurrent_test.py 报告

```json
{
  "test_time": "2025-01-04 18:30:00",
  "concurrent_users": 50,
  "results": {
    "register": [
      {
        "user_id": 0,
        "username": "testuser_abc123",
        "elapsed": 0.235,
        "status": "success"
      }
    ],
    "login": [...],
    "errors": [...]
  }
}
```

**关键字段：**
- `elapsed`: 操作耗时（秒）
- `status`: 成功/失败状态
- `errors`: 错误详情列表

### Locust 报告

在Web UI的Statistics标签页可以看到：

| Type | Name | Requests | Fails | Median | 95%ile | Avg | Min | Max | RPS |
|------|------|----------|-------|--------|--------|-----|-----|-----|-----|
| GET | 浏览餐厅 | 1000 | 0 | 120 | 250 | 135 | 80 | 500 | 20.5 |

**关键指标解读：**
- **Median**: 中位数响应时间（50%的请求低于此值）
- **95%ile**: 95%分位响应时间（95%的请求低于此值）
- **RPS**: 每秒请求数（Requests Per Second）

## 最佳实践

1. **渐进式增加负载**
   - 从小规模开始，逐步增加并发数
   - 观察系统指标变化

2. **监控系统资源**
   - CPU使用率
   - 内存使用率
   - 数据库连接数
   - 磁盘I/O

3. **记录测试结果**
   - 保存每次测试的详细数据
   - 对比不同版本的性能差异

4. **真实场景模拟**
   - 模拟不同用户行为比例
   - 添加合理的等待时间

## 联系支持

如有问题，请查看：
- 项目文档: `docs/架构师报告.md`
- 测试报告: `docs/测试报告.md`

