"""
Celery 任务单元测试
覆盖 app/tasks/order_tasks.py
直接调用任务底层函数（绕过 Broker），不需要真实 Redis
"""
import pytest
from datetime import datetime, timedelta
import uuid

from app.models import Order, User, Restaurant
from app import db


def _make_order(app, status='pending', minutes_ago=0):
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        restaurant = Restaurant.query.first()
        created = datetime.utcnow() - timedelta(minutes=minutes_ago)
        order = Order(
            order_no=f'T{uuid.uuid4().hex[:8].upper()}',
            user_id=user.id,
            restaurant_id=restaurant.id,
            delivery_name='收件人',
            delivery_phone='13900139000',
            delivery_address='测试地址',
            subtotal=25.5,
            delivery_fee=5.0,
            total_amount=30.5,
            status=status,
            payment_status='unpaid',
            created_at=created,
        )
        db.session.add(order)
        db.session.commit()
        return order.id


class TestNotifyNewOrder:
    def test_task_runs_without_error(self, app):
        from app.tasks.order_tasks import notify_new_order
        result = notify_new_order.run(
            order_id=1,
            order_no='TEST0001',
            restaurant_name='测试餐厅',
            total_amount=30.5,
        )
        assert result['status'] == 'ok'
        assert result['order_id'] == 1

    def test_task_returns_order_id(self, app):
        from app.tasks.order_tasks import notify_new_order
        result = notify_new_order.run(
            order_id=42,
            order_no='TEST0042',
            restaurant_name='餐厅A',
            total_amount=88.0,
        )
        assert result['order_id'] == 42


class TestNotifyOrderStatusChange:
    def test_task_runs_without_error(self, app):
        from app.tasks.order_tasks import notify_order_status_change
        result = notify_order_status_change.run(
            order_id=1,
            order_no='TEST0001',
            new_status='confirmed',
            user_phone='13900139000',
        )
        assert result['status'] == 'ok'
        assert result['new_status'] == 'confirmed'

    def test_task_all_known_statuses(self, app):
        from app.tasks.order_tasks import notify_order_status_change
        statuses = ['confirmed', 'preparing', 'delivering', 'completed', 'cancelled']
        for s in statuses:
            result = notify_order_status_change.run(
                order_id=1,
                order_no='TEST0001',
                new_status=s,
                user_phone='13900139000',
            )
            assert result['status'] == 'ok'

    def test_task_unknown_status(self, app):
        from app.tasks.order_tasks import notify_order_status_change
        result = notify_order_status_change.run(
            order_id=1,
            order_no='TEST0001',
            new_status='unknown_status',
            user_phone='13900139000',
        )
        assert result['status'] == 'ok'


class TestCleanupExpiredOrders:
    def test_cancels_orders_older_than_30_min(self, app):
        oid = _make_order(app, status='pending', minutes_ago=31)
        from app.tasks.order_tasks import cleanup_expired_orders
        with app.app_context():
            result = cleanup_expired_orders.run()
        assert result['cancelled'] >= 1
        with app.app_context():
            order = db.session.get(Order, oid)
            assert order.status == 'cancelled'

    def test_keeps_recent_pending_orders(self, app):
        oid = _make_order(app, status='pending', minutes_ago=5)
        from app.tasks.order_tasks import cleanup_expired_orders
        with app.app_context():
            cleanup_expired_orders.run()
        with app.app_context():
            order = db.session.get(Order, oid)
            assert order.status == 'pending'

    def test_does_not_cancel_non_pending_orders(self, app):
        oid = _make_order(app, status='completed', minutes_ago=60)
        from app.tasks.order_tasks import cleanup_expired_orders
        with app.app_context():
            cleanup_expired_orders.run()
        with app.app_context():
            order = db.session.get(Order, oid)
            assert order.status == 'completed'

    def test_returns_cancelled_count(self, app):
        _make_order(app, status='pending', minutes_ago=35)
        _make_order(app, status='pending', minutes_ago=40)
        from app.tasks.order_tasks import cleanup_expired_orders
        with app.app_context():
            result = cleanup_expired_orders.run()
        assert result['cancelled'] >= 2

    def test_no_expired_orders(self, app):
        from app.tasks.order_tasks import cleanup_expired_orders
        with app.app_context():
            result = cleanup_expired_orders.run()
        assert result['cancelled'] == 0
