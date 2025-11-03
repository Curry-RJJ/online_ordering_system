from flask import Flask, render_template_string, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # 直接配置基本设置
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key-please-change-in-production'
    
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
