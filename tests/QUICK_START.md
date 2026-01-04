# 并发测试快速参考

## 🚀 一分钟快速开始

### 步骤1：启动应用
```bash
快速启动.bat
```

### 步骤2：运行测试
```bash
运行并发测试.bat
```

### 步骤3：选择测试级别
```
请选择测试方式：
  1. 基础并发测试（自定义并发数）        ← 推荐新手
  2. 多级别对比测试（推荐）              ← 推荐使用这个！
  3. Locust压力测试（专业测试）
  4. 快速并发安全性测试
```

## 📊 三种测试模式对比

| 模式 | 并发数 | 时长 | 适用场景 | 难度 |
|------|--------|------|----------|------|
| **基础测试** | 自定义(50-1000) | 5-15分钟 | 单次性能测试 | ⭐ |
| **多级别测试** | 100/500/1000 | 15-30分钟 | 性能对比分析 | ⭐⭐ |
| **Locust测试** | 动态调整 | 自定义 | 专业压力测试 | ⭐⭐⭐ |

## 💡 推荐测试流程

### 第一次测试（建议）
```bash
# 使用多级别测试，一次性看到完整性能曲线
运行并发测试.bat
选择：2（多级别对比测试）
```

### 针对性测试
```bash
# 测试特定并发数
python tests/concurrent_test.py --users 100
python tests/concurrent_test.py --users 500
python tests/concurrent_test.py --users 1000
```

### 专业压力测试
```bash
# 启动Locust
locust -f tests/locust_test.py --host=http://localhost:5000

# 浏览器访问 http://localhost:8089
# 设置：
#   - Number of users: 500
#   - Spawn rate: 20
#   - 点击 Start swarming
```

## 📈 结果解读

### 多级别测试报告示例

```
┌──────────────────────────────────────────────────┐
│ 并发用户数 │ 总请求数 │ 成功率  │ 平均响应时间 │
├────────────┼──────────┼─────────┼──────────────┤
│     100    │   400    │ 99.75%  │   0.287s     │ ← 性能优秀
│     500    │  2000    │ 98.50%  │   0.523s     │ ← 性能良好
│    1000    │  4000    │ 96.25%  │   1.156s     │ ← 出现瓶颈
└────────────┴──────────┴─────────┴──────────────┘
```

### 性能评估标准

| 指标 | 优秀 | 良好 | 一般 | 较差 |
|------|------|------|------|------|
| **平均响应时间** | <0.5s | <1.0s | <2.0s | >2.0s |
| **成功率** | >99.5% | >99% | >95% | <95% |
| **95%响应时间** | <1.0s | <2.0s | <3.0s | >3.0s |

### 如何判断系统性能？

- ✅ **优秀**：1000并发下，平均响应<1s，成功率>99%
- ⚠️ **良好**：500并发下，平均响应<1s，成功率>99%
- ⚠️ **一般**：100并发下，平均响应<1s，成功率>99%
- ❌ **需要优化**：100并发下，响应>1s或成功率<95%

## 🔍 常见问题速查

### Q1: 测试时出现大量失败怎么办？
```bash
# 1. 检查服务是否正常运行
curl http://localhost:5000

# 2. 查看Docker日志
docker-compose logs web

# 3. 降低并发数重新测试
python tests/concurrent_test.py --users 10
```

### Q2: 想测试自定义并发数？
```bash
# 任意并发数（例如250）
python tests/concurrent_test.py --users 250
```

### Q3: 如何只测试某个功能？
```bash
# 只测试并发安全性
python -c "from tests.concurrent_test import test_concurrent_registration; test_concurrent_registration()"
```

### Q4: 测试完成后如何清理数据？
```bash
# 清理测试用户
docker-compose exec db mysql -u root -p123456 -e "
DELETE FROM user WHERE username LIKE 'testuser_%' OR username LIKE 'locust_%';
"
```

## 📁 测试报告文件说明

| 文件名 | 说明 |
|--------|------|
| `concurrent_test_report_100users.json` | 100并发测试详细报告 |
| `concurrent_test_report_500users.json` | 500并发测试详细报告 |
| `concurrent_test_report_1000users.json` | 1000并发测试详细报告 |
| `multi_level_test_report_*.json` | 多级别对比测试报告 |

## 🎯 测试建议时间表

| 开发阶段 | 推荐测试 | 频率 |
|----------|---------|------|
| **功能开发中** | 50并发基础测试 | 每次大改后 |
| **功能完成** | 100并发测试 | 提交前 |
| **测试阶段** | 多级别对比测试 | 每周一次 |
| **上线前** | Locust专业测试 | 上线前必测 |

## 💻 命令速查表

```bash
# === 基础测试 ===
python tests/concurrent_test.py                          # 默认50并发
python tests/concurrent_test.py --users 100              # 100并发
python tests/concurrent_test.py --users 500              # 500并发
python tests/concurrent_test.py --users 1000             # 1000并发

# === 多级别测试 ===
python tests/multi_level_test.py                         # 默认100/500/1000
python tests/multi_level_test.py --levels 50 100 500     # 自定义级别

# === Locust测试 ===
locust -f tests/locust_test.py --host=http://localhost:5000

# === 无头模式运行Locust（命令行直接运行） ===
locust -f tests/locust_test.py \
  --host=http://localhost:5000 \
  --users 500 \
  --spawn-rate 20 \
  --run-time 5m \
  --headless

# === 服务器检查 ===
curl http://localhost:5000                               # 检查服务
docker-compose ps                                        # 查看容器状态
docker-compose logs web                                  # 查看应用日志
```

## 🎓 进阶技巧

### 1. 导出CSV格式报告（Locust）
```bash
locust -f tests/locust_test.py \
  --host=http://localhost:5000 \
  --users 500 \
  --spawn-rate 20 \
  --run-time 5m \
  --headless \
  --csv=results
```

### 2. 多服务器分布式测试
```bash
# Master节点
locust -f tests/locust_test.py --master --host=http://localhost:5000

# Worker节点（在其他机器上）
locust -f tests/locust_test.py --worker --master-host=192.168.1.100
```

### 3. 自定义测试脚本
```python
# custom_test.py
from tests.concurrent_test import ConcurrentTester

tester = ConcurrentTester('http://localhost:5000')
tester.run_concurrent_test(200)  # 200并发
tester.print_statistics()
```

## 📞 需要帮助？

- 📖 详细文档：`tests/README_CONCURRENT_TEST.md`
- 🐛 测试报告：`docs/测试报告.md`
- 🏗️ 架构说明：`docs/架构师报告.md`

