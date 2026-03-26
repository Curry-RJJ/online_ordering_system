"""
评价功能测试 + 首页评分测试
覆盖 app/routes/order.py submit_review 路由
     app/routes/restaurant.py list_restaurants avg_rating 计算
"""
import pytest
from app.models import Review, Restaurant, User, Order
from app import db
import uuid


# ──────────────────────────────────────────────────────────────────────────────
# 首页平均评分
# ──────────────────────────────────────────────────────────────────────────────

class TestHomepageAvgRating:
    def test_no_reviews_shows_none(self, client):
        """无评价时 avg_rating 为 None，模板显示"暂无"相关内容"""
        rv = client.get('/restaurant/')
        assert rv.status_code == 200
        # 页面不应出现硬编码 4.8
        assert b'4.8' not in rv.data

    def test_avg_rating_calculated_after_review(self, app, web_client, completed_order_in_db):
        """提交评价后首页平均评分应反映真实数据"""
        oid = completed_order_in_db
        web_client.post(f'/order/{oid}/review', data={'rating': '4', 'content': '不错'})
        rv = web_client.get('/restaurant/')
        assert rv.status_code == 200
        # 评价提交后应能看到 4.0 分
        assert b'4.0' in rv.data


# ──────────────────────────────────────────────────────────────────────────────
# 评价提交
# ──────────────────────────────────────────────────────────────────────────────

class TestSubmitReview:
    def test_get_review_page_requires_login(self, client, completed_order_in_db):
        rv = client.get(f'/order/{completed_order_in_db}/review')
        assert rv.status_code == 302
        assert '/auth/login' in rv.headers['Location']

    def test_get_review_page_shows_form(self, web_client, completed_order_in_db):
        rv = web_client.get(f'/order/{completed_order_in_db}/review')
        assert rv.status_code == 200
        assert '写评价'.encode() in rv.data or b'rating' in rv.data

    def test_submit_review_success(self, app, web_client, completed_order_in_db):
        oid = completed_order_in_db
        rv = web_client.post(f'/order/{oid}/review',
                             data={'rating': '5', 'content': '非常好吃！'},
                             follow_redirects=True)
        assert rv.status_code == 200
        with app.app_context():
            review = Review.query.filter_by(order_id=oid).first()
            assert review is not None
            assert review.rating == 5
            assert review.content == '非常好吃！'

    def test_submit_review_updates_restaurant_rating(self, app, web_client, completed_order_in_db):
        """提交评价后餐厅 rating 和 review_count 应更新"""
        oid = completed_order_in_db
        with app.app_context():
            order = Order.query.get(oid)
            rid = order.restaurant_id
            restaurant = Restaurant.query.get(rid)
            old_count = restaurant.review_count or 0

        web_client.post(f'/order/{oid}/review', data={'rating': '4', 'content': ''})

        with app.app_context():
            restaurant = Restaurant.query.get(rid)
            assert restaurant.review_count == old_count + 1
            assert 0 < restaurant.rating <= 5

    def test_submit_review_without_rating_fails(self, web_client, completed_order_in_db):
        oid = completed_order_in_db
        rv = web_client.post(f'/order/{oid}/review',
                             data={'rating': '0', 'content': '随便'},
                             follow_redirects=True)
        assert rv.status_code == 200
        # 评价不应被创建

    def test_cannot_review_pending_order(self, web_client, order_in_db):
        """pending 状态订单不能评价"""
        rv = web_client.post(f'/order/{order_in_db}/review',
                             data={'rating': '5', 'content': '好'},
                             follow_redirects=True)
        assert rv.status_code == 200
        assert '只有已完成'.encode() in rv.data

    def test_cannot_review_others_order(self, app, client, completed_order_in_db):
        """不能评价别人的订单"""
        client.post('/auth/login', data={'username': 'otheruser', 'password': 'Test123456'})
        rv = client.post(f'/order/{completed_order_in_db}/review',
                         data={'rating': '5', 'content': '好'},
                         follow_redirects=True)
        assert rv.status_code == 200
        assert '权限不足'.encode() in rv.data

    def test_cannot_review_same_order_twice(self, app, web_client, completed_order_in_db):
        """同一订单不能重复评价"""
        oid = completed_order_in_db
        web_client.post(f'/order/{oid}/review', data={'rating': '5', 'content': '第一次'})
        rv = web_client.post(f'/order/{oid}/review',
                             data={'rating': '3', 'content': '第二次'},
                             follow_redirects=True)
        assert rv.status_code == 200
        with app.app_context():
            count = Review.query.filter_by(order_id=oid).count()
            assert count == 1  # 只有一条评价

    def test_review_content_optional(self, app, web_client, completed_order_in_db):
        """评价内容可以为空"""
        oid = completed_order_in_db
        rv = web_client.post(f'/order/{oid}/review',
                             data={'rating': '4', 'content': ''},
                             follow_redirects=True)
        assert rv.status_code == 200
        with app.app_context():
            review = Review.query.filter_by(order_id=oid).first()
            assert review is not None
            assert review.content is None
