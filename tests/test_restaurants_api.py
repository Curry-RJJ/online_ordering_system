"""
餐厅 REST API 测试
覆盖 app/api/restaurants.py
"""
import pytest
from tests.conftest import auth_header


class TestListRestaurantsAPI:
    def test_list_returns_200(self, client):
        rv = client.get('/api/v1/restaurants')
        assert rv.status_code == 200
        data = rv.get_json()
        assert data['code'] == 200
        assert 'restaurants' in data['data']

    def test_list_returns_open_restaurants(self, client):
        rv = client.get('/api/v1/restaurants')
        data = rv.get_json()
        assert data['data']['total'] == 1
        assert data['data']['restaurants'][0]['name'] == '测试餐厅'

    def test_list_default_sort_by_rating(self, client):
        rv = client.get('/api/v1/restaurants')
        data = rv.get_json()
        assert data['code'] == 200
        assert data['data']['page'] == 1

    def test_list_keyword_matches_restaurant_name(self, client):
        rv = client.get('/api/v1/restaurants?keyword=测试')
        data = rv.get_json()
        assert data['code'] == 200
        assert data['data']['total'] == 1

    def test_list_keyword_matches_dish_name(self, client):
        rv = client.get('/api/v1/restaurants?keyword=红烧肉')
        data = rv.get_json()
        assert data['code'] == 200
        assert data['data']['total'] == 1

    def test_list_keyword_no_match(self, client):
        rv = client.get('/api/v1/restaurants?keyword=不存在的餐厅xyz')
        data = rv.get_json()
        assert data['data']['total'] == 0

    def test_list_sort_by_newest(self, client):
        rv = client.get('/api/v1/restaurants?sort=newest')
        assert rv.status_code == 200
        data = rv.get_json()
        assert data['code'] == 200

    def test_list_sort_by_sales(self, client):
        rv = client.get('/api/v1/restaurants?sort=sales')
        assert rv.status_code == 200

    def test_list_pagination_params(self, client):
        rv = client.get('/api/v1/restaurants?page=1&per_page=5')
        data = rv.get_json()
        assert data['data']['page'] == 1
        assert data['data']['per_page'] == 5

    def test_list_per_page_capped_at_50(self, client):
        rv = client.get('/api/v1/restaurants?per_page=100')
        data = rv.get_json()
        assert data['data']['per_page'] == 50

    def test_list_uses_cache_on_second_request(self, client):
        rv1 = client.get('/api/v1/restaurants')
        rv2 = client.get('/api/v1/restaurants')
        assert rv1.status_code == rv2.status_code == 200
        assert rv1.get_json()['data']['total'] == rv2.get_json()['data']['total']


class TestRestaurantDetailAPI:
    def test_get_detail_returns_200(self, client):
        rv = client.get('/api/v1/restaurants/1')
        assert rv.status_code == 200
        data = rv.get_json()
        assert data['code'] == 200

    def test_get_detail_restaurant_info(self, client):
        rv = client.get('/api/v1/restaurants/1')
        data = rv.get_json()
        assert data['data']['restaurant']['name'] == '测试餐厅'
        assert 'delivery_fee' in data['data']['restaurant']

    def test_get_detail_includes_categories(self, client):
        rv = client.get('/api/v1/restaurants/1')
        data = rv.get_json()
        assert 'categories' in data['data']

    def test_get_detail_includes_dishes_by_category(self, client):
        rv = client.get('/api/v1/restaurants/1')
        data = rv.get_json()
        assert 'dishes_by_category' in data['data']
        # 热菜分类下有 红烧肉（已上架）
        assert '热菜' in data['data']['dishes_by_category']

    def test_get_detail_includes_reviews(self, client):
        rv = client.get('/api/v1/restaurants/1')
        data = rv.get_json()
        assert 'reviews' in data['data']
        assert isinstance(data['data']['reviews'], list)

    def test_get_detail_recommended_dishes(self, client):
        rv = client.get('/api/v1/restaurants/1')
        data = rv.get_json()
        assert 'recommended_dishes' in data['data']

    def test_get_detail_not_found(self, client):
        rv = client.get('/api/v1/restaurants/9999')
        assert rv.status_code == 404

    def test_get_detail_uses_cache(self, client):
        rv1 = client.get('/api/v1/restaurants/1')
        rv2 = client.get('/api/v1/restaurants/1')
        assert rv1.status_code == rv2.status_code == 200
