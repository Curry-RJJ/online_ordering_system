"""
健康检查接口测试
覆盖 app/__init__.py 中的 /health 路由
"""
import json


class TestHealthCheck:
    def test_health_returns_200(self, client):
        rv = client.get('/health')
        assert rv.status_code == 200

    def test_health_returns_json(self, client):
        rv = client.get('/health')
        data = json.loads(rv.data)
        assert 'status' in data
        assert 'timestamp' in data

    def test_health_db_ok(self, client):
        rv = client.get('/health')
        data = json.loads(rv.data)
        assert data['db'] == 'ok'

    def test_health_cache_ok(self, client):
        rv = client.get('/health')
        data = json.loads(rv.data)
        assert data['cache'] == 'ok'

    def test_health_status_ok(self, client):
        rv = client.get('/health')
        data = json.loads(rv.data)
        assert data['status'] == 'ok'

    def test_health_no_auth_required(self, client):
        """健康检查不需要登录"""
        rv = client.get('/health')
        assert rv.status_code != 302
        assert rv.status_code != 401
