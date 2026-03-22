"""
订单 API 测试
对应测试报告：M06 - TC-ORD-01~07
"""
import pytest
from app.models import Dish, Address, Order
from app import db
from tests.conftest import auth_header


# ──────────────────────────────────────────────
# 辅助：向购物车添加可用菜品
# ──────────────────────────────────────────────

def _fill_cart(client, token, app, quantity=1):
    """向 testuser 购物车加入一个可用菜品，返回 dish_id"""
    with app.app_context():
        dish = Dish.query.filter_by(available=True).first()
        dish_id = dish.id
    client.post('/api/v1/cart/items',
                json={'dish_id': dish_id, 'quantity': quantity},
                headers=auth_header(token))
    return dish_id


def _get_address_id(app, username='testuser'):
    with app.app_context():
        from app.models import User
        user = User.query.filter_by(username=username).first()
        addr = Address.query.filter_by(user_id=user.id).first()
        return addr.id if addr else None


class TestCreateOrder:
    """TC-ORD-01: 提交订单成功，购物车清空，生成唯一订单号"""

    def test_tc_ord_01_create_order(self, client, app, user_token):
        _fill_cart(client, user_token, app)
        address_id = _get_address_id(app)

        resp = client.post('/api/v1/orders',
                           json={'address_id': address_id, 'remark': '不要辣'},
                           headers=auth_header(user_token))
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['code'] == 201
        assert data['message'] == '下单成功'
        orders = data['data']['orders']
        assert len(orders) >= 1
        # 订单号唯一性验证（有值且非空）
        assert orders[0]['order_no'] != ''

        # 购物车应已清空
        cart_resp = client.get('/api/v1/cart', headers=auth_header(user_token))
        assert cart_resp.get_json()['data']['items'] == []

    def test_create_order_empty_cart(self, client, app, user_token):
        """购物车为空时下单应返回错误"""
        address_id = _get_address_id(app)
        resp = client.post('/api/v1/orders',
                           json={'address_id': address_id},
                           headers=auth_header(user_token))
        assert resp.status_code == 400
        assert '购物车为空' in resp.get_json()['message']

    def test_create_order_invalid_address(self, client, app, user_token):
        """使用不存在的地址 ID 下单应返回 404"""
        _fill_cart(client, user_token, app)
        resp = client.post('/api/v1/orders',
                           json={'address_id': 99999},
                           headers=auth_header(user_token))
        assert resp.status_code == 404

    def test_create_order_missing_address_id(self, client, app, user_token):
        _fill_cart(client, user_token, app)
        resp = client.post('/api/v1/orders', json={}, headers=auth_header(user_token))
        assert resp.status_code == 400

    def test_create_order_requires_auth(self, client):
        resp = client.post('/api/v1/orders', json={'address_id': 1})
        assert resp.status_code == 401


class TestGetOrderDetail:
    """TC-ORD-02: 查看订单详情"""

    def _create_order(self, client, app, token):
        _fill_cart(client, token, app)
        address_id = _get_address_id(app)
        client.post('/api/v1/orders',
                    json={'address_id': address_id},
                    headers=auth_header(token))
        with app.app_context():
            from app.models import User
            user = User.query.filter_by(username='testuser').first()
            order = Order.query.filter_by(user_id=user.id).first()
            return order.id

    def test_tc_ord_02_get_order_detail(self, client, app, user_token):
        order_id = self._create_order(client, app, user_token)
        resp = client.get(f'/api/v1/orders/{order_id}',
                          headers=auth_header(user_token))
        assert resp.status_code == 200
        data = resp.get_json()['data']
        assert 'items' in data
        assert 'total_amount' in data
        assert 'status' in data

    def test_get_nonexistent_order(self, client, user_token):
        resp = client.get('/api/v1/orders/99999', headers=auth_header(user_token))
        assert resp.status_code == 404


class TestCancelOrder:
    """TC-ORD-03/04: 取消订单"""

    def _place_order(self, client, app, token):
        _fill_cart(client, token, app)
        address_id = _get_address_id(app)
        client.post('/api/v1/orders',
                    json={'address_id': address_id},
                    headers=auth_header(token))
        with app.app_context():
            from app.models import User
            user = User.query.filter_by(username='testuser').first()
            return Order.query.filter_by(user_id=user.id).order_by(Order.id.desc()).first().id

    def test_tc_ord_03_cancel_pending_order(self, client, app, user_token):
        """TC-ORD-03: 取消 pending 状态的订单应成功"""
        order_id = self._place_order(client, app, user_token)
        resp = client.patch(f'/api/v1/orders/{order_id}/cancel',
                            headers=auth_header(user_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['data']['status'] == 'cancelled'

    def test_tc_ord_04_cancel_confirmed_order_fails(self, client, app, user_token):
        """TC-ORD-04: 取消非 pending 状态的订单应失败"""
        order_id = self._place_order(client, app, user_token)

        # 模拟订单已被确认
        with app.app_context():
            order = Order.query.get(order_id)
            order.status = 'confirmed'
            db.session.commit()

        resp = client.patch(f'/api/v1/orders/{order_id}/cancel',
                            headers=auth_header(user_token))
        assert resp.status_code == 400
        assert '不可取消' in resp.get_json()['message']

    def test_cancel_nonexistent_order(self, client, user_token):
        resp = client.patch('/api/v1/orders/99999/cancel',
                            headers=auth_header(user_token))
        assert resp.status_code == 404


class TestOrderIsolation:
    """TC-ORD-07: 用户不能查看他人的订单"""

    def test_tc_ord_07_user_cannot_access_others_order(self, client, app, user_token, other_token):
        # testuser 下单
        _fill_cart(client, user_token, app)
        address_id = _get_address_id(app)
        client.post('/api/v1/orders',
                    json={'address_id': address_id},
                    headers=auth_header(user_token))

        with app.app_context():
            from app.models import User
            user = User.query.filter_by(username='testuser').first()
            order = Order.query.filter_by(user_id=user.id).first()
            order_id = order.id

        # otheruser 尝试访问，应被拒绝
        resp = client.get(f'/api/v1/orders/{order_id}',
                          headers=auth_header(other_token))
        assert resp.status_code == 403

    def test_order_list_only_returns_own_orders(self, client, app, user_token, other_token):
        """订单列表只返回当前用户自己的订单"""
        _fill_cart(client, user_token, app)
        address_id = _get_address_id(app)
        client.post('/api/v1/orders',
                    json={'address_id': address_id},
                    headers=auth_header(user_token))

        # otheruser 查看自己的订单列表，应为空
        resp = client.get('/api/v1/orders', headers=auth_header(other_token))
        assert resp.status_code == 200
        assert resp.get_json()['data']['total'] == 0
