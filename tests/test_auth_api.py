"""
用户认证 API 测试
对应测试报告：
  M01 - TC-AUTH-01~06（注册、登录、密码修改）
  权限控制 - TC-PERM-04（未登录访问受保护接口）
"""
import pytest
from flask_jwt_extended import create_refresh_token

from app.models import User
from tests.conftest import auth_header


class TestRegister:
    """TC-AUTH-01: 新用户注册成功"""

    def test_tc_auth_01_register_success(self, client):
        resp = client.post('/api/v1/auth/register', json={
            'username': 'newuser', 'password': 'Test123456'
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['code'] == 201
        assert 'access_token' in data['data']
        assert data['data']['user']['username'] == 'newuser'

    """TC-AUTH-02: 重复用户名注册失败"""

    def test_tc_auth_02_register_duplicate_username(self, client):
        resp = client.post('/api/v1/auth/register', json={
            'username': 'admin', 'password': 'Test123456'
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert '用户名已存在' in data['message']

    def test_register_invalid_params_missing_password(self, client):
        resp = client.post('/api/v1/auth/register', json={'username': 'newuser'})
        assert resp.status_code == 400

    def test_register_username_too_short(self, client):
        resp = client.post('/api/v1/auth/register', json={
            'username': 'ab', 'password': 'Test123456'
        })
        assert resp.status_code == 400

    def test_register_returns_token_pair(self, client):
        resp = client.post('/api/v1/auth/register', json={
            'username': 'brandnewuser', 'password': 'MyPass123'
        })
        data = resp.get_json()
        assert 'access_token' in data['data']
        assert 'refresh_token' in data['data']


class TestLogin:
    """TC-AUTH-03: 正确凭据登录成功"""

    def test_tc_auth_03_login_success(self, client):
        resp = client.post('/api/v1/auth/login', json={
            'username': 'admin', 'password': 'admin123'
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['code'] == 200
        assert data['message'] == '登录成功'
        assert 'access_token' in data['data']
        assert data['data']['user']['role'] == 'admin'

    """TC-AUTH-04: 错误密码登录失败"""

    def test_tc_auth_04_login_wrong_password(self, client):
        resp = client.post('/api/v1/auth/login', json={
            'username': 'admin', 'password': 'wrongpass'
        })
        assert resp.status_code == 401
        data = resp.get_json()
        assert '用户名或密码错误' in data['message']

    def test_login_nonexistent_user(self, client):
        resp = client.post('/api/v1/auth/login', json={
            'username': 'nosuchuser', 'password': 'Test123456'
        })
        assert resp.status_code == 401

    def test_login_missing_fields(self, client):
        resp = client.post('/api/v1/auth/login', json={'username': 'admin'})
        assert resp.status_code == 400


class TestGetMe:
    """TC-PERM-04: 未登录访问受保护接口应返回 401"""

    def test_tc_perm_04_unauthenticated_access(self, client):
        resp = client.get('/api/v1/auth/me')
        assert resp.status_code == 401

    def test_get_me_with_valid_token(self, client, user_token):
        resp = client.get('/api/v1/auth/me',
                          headers=auth_header(user_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['data']['username'] == 'testuser'

    def test_get_me_invalid_token(self, client):
        resp = client.get('/api/v1/auth/me',
                          headers={'Authorization': 'Bearer invalid.token.here'})
        assert resp.status_code == 401


class TestTokenRefresh:
    """JWT Token 刷新"""

    def test_refresh_token(self, client, app):
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            refresh_token = create_refresh_token(identity=str(user.id))

        resp = client.post('/api/v1/auth/refresh',
                           headers={'Authorization': f'Bearer {refresh_token}'})
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'access_token' in data['data']

    def test_refresh_with_access_token_fails(self, client, user_token):
        """用 access_token 尝试刷新应失败（自定义错误handler返回 401）"""
        resp = client.post('/api/v1/auth/refresh',
                           headers={'Authorization': f'Bearer {user_token}'})
        assert resp.status_code in (401, 422)
