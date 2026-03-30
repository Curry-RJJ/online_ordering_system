from flask import Flask, render_template_string, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_caching import Cache
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from datetime import timedelta
import os

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
cache = Cache()
jwt = JWTManager()
csrf = CSRFProtect()
# Limiter 单例：装饰器在各模块直接 import 使用
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=['200 per minute'],   # 全局兜底：每 IP 每分钟 200 次
    storage_uri=os.environ.get('REDIS_URL', 'memory://'),
)

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # 开发模式下自动重载模板；生产环境由 FLASK_ENV 决定
    is_dev = os.environ.get('FLASK_ENV', 'production') == 'development'
    app.config['TEMPLATES_AUTO_RELOAD'] = is_dev
    app.jinja_env.auto_reload = is_dev
    # 生产环境开启静态资源浏览器缓存（1小时），开发环境关闭
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0 if is_dev else 3600
    
    # 直接配置基本设置
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key-please-change-in-production'
    app.config['WTF_CSRF_TIME_LIMIT'] = None  # 不限制 CSRF token 过期时间

    # JWT 配置
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY') or app.config['SECRET_KEY']
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

    # Redis 缓存配置：有 REDIS_URL 则用 Redis，否则回退到简单内存缓存（方便本地开发）
    redis_url = os.environ.get('REDIS_URL')
    if redis_url:
        app.config['CACHE_TYPE'] = 'RedisCache'
        app.config['CACHE_REDIS_URL'] = redis_url
        app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 默认缓存 5 分钟
    else:
        app.config['CACHE_TYPE'] = 'SimpleCache'
        app.config['CACHE_DEFAULT_TIMEOUT'] = 300
    
    # 生产环境安全检查：强制要求设置 SECRET_KEY
    # 判断是否为生产环境：检查 FLASK_ENV 或 DATABASE_URL（使用 MySQL 即为生产环境）
    is_production = (os.environ.get('FLASK_ENV') == 'production' or 
                     os.environ.get('DATABASE_URL', '').startswith('mysql'))
    if is_production and not os.environ.get('SECRET_KEY'):
        raise RuntimeError("生产环境必须设置 SECRET_KEY 环境变量！")
    
    # 数据库配置
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{os.path.join(basedir, "..", "instance", "database.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 生产环境启用数据库连接池优化
    if not is_dev:
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_size': 20,
            'max_overflow': 10,
            'pool_recycle': 3600,
        }
    
    # 高德地图 API Key 配置
    app.config['AMAP_JS_KEY'] = os.environ.get('AMAP_JS_KEY', '')
    app.config['AMAP_JS_SECURITY_KEY'] = os.environ.get('AMAP_JS_SECURITY_KEY', '')
    app.config['AMAP_WEB_KEY'] = os.environ.get('AMAP_WEB_KEY', '')

    # 文件上传配置
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # 密码强度：zxcvbn 分数阈值 0～4，默认 2（可通过环境变量 PASSWORD_ZXCVBN_MIN_SCORE 覆盖）
    app.config['PASSWORD_ZXCVBN_MIN_SCORE'] = int(
        os.environ.get('PASSWORD_ZXCVBN_MIN_SCORE', '2')
    )
    
    # 确保上传目录存在
    os.makedirs(os.path.join(basedir, 'static', 'images', 'dishes'), exist_ok=True)
    os.makedirs(os.path.join(basedir, 'static', 'images', 'restaurants'), exist_ok=True)
    os.makedirs(os.path.join(basedir, 'static', 'images', 'logos'), exist_ok=True)
    os.makedirs(os.path.join(basedir, 'static', 'images', 'banners'), exist_ok=True)

    # 限流存储：通过 app.config 注入，让 limiter.init_app 读取正确的 storage
    redis_url = os.environ.get('REDIS_URL')
    app.config['RATELIMIT_STORAGE_URI'] = redis_url if redis_url else 'memory://'
    app.config['RATELIMIT_STRATEGY'] = 'fixed-window'

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    cache.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)

    # 统一限流超出响应格式（429）
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({
            'code': 429,
            'message': f'请求过于频繁，{e.description}',
            'data': None
        }), 429

    # 统一 JWT 错误响应格式
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_data):
        return jsonify({'code': 401, 'message': 'Token 已过期，请重新登录', 'data': None}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'code': 401, 'message': '无效的 Token', 'data': None}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'code': 401, 'message': '未提供 Token，请先登录', 'data': None}), 401

    # 注册蓝图
    from app.routes.auth import auth_bp
    from app.routes.dish import dish_bp
    from app.routes.order import order_bp
    from app.routes.restaurant import restaurant_bp
    from app.routes.cart import cart_bp
    from app.routes.restaurant_category import restaurant_category_bp
    from app.routes.category import category_bp
    from app.routes.location import location_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dish_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(restaurant_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(restaurant_category_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(location_bp)

    # 注册 RESTful API 蓝图（JWT 鉴权，排除 CSRF 检查）
    from app.api import api_bp
    csrf.exempt(api_bp)
    app.register_blueprint(api_bp)

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('restaurant.list_restaurants'))
        else:
            return redirect(url_for('auth.login'))

    @app.route('/health')
    def health_check():
        """健康检查接口：供 Nginx upstream 检测和运维监控脚本调用"""
        import time
        status = {'status': 'ok', 'timestamp': int(time.time())}
        try:
            # 检查数据库连通性
            db.session.execute(db.text('SELECT 1'))
            status['db'] = 'ok'
        except Exception as e:
            status['db'] = 'error'
            status['status'] = 'degraded'
            app.logger.error(f'Health check DB error: {e}')
        try:
            # 检查 Redis 连通性（通过 cache ping）
            cache.get('__health__')
            status['cache'] = 'ok'
        except Exception as e:
            status['cache'] = 'error'
            status['status'] = 'degraded'
            app.logger.error(f'Health check Cache error: {e}')
        http_code = 200 if status['status'] == 'ok' else 503
        return jsonify(status), http_code

    # 将高德 JS Key 注入所有 Jinja2 模板（Web 服务 Key 不暴露给前端）
    app.jinja_env.globals['amap_js_key'] = app.config['AMAP_JS_KEY']
    app.jinja_env.globals['amap_js_security_key'] = app.config['AMAP_JS_SECURITY_KEY']

    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app
