-- ============================================================
-- 数据库索引迁移脚本
-- 适用：MySQL 8.0（生产环境手动执行）
-- 说明：IF NOT EXISTS 保证幂等，可重复执行不报错
-- 影响：只添加索引，不修改任何数据，零风险操作
-- ============================================================

-- ── dish 表 ─────────────────────────────────────────────────
-- 菜单页核心查询：WHERE restaurant_id=? AND available=1
CREATE INDEX IF NOT EXISTS idx_dish_restaurant_id  ON dish (restaurant_id);
CREATE INDEX IF NOT EXISTS idx_dish_category_id    ON dish (category_id);
CREATE INDEX IF NOT EXISTS idx_dish_available      ON dish (available);
-- 复合索引：同时命中餐厅+上架状态过滤（比两个单列索引更快）
CREATE INDEX IF NOT EXISTS idx_dish_restaurant_available ON dish (restaurant_id, available);

-- ── order 表 ────────────────────────────────────────────────
-- 用户订单列表：WHERE user_id=? ORDER BY created_at DESC
CREATE INDEX IF NOT EXISTS idx_order_user_id       ON `order` (user_id);
-- 餐厅订单管理：WHERE restaurant_id=?
CREATE INDEX IF NOT EXISTS idx_order_restaurant_id ON `order` (restaurant_id);
-- 订单状态过滤（Celery Beat 清理 pending 订单）
CREATE INDEX IF NOT EXISTS idx_order_status        ON `order` (status);
-- 时间范围过滤（cleanup_expired_orders 按 created_at < cutoff_time）
CREATE INDEX IF NOT EXISTS idx_order_created_at    ON `order` (created_at);
-- 复合索引：Celery 定时任务专用 WHERE status='pending' AND created_at < ?
CREATE INDEX IF NOT EXISTS idx_order_status_created ON `order` (status, created_at);

-- ── order_item 表 ────────────────────────────────────────────
-- 订单详情：WHERE order_id=?（高频，每次查看订单详情都执行）
CREATE INDEX IF NOT EXISTS idx_order_item_order_id ON order_item (order_id);
CREATE INDEX IF NOT EXISTS idx_order_item_dish_id  ON order_item (dish_id);

-- ── review 表 ───────────────────────────────────────────────
-- 餐厅详情页评价列表：WHERE restaurant_id=? ORDER BY created_at DESC
CREATE INDEX IF NOT EXISTS idx_review_restaurant_id ON review (restaurant_id);
CREATE INDEX IF NOT EXISTS idx_review_user_id       ON review (user_id);

-- ── restaurant_change_request 表 ────────────────────────────
-- 审核队列：WHERE status='pending' ORDER BY timestamp DESC
CREATE INDEX IF NOT EXISTS idx_change_request_status       ON restaurant_change_request (status);
CREATE INDEX IF NOT EXISTS idx_change_request_type         ON restaurant_change_request (request_type);
CREATE INDEX IF NOT EXISTS idx_change_request_merchant_id  ON restaurant_change_request (merchant_id);
CREATE INDEX IF NOT EXISTS idx_change_request_restaurant_id ON restaurant_change_request (restaurant_id);

-- ============================================================
-- 执行方式（在正在运行的 MySQL 容器中执行）：
--   docker exec -i online_ordering_mysql mysql \
--     -u meituan_user -pmeituan_pass meituan_waimai \
--     < database/add_indexes.sql
-- ============================================================
