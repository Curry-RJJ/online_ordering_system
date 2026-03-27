"""
Location 路由测试
覆盖 app/routes/location.py 及 before_request 拦截逻辑
"""
import pytest
from werkzeug.security import generate_password_hash

from app import db
from app.models import User, Address


# ──────────────────────────────────────────────────────────────
# 辅助 fixture：未完成位置设置的用户
# ──────────────────────────────────────────────────────────────

@pytest.fixture
def unconfirmed_client(client, app):
    """已登录、但 location_confirmed=False 的 Web 客户端"""
    with app.app_context():
        u = User(
            username='unconfirmed_user',
            password=generate_password_hash('Test123456'),
            role='user',
            phone='13700137000',
            location_confirmed=False,
        )
        db.session.add(u)
        db.session.commit()
    client.post('/auth/login', data={
        'username': 'unconfirmed_user',
        'password': 'Test123456',
    })
    return client


# ──────────────────────────────────────────────────────────────
# GET /setup-location
# ──────────────────────────────────────────────────────────────

class TestSetupLocationGet:
    def test_requires_login(self, client):
        """未登录访问选位置页面应重定向到登录"""
        rv = client.get('/setup-location')
        assert rv.status_code == 302
        assert '/auth/login' in rv.headers['Location']

    def test_get_page_returns_200(self, unconfirmed_client):
        """已登录未确认用户可以访问选位置页面"""
        rv = unconfirmed_client.get('/setup-location')
        assert rv.status_code == 200

    def test_page_contains_map_container(self, unconfirmed_client):
        """页面包含地图容器元素"""
        rv = unconfirmed_client.get('/setup-location')
        assert b'amap-div' in rv.data

    def test_page_contains_search_input(self, unconfirmed_client):
        """页面包含搜索框"""
        rv = unconfirmed_client.get('/setup-location')
        assert b'amap-search-input' in rv.data

    def test_page_contains_amap_script(self, unconfirmed_client):
        """页面包含高德地图 JS API script 标签"""
        rv = unconfirmed_client.get('/setup-location')
        assert b'webapi.amap.com/maps' in rv.data

    def test_confirmed_user_not_redirected_to_setup(self, web_client):
        """已确认位置的用户访问主页，不应被重定向到选位置"""
        rv = web_client.get('/restaurant/', follow_redirects=False)
        # 不应跳到 setup-location
        location_header = rv.headers.get('Location', '')
        assert 'setup-location' not in location_header


# ──────────────────────────────────────────────────────────────
# POST /setup-location
# ──────────────────────────────────────────────────────────────

class TestSetupLocationPost:
    def test_post_valid_location_redirects(self, unconfirmed_client):
        """提交有效坐标后应重定向到餐厅列表"""
        rv = unconfirmed_client.post('/setup-location', data={
            'latitude' : '22.689800',
            'longitude': '114.349000',
            'address'  : '广东省深圳市坪山区坑梓街道',
        })
        assert rv.status_code == 302
        assert '/restaurant/' in rv.headers['Location']

    def test_post_sets_location_confirmed(self, app, unconfirmed_client):
        """成功提交后 user.location_confirmed 变为 True"""
        unconfirmed_client.post('/setup-location', data={
            'latitude' : '22.689800',
            'longitude': '114.349000',
            'address'  : '广东省深圳市坪山区',
        })
        with app.app_context():
            u = User.query.filter_by(username='unconfirmed_user').first()
            assert u.location_confirmed is True

    def test_post_creates_default_address(self, app, unconfirmed_client):
        """成功提交后应在 Address 表创建默认地址"""
        unconfirmed_client.post('/setup-location', data={
            'latitude' : '22.689800',
            'longitude': '114.349000',
            'address'  : '广东省深圳市坪山区坑梓街道',
        })
        with app.app_context():
            u    = User.query.filter_by(username='unconfirmed_user').first()
            addr = Address.query.filter_by(user_id=u.id, is_default=True).first()
            assert addr is not None
            assert addr.address == '广东省深圳市坪山区坑梓街道'
            assert abs(addr.latitude  - 22.689800) < 1e-5
            assert abs(addr.longitude - 114.349000) < 1e-5

    def test_post_missing_coordinates_redirects_back(self, unconfirmed_client):
        """坐标缺失时应重定向回选位置页面"""
        rv = unconfirmed_client.post('/setup-location', data={
            'latitude' : '',
            'longitude': '',
            'address'  : '某个地址',
        })
        assert rv.status_code == 302
        assert 'setup-location' in rv.headers['Location']

    def test_post_invalid_coordinates_redirects_back(self, unconfirmed_client):
        """坐标非数字时应重定向回选位置页面"""
        rv = unconfirmed_client.post('/setup-location', data={
            'latitude' : 'not-a-number',
            'longitude': '114.349000',
            'address'  : '某个地址',
        })
        assert rv.status_code == 302
        assert 'setup-location' in rv.headers['Location']

    def test_post_missing_address_redirects_back(self, unconfirmed_client):
        """地址文字为空时应重定向回选位置页面"""
        rv = unconfirmed_client.post('/setup-location', data={
            'latitude' : '22.689800',
            'longitude': '114.349000',
            'address'  : '',
        })
        assert rv.status_code == 302
        assert 'setup-location' in rv.headers['Location']

    def test_post_does_not_create_duplicate_default_address(self, app, unconfirmed_client):
        """若已有默认地址，不应再创建一条新的默认地址"""
        with app.app_context():
            u = User.query.filter_by(username='unconfirmed_user').first()
            existing = Address(
                user_id=u.id, name=u.username, phone='13700137000',
                address='已有默认地址', is_default=True,
            )
            db.session.add(existing)
            db.session.commit()

        unconfirmed_client.post('/setup-location', data={
            'latitude' : '22.689800',
            'longitude': '114.349000',
            'address'  : '广东省深圳市坪山区',
        })

        with app.app_context():
            u = User.query.filter_by(username='unconfirmed_user').first()
            count = Address.query.filter_by(user_id=u.id, is_default=True).count()
            assert count == 1


# ──────────────────────────────────────────────────────────────
# before_request 拦截行为
# ──────────────────────────────────────────────────────────────

class TestBeforeRequestInterception:
    def test_unconfirmed_user_redirected_from_restaurant_list(self, unconfirmed_client):
        """未确认位置的用户访问餐厅列表，应被重定向到 setup-location"""
        rv = unconfirmed_client.get('/restaurant/')
        assert rv.status_code == 302
        assert 'setup-location' in rv.headers['Location']

    def test_unconfirmed_user_can_access_logout(self, unconfirmed_client):
        """未确认位置的用户仍可访问 logout（白名单）"""
        rv = unconfirmed_client.get('/auth/logout')
        # logout 会重定向到 login，不应跳到 setup-location
        assert rv.status_code == 302
        assert 'setup-location' not in rv.headers.get('Location', '')

    def test_unauthenticated_not_redirected_to_setup(self, client):
        """未登录用户访问任意页面，不触发位置拦截（交由 login_required 处理）"""
        rv = client.get('/restaurant/')
        location = rv.headers.get('Location', '')
        assert 'setup-location' not in location
