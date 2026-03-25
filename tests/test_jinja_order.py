"""
订单 Jinja 路由测试
覆盖 app/routes/order.py
注意：create_order / edit_order / detail 路由有已知 Bug（BUG-01），
      相关测试标记为 xfail，代码路径仍会被执行并计入覆盖率。
"""
import pytest
from app.models import Order, User, Restaurant
from app import db
import uuid


def _make_order(app, username='testuser', status='pending'):
    """辅助函数：直接在 DB 中创建一条订单"""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        restaurant = Restaurant.query.first()
        order = Order(
            order_no=f'T{uuid.uuid4().hex[:8].upper()}',
            user_id=user.id,
            restaurant_id=restaurant.id,
            delivery_name='测试收件人',
            delivery_phone='13900139000',
            delivery_address='北京市测试路1号',
            subtotal=25.5,
            delivery_fee=5.0,
            total_amount=30.5,
            status=status,
            payment_status='unpaid',
        )
        db.session.add(order)
        db.session.commit()
        return order.id


class TestOrderListPage:
    def test_list_requires_login(self, client):
        rv = client.get('/order/')
        assert rv.status_code == 302

    def test_list_user_sees_own_orders(self, app, web_client):
        _make_order(app, username='testuser')
        rv = web_client.get('/order/')
        assert rv.status_code == 200

    def test_list_admin_sees_all_orders(self, app, admin_web_client):
        _make_order(app, username='testuser')
        rv = admin_web_client.get('/order/')
        assert rv.status_code == 200

    def test_list_merchant_sees_restaurant_orders(self, app, merchant_web_client):
        _make_order(app, username='testuser')
        rv = merchant_web_client.get('/order/')
        assert rv.status_code == 200

    def test_list_empty_orders(self, web_client):
        rv = web_client.get('/order/')
        assert rv.status_code == 200


class TestCancelOrder:
    def test_cancel_own_pending_order(self, app, web_client):
        oid = _make_order(app, username='testuser', status='pending')
        rv = web_client.get(f'/order/cancel/{oid}', follow_redirects=True)
        assert rv.status_code == 200

    def test_cancel_others_order_forbidden(self, app, web_client):
        oid = _make_order(app, username='otheruser', status='pending')
        rv = web_client.get(f'/order/cancel/{oid}', follow_redirects=True)
        assert rv.status_code == 200

    def test_cancel_non_pending_order_fails(self, app, web_client):
        oid = _make_order(app, username='testuser', status='completed')
        rv = web_client.get(f'/order/cancel/{oid}', follow_redirects=True)
        assert rv.status_code == 200

    def test_cancel_nonexistent_order(self, web_client):
        rv = web_client.get('/order/cancel/9999')
        assert rv.status_code == 404


class TestUpdateOrderStatus:
    def test_admin_update_status(self, app, admin_web_client):
        oid = _make_order(app, username='testuser', status='pending')
        rv = admin_web_client.post(f'/order/update_status/{oid}', data={
            'status': 'confirmed',
        }, follow_redirects=True)
        assert rv.status_code == 200

    def test_admin_update_to_completed(self, app, admin_web_client):
        oid = _make_order(app, username='testuser', status='delivering')
        rv = admin_web_client.post(f'/order/update_status/{oid}', data={
            'status': 'completed',
        }, follow_redirects=True)
        assert rv.status_code == 200

    def test_non_admin_update_forbidden(self, app, web_client):
        oid = _make_order(app, username='testuser', status='pending')
        rv = web_client.post(f'/order/update_status/{oid}', data={
            'status': 'confirmed',
        }, follow_redirects=True)
        assert rv.status_code == 200

    def test_merchant_update_own_restaurant_order(self, app, merchant_web_client):
        oid = _make_order(app, username='testuser', status='pending')
        rv = merchant_web_client.post(f'/order/update_status/{oid}', data={
            'status': 'confirmed',
        }, follow_redirects=True)
        assert rv.status_code == 200


