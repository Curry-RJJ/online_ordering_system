"""
购物车 API 测试
对应测试报告：M05 - TC-CART-01~07
"""
import pytest
from app.models import Dish
from tests.conftest import auth_header


def _get_dish_id(app, available=True):
    """从 DB 取第一个符合条件的菜品 ID"""
    with app.app_context():
        dish = Dish.query.filter_by(available=available).first()
        return dish.id


class TestAddToCart:
    """TC-CART-01: 添加商品到购物车"""

    def test_tc_cart_01_add_item(self, client, app, user_token):
        dish_id = _get_dish_id(app, available=True)
        resp = client.post('/api/v1/cart/items',
                           json={'dish_id': dish_id, 'quantity': 1},
                           headers=auth_header(user_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['code'] == 200
        assert data['data']['cart_size'] == 1

    """TC-CART-02: 重复添加同一商品，数量应累加"""

    def test_tc_cart_02_add_same_item_accumulates(self, client, app, user_token):
        dish_id = _get_dish_id(app, available=True)
        headers = auth_header(user_token)
        client.post('/api/v1/cart/items', json={'dish_id': dish_id, 'quantity': 2}, headers=headers)
        client.post('/api/v1/cart/items', json={'dish_id': dish_id, 'quantity': 3}, headers=headers)

        resp = client.get('/api/v1/cart', headers=headers)
        data = resp.get_json()
        items = data['data']['items']
        dish_item = next(i for i in items if i['dish_id'] == dish_id)
        assert dish_item['quantity'] == 5  # 2+3 累加

    """TC-CART-05: 添加已下架商品应返回错误"""

    def test_tc_cart_05_add_unavailable_item(self, client, app, user_token):
        dish_id = _get_dish_id(app, available=False)
        resp = client.post('/api/v1/cart/items',
                           json={'dish_id': dish_id, 'quantity': 1},
                           headers=auth_header(user_token))
        assert resp.status_code == 400
        data = resp.get_json()
        assert '下架' in data['message']

    def test_add_nonexistent_dish(self, client, user_token):
        resp = client.post('/api/v1/cart/items',
                           json={'dish_id': 99999, 'quantity': 1},
                           headers=auth_header(user_token))
        assert resp.status_code == 404

    def test_add_without_token(self, client, app):
        dish_id = _get_dish_id(app, available=True)
        resp = client.post('/api/v1/cart/items', json={'dish_id': dish_id, 'quantity': 1})
        assert resp.status_code == 401

    def test_add_missing_dish_id(self, client, user_token):
        resp = client.post('/api/v1/cart/items',
                           json={'quantity': 1},
                           headers=auth_header(user_token))
        assert resp.status_code == 400


class TestUpdateCartItem:
    """TC-CART-03: 更新购物车数量"""

    def test_tc_cart_03_update_quantity(self, client, app, user_token):
        dish_id = _get_dish_id(app, available=True)
        headers = auth_header(user_token)
        client.post('/api/v1/cart/items', json={'dish_id': dish_id, 'quantity': 1}, headers=headers)

        resp = client.put(f'/api/v1/cart/items/{dish_id}',
                          json={'quantity': 5},
                          headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['data']['quantity'] == 5

    """TC-CART-04: 更新数量为 0 应返回错误"""

    def test_tc_cart_04_update_quantity_to_zero(self, client, app, user_token):
        dish_id = _get_dish_id(app, available=True)
        headers = auth_header(user_token)
        client.post('/api/v1/cart/items', json={'dish_id': dish_id, 'quantity': 1}, headers=headers)

        resp = client.put(f'/api/v1/cart/items/{dish_id}',
                          json={'quantity': 0},
                          headers=headers)
        assert resp.status_code == 400

    def test_update_item_not_in_cart(self, client, user_token):
        resp = client.put('/api/v1/cart/items/99999',
                          json={'quantity': 3},
                          headers=auth_header(user_token))
        assert resp.status_code == 404


class TestRemoveCartItem:
    def test_remove_item(self, client, app, user_token):
        dish_id = _get_dish_id(app, available=True)
        headers = auth_header(user_token)
        client.post('/api/v1/cart/items', json={'dish_id': dish_id, 'quantity': 2}, headers=headers)

        resp = client.delete(f'/api/v1/cart/items/{dish_id}', headers=headers)
        assert resp.status_code == 200

        cart_resp = client.get('/api/v1/cart', headers=headers)
        data = cart_resp.get_json()
        assert data['data']['items'] == []


class TestClearCart:
    """TC-CART-06: 清空购物车"""

    def test_tc_cart_06_clear_cart(self, client, app, user_token):
        dish_id = _get_dish_id(app, available=True)
        headers = auth_header(user_token)
        client.post('/api/v1/cart/items', json={'dish_id': dish_id, 'quantity': 3}, headers=headers)

        resp = client.delete('/api/v1/cart', headers=headers)
        assert resp.status_code == 200

        cart_resp = client.get('/api/v1/cart', headers=headers)
        data = cart_resp.get_json()
        assert data['data']['items'] == []
        assert data['data']['total_amount'] == 0


class TestCartGroupByRestaurant:
    """TC-CART-07: 购物车按餐厅分组显示"""

    def test_tc_cart_07_cart_grouped_by_restaurant(self, client, app, user_token):
        dish_id = _get_dish_id(app, available=True)
        headers = auth_header(user_token)
        client.post('/api/v1/cart/items', json={'dish_id': dish_id, 'quantity': 2}, headers=headers)

        resp = client.get('/api/v1/cart', headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()['data']

        # 检查响应结构：有 items、total_amount、restaurants
        assert 'items' in data
        assert 'total_amount' in data
        assert 'restaurants' in data
        assert len(data['restaurants']) >= 1

        # 检查 restaurants 中包含 delivery_fee
        rest_info = data['restaurants'][0]
        assert 'restaurant_name' in rest_info
        assert 'delivery_fee' in rest_info
