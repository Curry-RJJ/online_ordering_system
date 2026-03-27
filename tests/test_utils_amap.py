"""
工具函数单元测试（第三步）
覆盖 app/utils.py 中的 haversine / amap_ip_locate / amap_regeocode
"""
import pytest
from unittest.mock import patch, MagicMock
from app.utils import haversine


class TestHaversine:
    """haversine() 不依赖 API，纯数学，可直接测试"""

    def test_same_point_is_zero(self):
        assert haversine(22.6899, 114.3490, 22.6899, 114.3490) == pytest.approx(0.0, abs=1e-6)

    def test_known_distance(self):
        # 北京天安门(39.9087,116.3975) → 上海外滩(31.2397,121.4917) ≈ 1065 km
        d = haversine(39.9087, 116.3975, 31.2397, 121.4917)
        assert 1050 < d < 1090

    def test_short_distance(self):
        # 同城两点，约几千米
        d = haversine(22.6899, 114.3490, 22.6950, 114.3560)
        assert 0.5 < d < 2.0

    def test_symmetry(self):
        d1 = haversine(22.6899, 114.3490, 31.2397, 121.4917)
        d2 = haversine(31.2397, 121.4917, 22.6899, 114.3490)
        assert d1 == pytest.approx(d2, rel=1e-6)

    def test_returns_float(self):
        result = haversine(0.0, 0.0, 1.0, 1.0)
        assert isinstance(result, float)


class TestAmapIpLocate:
    """amap_ip_locate() 需 Flask app context 及 AMAP_WEB_KEY"""

    def test_returns_none_when_no_key(self, app):
        """无 Key 时直接返回 None，不发请求"""
        with app.app_context():
            app.config['AMAP_WEB_KEY'] = ''
            from app.utils import amap_ip_locate
            assert amap_ip_locate('8.8.8.8') is None

    def test_returns_tuple_on_success(self, app):
        """Mock 正常响应时返回 (lat, lng, city)"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'status': '1',
            'rectangle': '114.3490,22.6500;114.4000,22.7200',
            'city': '深圳市',
        }
        with app.app_context():
            app.config['AMAP_WEB_KEY'] = 'fake_key'
            with patch('requests.get', return_value=mock_response):
                from app.utils import amap_ip_locate
                result = amap_ip_locate('1.2.3.4')
        assert result is not None
        lat, lng, city = result
        assert isinstance(lat, float)
        assert isinstance(lng, float)
        assert city == '深圳市'

    def test_returns_none_on_api_error(self, app):
        """API 返回 status != '1' 时返回 None"""
        mock_response = MagicMock()
        mock_response.json.return_value = {'status': '0', 'info': 'INVALID_KEY'}
        with app.app_context():
            app.config['AMAP_WEB_KEY'] = 'fake_key'
            with patch('requests.get', return_value=mock_response):
                from app.utils import amap_ip_locate
                result = amap_ip_locate('1.2.3.4')
        assert result is None

    def test_returns_none_on_network_exception(self, app):
        """网络异常时返回 None，不抛出"""
        with app.app_context():
            app.config['AMAP_WEB_KEY'] = 'fake_key'
            with patch('requests.get', side_effect=Exception('timeout')):
                from app.utils import amap_ip_locate
                result = amap_ip_locate('1.2.3.4')
        assert result is None


class TestAmapRegeocode:
    """amap_regeocode() 需 Flask app context 及 AMAP_WEB_KEY"""

    def test_returns_none_when_no_key(self, app):
        with app.app_context():
            app.config['AMAP_WEB_KEY'] = ''
            from app.utils import amap_regeocode
            assert amap_regeocode(22.6899, 114.3490) is None

    def test_returns_address_on_success(self, app):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'status': '1',
            'regeocode': {'formatted_address': '广东省深圳市南山区科技园'},
        }
        with app.app_context():
            app.config['AMAP_WEB_KEY'] = 'fake_key'
            with patch('requests.get', return_value=mock_response):
                from app.utils import amap_regeocode
                result = amap_regeocode(22.6899, 114.3490)
        assert result == '广东省深圳市南山区科技园'

    def test_returns_none_on_api_error(self, app):
        mock_response = MagicMock()
        mock_response.json.return_value = {'status': '0'}
        with app.app_context():
            app.config['AMAP_WEB_KEY'] = 'fake_key'
            with patch('requests.get', return_value=mock_response):
                from app.utils import amap_regeocode
                result = amap_regeocode(22.6899, 114.3490)
        assert result is None

    def test_returns_none_on_network_exception(self, app):
        with app.app_context():
            app.config['AMAP_WEB_KEY'] = 'fake_key'
            with patch('requests.get', side_effect=Exception('timeout')):
                from app.utils import amap_regeocode
                result = amap_regeocode(22.6899, 114.3490)
        assert result is None
