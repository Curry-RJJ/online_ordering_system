"""
Auth Jinja 路由测试
覆盖 app/routes/auth.py
"""
import pytest
from app.models import User, Address
from app import db


class TestRegisterRoute:
    def test_get_register_page(self, client):
        rv = client.get('/auth/register')
        assert rv.status_code == 200

    def test_post_register_success(self, client):
        rv = client.post('/auth/register', data={
            'username': 'newuser',
            'password': 'NewPass123',
            'confirm_password': 'NewPass123',
        }, follow_redirects=True)
        assert rv.status_code == 200

    def test_post_register_redirects_to_login(self, client):
        rv = client.post('/auth/register', data={
            'username': 'newuser2',
            'password': 'NewPass123',
            'confirm_password': 'NewPass123',
        })
        assert rv.status_code == 302
        assert '/auth/login' in rv.headers['Location']

    def test_post_register_duplicate_username(self, client):
        rv = client.post('/auth/register', data={
            'username': 'testuser',
            'password': 'AnyPass123',
            'confirm_password': 'AnyPass123',
        }, follow_redirects=True)
        assert rv.status_code == 200

    def test_post_register_creates_user_in_db(self, app, client):
        client.post('/auth/register', data={
            'username': 'brandnew',
            'password': 'BrandNew123',
            'confirm_password': 'BrandNew123',
        })
        with app.app_context():
            user = User.query.filter_by(username='brandnew').first()
            assert user is not None


class TestLoginRoute:
    def test_get_login_page(self, client):
        rv = client.get('/auth/login')
        assert rv.status_code == 200

    def test_post_login_success_redirects(self, client):
        rv = client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'Test123456',
        })
        assert rv.status_code == 302

    def test_post_login_success_goes_to_restaurant_list(self, client):
        rv = client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'Test123456',
        }, follow_redirects=True)
        assert rv.status_code == 200

    def test_post_login_wrong_password(self, client):
        rv = client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'wrongpassword',
        }, follow_redirects=True)
        assert rv.status_code == 200

    def test_post_login_nonexistent_user(self, client):
        rv = client.post('/auth/login', data={
            'username': 'nobody',
            'password': 'nopass',
        }, follow_redirects=True)
        assert rv.status_code == 200

    def test_post_login_with_next_param(self, client):
        rv = client.post('/auth/login?next=/restaurant/', data={
            'username': 'testuser',
            'password': 'Test123456',
        })
        assert rv.status_code == 302


class TestLogoutRoute:
    def test_logout_requires_login(self, client):
        rv = client.get('/auth/logout')
        assert rv.status_code == 302

    def test_logout_success(self, web_client):
        rv = web_client.get('/auth/logout', follow_redirects=True)
        assert rv.status_code == 200


class TestProfileRoute:
    def test_profile_requires_login(self, client):
        rv = client.get('/auth/profile')
        assert rv.status_code == 302

    def test_profile_get_logged_in(self, web_client):
        rv = web_client.get('/auth/profile')
        assert rv.status_code == 200

    def test_profile_update_basic_info(self, web_client):
        rv = web_client.post('/auth/profile', data={
            'username': 'testuser',
            'email': 'newemail@test.com',
            'phone': '13900139001',
        }, follow_redirects=True)
        assert rv.status_code == 200

    def test_profile_update_duplicate_username(self, web_client):
        rv = web_client.post('/auth/profile', data={
            'username': 'admin',
            'email': '',
            'phone': '',
        }, follow_redirects=True)
        assert rv.status_code == 200

    def test_profile_change_password_wrong_old_password(self, web_client):
        rv = web_client.post('/auth/profile', data={
            'username': 'testuser',
            'email': '',
            'phone': '',
            'old_password': 'wrongold',
            'new_password': 'NewPass123',
        }, follow_redirects=True)
        assert rv.status_code == 200

    def test_profile_change_password_success(self, web_client):
        rv = web_client.post('/auth/profile', data={
            'username': 'testuser',
            'email': '',
            'phone': '',
            'old_password': 'Test123456',
            'new_password': 'NewPass123',
        }, follow_redirects=True)
        assert rv.status_code == 200


