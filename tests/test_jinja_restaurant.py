"""
餐厅 Jinja 路由测试
覆盖 app/routes/restaurant.py
"""
import pytest
from app.models import Restaurant
from app import db


class TestRestaurantListPage:
    def test_list_page_no_login_required(self, client):
        rv = client.get('/restaurant/')
        assert rv.status_code == 200

    def test_list_page_with_keyword(self, client):
        rv = client.get('/restaurant/?keyword=测试')
        assert rv.status_code == 200

    def test_list_page_no_keyword_match(self, client):
        rv = client.get('/restaurant/?keyword=不存在的餐厅xyz')
        assert rv.status_code == 200

    def test_list_page_sort_by_rating(self, client):
        rv = client.get('/restaurant/?sort=rating')
        assert rv.status_code == 200

    def test_list_page_sort_by_sales(self, client):
        rv = client.get('/restaurant/?sort=sales')
        assert rv.status_code == 200

    def test_list_page_with_category_filter(self, client):
        rv = client.get('/restaurant/?category=1')
        assert rv.status_code == 200

    def test_list_page_uses_cache(self, client):
        rv1 = client.get('/restaurant/')
        rv2 = client.get('/restaurant/')
        assert rv1.status_code == rv2.status_code == 200


class TestRestaurantDetailPage:
    def test_detail_page_no_login_required(self, client):
        rv = client.get('/restaurant/1')
        assert rv.status_code == 200

    def test_detail_page_not_found(self, client):
        rv = client.get('/restaurant/9999')
        assert rv.status_code == 404

    def test_detail_page_logged_in_user(self, web_client):
        rv = web_client.get('/restaurant/1')
        assert rv.status_code == 200


class TestRestaurantMenuAjax:
    def test_menu_ajax_returns_json(self, client):
        rv = client.get('/restaurant/1/menu')
        assert rv.status_code == 200
        data = rv.get_json()
        assert 'dishes' in data

    def test_menu_ajax_not_found(self, client):
        rv = client.get('/restaurant/9999/menu')
        assert rv.status_code == 404

    def test_menu_ajax_with_category_filter(self, client):
        rv = client.get('/restaurant/1/menu?category_id=1')
        assert rv.status_code == 200
        data = rv.get_json()
        assert 'dishes' in data


class TestRestaurantSearch:
    def test_search_returns_json(self, client):
        rv = client.get('/restaurant/search?q=测试')
        assert rv.status_code == 200
        data = rv.get_json()
        assert 'restaurants' in data

    def test_search_empty_query(self, client):
        rv = client.get('/restaurant/search')
        assert rv.status_code == 200
        data = rv.get_json()
        assert data['restaurants'] == []

    def test_search_no_match(self, client):
        rv = client.get('/restaurant/search?q=不存在xyz')
        data = rv.get_json()
        assert data['restaurants'] == []


class TestAdminRestaurantManagement:
    def test_admin_list_page(self, admin_web_client):
        # 正确路由：/restaurant/admin
        rv = admin_web_client.get('/restaurant/admin')
        assert rv.status_code == 200

    def test_admin_list_non_admin_redirects(self, web_client):
        rv = web_client.get('/restaurant/admin')
        assert rv.status_code == 302

    def test_add_restaurant_page_admin(self, admin_web_client):
        rv = admin_web_client.get('/restaurant/add')
        assert rv.status_code == 200

    def test_add_restaurant_page_non_admin_redirects(self, web_client):
        rv = web_client.get('/restaurant/add')
        assert rv.status_code == 302

    def test_add_restaurant_post_admin(self, admin_web_client):
        # 带坐标提交，应重定向到管理列表
        rv = admin_web_client.post('/restaurant/add', data={
            'name': '新餐厅',
            'description': '这是一个新餐厅的描述信息',
            'address': '上海市测试路',
            'phone': '021-12345678',
            'business_hours': '10:00-22:00',
            'delivery_fee': '5',
            'min_order': '20',
            'cuisine_type': '中餐',
            'rating': '4.5',
            'review_count': '0',
            'latitude': '22.6899',
            'longitude': '114.3490',
        })
        assert rv.status_code == 302
        assert '/restaurant/admin' in rv.headers['Location']

    def test_add_restaurant_post_without_coords_rejected(self, admin_web_client):
        """不提供坐标时应拒绝并重定向回表单"""
        rv = admin_web_client.post('/restaurant/add', data={
            'name': '无坐标餐厅',
            'address': '上海市测试路',
            'delivery_fee': '5',
            'min_order': '20',
        })
        assert rv.status_code == 302
        assert '/restaurant/add' in rv.headers['Location']

    def test_edit_restaurant_page_admin(self, admin_web_client):
        rv = admin_web_client.get('/restaurant/1/edit')
        assert rv.status_code == 200

    def test_edit_restaurant_page_non_admin_redirects(self, web_client):
        rv = web_client.get('/restaurant/1/edit')
        assert rv.status_code == 302

    def test_edit_restaurant_page_merchant(self, merchant_web_client):
        rv = merchant_web_client.get('/restaurant/1/edit')
        assert rv.status_code == 200

    def test_delete_restaurant_admin(self, app, admin_web_client):
        with app.app_context():
            r = Restaurant(name='待删除餐厅', address='测试', status='closed',
                           description='描述内容不能为空')
            db.session.add(r)
            db.session.commit()
            rid = r.id
        # delete 是 GET 路由
        rv = admin_web_client.get(f'/restaurant/{rid}/delete')
        assert rv.status_code == 302

    def test_delete_restaurant_non_admin_forbidden(self, web_client):
        # 非管理员会被重定向
        rv = web_client.get('/restaurant/1/delete')
        assert rv.status_code == 302

    def test_toggle_restaurant_status_admin(self, admin_web_client):
        # toggle_status 是 JSON 接口
        rv = admin_web_client.post('/restaurant/1/toggle_status',
                                   json={'status': 'closed'})
        assert rv.status_code == 200
        data = rv.get_json()
        assert data['success'] is True