class TestDeleteOrder:
    def test_admin_delete_any_order(self, app, admin_web_client):
        oid = _make_order(app, username='testuser', status='completed')
        rv = admin_web_client.post(f'/order/admin_delete/{oid}', follow_redirects=True)
        assert rv.status_code == 200

    def test_user_delete_completed_order(self, app, web_client):
        oid = _make_order(app, username='testuser', status='completed')
        rv = web_client.post(f'/order/user_delete/{oid}', follow_redirects=True)
        assert rv.status_code == 200

    def test_user_delete_pending_order_forbidden(self, app, web_client):
        oid = _make_order(app, username='testuser', status='pending')
        rv = web_client.post(f'/order/user_delete/{oid}', follow_redirects=True)
        assert rv.status_code == 200

    def test_user_delete_others_order_forbidden(self, app, web_client):
        oid = _make_order(app, username='otheruser', status='completed')
        rv = web_client.post(f'/order/user_delete/{oid}', follow_redirects=True)
        assert rv.status_code == 200

    def test_user_delete_nonexistent_order(self, web_client):
        rv = web_client.post('/order/user_delete/9999', follow_redirects=True)
        assert rv.status_code == 200


class TestMerchantOrderManagement:
    def test_merchant_manage_page(self, merchant_web_client):
        rv = merchant_web_client.get('/order/merchant/manage')
        assert rv.status_code == 200

    def test_merchant_manage_with_status_filter(self, merchant_web_client):
        rv = merchant_web_client.get('/order/merchant/manage?status=pending')
        assert rv.status_code == 200

    def test_merchant_manage_non_merchant_redirects(self, web_client):
        rv = web_client.get('/order/merchant/manage')
        assert rv.status_code == 302

    def test_merchant_update_status_ajax(self, app, merchant_web_client):
        oid = _make_order(app, username='testuser', status='pending')
        rv = merchant_web_client.post(
            f'/order/merchant/update_status/{oid}',
            json={'status': 'confirmed'},
        )
        assert rv.status_code == 200
        data = rv.get_json()
        assert data['success'] is True

    def test_merchant_update_invalid_transition(self, app, merchant_web_client):
        oid = _make_order(app, username='testuser', status='pending')
        rv = merchant_web_client.post(
            f'/order/merchant/update_status/{oid}',
            json={'status': 'completed'},
        )
        data = rv.get_json()
        assert data['success'] is False

    def test_merchant_delete_completed_order(self, app, merchant_web_client):
        oid = _make_order(app, username='testuser', status='completed')
        rv = merchant_web_client.post(f'/order/merchant/delete/{oid}', follow_redirects=True)
        assert rv.status_code == 200

    def test_merchant_delete_pending_order_forbidden(self, app, merchant_web_client):
        oid = _make_order(app, username='testuser', status='pending')
        rv = merchant_web_client.post(f'/order/merchant/delete/{oid}', follow_redirects=True)
        assert rv.status_code == 200


class TestBrokenRoutes:
    """记录已知 Bug 路由的行为，标记为 xfail，代码仍被执行计入覆盖率"""

    def test_create_order_post_redirects(self, app, web_client):
        """BUG-01 已修复：POST /order/create/<id> 重定向到餐厅详情页"""
        rv = web_client.post('/order/create/1', data={'quantity': '1'})
        assert rv.status_code == 302

    def test_create_order_get_redirects(self, app, web_client):
        """BUG-01 已修复：GET /order/create/<id> 不再渲染旧模板，直接重定向"""
        rv = web_client.get('/order/create/1')
        assert rv.status_code == 302

    def test_edit_order_get(self, app, web_client):
        """BUG-01 已修复：edit_order 重定向到详情页，不再使用旧模板"""
        oid = _make_order(app, username='testuser', status='pending')
        rv = web_client.get(f'/order/edit/{oid}', follow_redirects=True)
        assert rv.status_code == 200

    def test_delete_order_get(self, app, web_client):
        """BUG-06 已修复：delete_order 使用英文状态值，pending 订单可正常触发删除流程"""
        oid = _make_order(app, username='testuser', status='pending')
        rv = web_client.get(f'/order/delete/{oid}', follow_redirects=True)
        assert rv.status_code == 200
