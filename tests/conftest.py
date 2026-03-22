"""
pytest 全局配置
- 通过环境变量在 create_app() 之前注入 SQLite 路径，彻底避免引擎缓存问题
- fakeredis 模拟 Redis，无需真实 Redis 连接
"""
import pytest
import fakeredis
from werkzeug.security import generate_password_hash
from flask_jwt_extended import create_access_token

from app import create_app, db
from app.models import User, Restaurant, Dish, Category, Address


# ──────────────────────────────────────────────
# App & DB Fixtures
# ──────────────────────────────────────────────

@pytest.fixture
def app(monkeypatch, tmp_path):
    """
    测试 App 创建策略：
    1. 通过 monkeypatch.setenv 在 create_app() 之前注入所有配置
    2. create_app() 读取 DATABASE_URL → SQLite 文件，不会拿到生产 MySQL URI
    3. 每个测试拥有独立的 tmp_path SQLite 文件
    """
    db_file = str(tmp_path / 'test.db')

    # 必须在 create_app() 之前设置，保证引擎初始化时读到正确 URI
    monkeypatch.setenv('DATABASE_URL', f'sqlite:///{db_file}')
    monkeypatch.setenv('FLASK_ENV', 'development')   # 跳过生产环境连接池配置
    monkeypatch.setenv('SECRET_KEY', 'test-secret-key')
    monkeypatch.setenv('JWT_SECRET_KEY', 'test-jwt-secret')

    # fakeredis 替换购物车 Redis 调用
    fake_redis = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr('app.services.cart_service._get_redis', lambda: fake_redis)

    application = create_app()
    application.config.update({
        'TESTING': True,
        'CACHE_TYPE': 'SimpleCache',
        'WTF_CSRF_ENABLED': False,
        'RATELIMIT_ENABLED': False,   # 测试环境完全禁用限流
    })

    with application.app_context():
        db.create_all()
        _seed()

        # 测试环境关闭 Celery（无 Redis Broker 可连），避免连接超时拖慢测试
        import app.api.orders as _orders_mod
        import app.routes.order as _order_route_mod
        monkeypatch.setattr(_orders_mod, '_CELERY_ENABLED', False)
        monkeypatch.setattr(_order_route_mod, '_CELERY_ENABLED', False)

        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


# ──────────────────────────────────────────────
# 种子数据（在 app_context 内直接调用，无需嵌套）
# ──────────────────────────────────────────────

def _seed():
    admin = User(username='admin',
                 password=generate_password_hash('admin123'),
                 role='admin', email='admin@test.com', phone='13800138000')
    user1 = User(username='testuser',
                 password=generate_password_hash('Test123456'),
                 role='user', phone='13900139000')
    user2 = User(username='otheruser',
                 password=generate_password_hash('Test123456'),
                 role='user', phone='13911139000')
    db.session.add_all([admin, user1, user2])
    db.session.flush()

    restaurant = Restaurant(name='测试餐厅', address='北京市测试路1号',
                            phone='010-12345678', status='open',
                            delivery_fee=5.0, min_order=20.0, rating=4.5)
    db.session.add(restaurant)
    db.session.flush()

    category = Category(name='热菜', sort_order=1)
    db.session.add(category)
    db.session.flush()

    dish = Dish(name='红烧肉', price=25.5, restaurant_id=restaurant.id,
                category_id=category.id, available=True, sales_count=100)
    dish_unavailable = Dish(name='已下架菜品', price=10.0,
                            restaurant_id=restaurant.id, available=False)
    db.session.add_all([dish, dish_unavailable])

    address = Address(user_id=user1.id, name='测试收件人',
                      phone='13900139000', address='北京市测试收货地址',
                      is_default=True)
    db.session.add(address)
    db.session.commit()


# ──────────────────────────────────────────────
# JWT Token Fixtures
# ──────────────────────────────────────────────

@pytest.fixture
def admin_token(app):
    with app.app_context():
        user = User.query.filter_by(username='admin').first()
        return create_access_token(identity=str(user.id))


@pytest.fixture
def user_token(app):
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        return create_access_token(identity=str(user.id))


@pytest.fixture
def other_token(app):
    with app.app_context():
        user = User.query.filter_by(username='otheruser').first()
        return create_access_token(identity=str(user.id))


# ──────────────────────────────────────────────
# 辅助函数
# ──────────────────────────────────────────────

def auth_header(token):
    return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