class TestAddressRoutes:
    def test_add_address(self, web_client):
        rv = web_client.post('/auth/address/add', data={
            'name': '新收件人',
            'phone': '13800138001',
            'address': '北京市朝阳区新地址',
        }, follow_redirects=True)
        assert rv.status_code == 200

    def test_add_address_requires_login(self, client):
        rv = client.post('/auth/address/add', data={
            'name': '收件人',
            'phone': '13800138001',
            'address': '测试地址',
        })
        assert rv.status_code == 302

    def test_delete_address(self, app, web_client):
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            addr = Address.query.filter_by(user_id=user.id).first()
            addr_id = addr.id
        # delete 是 GET 路由
        rv = web_client.get(f'/auth/address/{addr_id}/delete', follow_redirects=True)
        assert rv.status_code == 200

    def test_set_default_address(self, app, web_client):
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            addr = Address.query.filter_by(user_id=user.id).first()
            addr_id = addr.id
        # set_default 是 GET 路由
        rv = web_client.get(f'/auth/address/{addr_id}/set_default', follow_redirects=True)
        assert rv.status_code == 200


class TestAdminUserManagement:
    def test_admin_users_page(self, admin_web_client):
        rv = admin_web_client.get('/auth/admin/users')
        assert rv.status_code == 200

    def test_admin_users_page_non_admin_redirects(self, web_client):
        rv = web_client.get('/auth/admin/users')
        assert rv.status_code == 302

    def test_admin_delete_user(self, app, admin_web_client):
        with app.app_context():
            user = User.query.filter_by(username='otheruser').first()
            uid = user.id
        rv = admin_web_client.get(f'/auth/admin/users/{uid}/delete', follow_redirects=True)
        assert rv.status_code == 200

    def test_admin_cannot_delete_self(self, app, admin_web_client):
        with app.app_context():
            admin = User.query.filter_by(username='admin').first()
            uid = admin.id
        rv = admin_web_client.get(f'/auth/admin/users/{uid}/delete', follow_redirects=True)
        assert rv.status_code == 200

    def test_admin_change_user_role(self, app, admin_web_client):
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            uid = user.id
        rv = admin_web_client.post(f'/auth/admin/users/{uid}/change_role', data={
            'new_role': 'admin',
        }, follow_redirects=True)
        assert rv.status_code == 200

    def test_admin_change_role_invalid(self, app, admin_web_client):
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            uid = user.id
        rv = admin_web_client.post(f'/auth/admin/users/{uid}/change_role', data={
            'new_role': 'superadmin',
        }, follow_redirects=True)
        assert rv.status_code == 200

    def test_toggle_user_role(self, app, admin_web_client):
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            uid = user.id
        rv = admin_web_client.get(f'/auth/admin/users/{uid}/toggle_role', follow_redirects=True)
        assert rv.status_code == 200


class TestApplyAdminRoute:
    def test_get_apply_admin_page(self, web_client):
        rv = web_client.get('/auth/apply_admin')
        assert rv.status_code == 200

    def test_post_apply_admin(self, web_client):
        rv = web_client.post('/auth/apply_admin', data={
            'reason': '希望成为管理员',
        }, follow_redirects=True)
        assert rv.status_code == 200

    def test_admin_applications_page(self, admin_web_client):
        rv = admin_web_client.get('/auth/admin/applications')
        assert rv.status_code == 200


class TestMerchantApplicationRoute:
    def test_get_apply_merchant_page(self, merchant_web_client):
        # 该路由要求 role='merchant'
        rv = merchant_web_client.get('/auth/merchant/apply_restaurant')
        assert rv.status_code == 200

    def test_admin_merchant_applications_page(self, admin_web_client):
        # 商家申请与管理员申请合并在同一页面
        rv = admin_web_client.get('/auth/admin/applications')
        assert rv.status_code == 200

    def test_admin_change_requests_page(self, admin_web_client):
        # 变更审核在 restaurant 蓝图下
        rv = admin_web_client.get('/restaurant/admin/change_requests')
        assert rv.status_code == 200
