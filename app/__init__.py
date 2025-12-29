from flask import Flask, render_template_string, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # 禁用模板缓存（开发时使用）
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.jinja_env.auto_reload = True
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    
    # 直接配置基本设置
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key-please-change-in-production'
    
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
    
    # 文件上传配置
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # 确保上传目录存在
    os.makedirs(os.path.join(basedir, 'static', 'images', 'dishes'), exist_ok=True)
    os.makedirs(os.path.join(basedir, 'static', 'images', 'restaurants'), exist_ok=True)
    os.makedirs(os.path.join(basedir, 'static', 'images', 'logos'), exist_ok=True)
    os.makedirs(os.path.join(basedir, 'static', 'images', 'banners'), exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # 注册蓝图
    from app.routes.auth import auth_bp
    from app.routes.dish import dish_bp
    from app.routes.order import order_bp
    from app.routes.restaurant import restaurant_bp
    from app.routes.cart import cart_bp
    from app.routes.restaurant_category import restaurant_category_bp
    from app.routes.category import category_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dish_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(restaurant_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(restaurant_category_bp)
    app.register_blueprint(category_bp)

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('restaurant.list_restaurants'))
        else:
            return redirect(url_for('auth.login'))

    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app