class TestRestaurantCategoryPage:
    def test_category_list_page_admin(self, admin_web_client):
        # restaurant_category_bp 的 url_prefix 是 /restaurant-category
        rv = admin_web_client.get('/restaurant-category/list')
        assert rv.status_code == 200


class TestEditRestaurantWithCoords:
    """第五步：编辑餐厅时更新坐标"""

    def test_edit_restaurant_post_with_coords_admin(self, admin_web_client):
        rv = admin_web_client.post('/restaurant/1/edit', data={
            'name': '测试餐厅已修改',
            'address': '深圳市南山区',
            'delivery_fee': '5',
            'min_order': '20',
            'business_hours': '09:00-21:00',
            'latitude': '22.6899',
            'longitude': '114.3490',
        }, follow_redirects=False)
        assert rv.status_code == 302

    def test_edit_restaurant_post_with_coords_merchant(self, merchant_web_client):
        rv = merchant_web_client.post('/restaurant/1/edit', data={
            'name': '商家自改名称',
            'address': '深圳市南山区新地址',
            'delivery_fee': '6',
            'min_order': '25',
            'latitude': '22.6800',
            'longitude': '114.3400',
        }, follow_redirects=False)
        # 商家编辑后提交申请，重定向到编辑页或列表
        assert rv.status_code == 302


class TestSetUserLocation:
    """第六步：用户切换位置（AJAX 接口）"""

    def test_set_location_logged_in(self, web_client):
        rv = web_client.post('/restaurant/set-location', json={
            'lat': 22.6899,
            'lng': 114.3490,
            'address': '深圳市南山区科技园',
        })
        assert rv.status_code == 200
        data = rv.get_json()
        assert data.get('success') is True

    def test_set_location_missing_coords(self, web_client):
        rv = web_client.post('/restaurant/set-location', json={
            'address': '只有地址没有坐标',
        })
        assert rv.status_code == 400

    def test_set_location_not_logged_in(self, client):
        rv = client.post('/restaurant/set-location', json={
            'lat': 22.6899,
            'lng': 114.3490,
            'address': '深圳市南山区',
        })
        # 未登录应 401 或重定向
        assert rv.status_code in (302, 401)


class TestDistanceFiltering:
    """第六步：有位置时的距离过滤与排序"""

    def test_list_sort_distance_with_location(self, app, web_client):
        """Session 中有坐标时按距离排序应返回 200"""
        with web_client.session_transaction() as sess:
            sess['user_lat'] = 22.6899
            sess['user_lng'] = 114.3490
            sess['user_address'] = '深圳市南山区'
        rv = web_client.get('/restaurant/?sort=distance')
        assert rv.status_code == 200

    def test_list_sort_distance_without_location_fallback(self, web_client):
        """无坐标时 sort=distance 应降级为按评分排序，返回 200"""
        rv = web_client.get('/restaurant/?sort=distance')
        assert rv.status_code == 200

    def test_list_with_location_shows_restaurants(self, app, web_client):
        """有位置时，列表内容正常渲染"""
        with app.app_context():
            from app.models import Restaurant
            from app import db
            r = Restaurant(
                name='附近餐厅',
                address='深圳市南山区测试路',
                latitude=22.6900,
                longitude=114.3491,
                description='附近餐厅描述',
            )
            db.session.add(r)
            db.session.commit()

        with web_client.session_transaction() as sess:
            sess['user_lat'] = 22.6899
            sess['user_lng'] = 114.3490
            sess['user_address'] = '深圳市南山区'
        rv = web_client.get('/restaurant/')
        assert rv.status_code == 200
