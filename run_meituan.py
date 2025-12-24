#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美团风格订餐系统 - 启动脚本
支持SQLite和MySQL数据库
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

def create_app_with_config(use_mysql=False):
    """根据配置创建Flask应用"""
    app = Flask(__name__, 
                template_folder='app/templates',
                static_folder='app/static')
    
    if use_mysql:
        # 使用MySQL配置
        from config_mysql import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)
        print("🗄️ 使用MySQL数据库")
    else:
        # 使用SQLite配置
        from config import Config
        app.config.from_object(Config)
        print("🗄️ 使用SQLite数据库")
    
    # 初始化扩展
    from app import db, login_manager
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

    # 首页路由
    from flask_login import current_user
    from flask import redirect, url_for
    
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('restaurant.list_restaurants'))
        else:
            return redirect(url_for('auth.login'))

    # 用户加载器
    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app

def main():
    """主函数"""
    print("=" * 60)
    print("🍽️  美团风格订餐系统")
    print("=" * 60)
    
    # 检查是否需要初始化数据库
    if len(sys.argv) > 1 and sys.argv[1] == 'init':
        print("\n📋 选择数据库类型:")
        print("1. SQLite（推荐，无需额外配置）")
        print("2. MySQL（需要PHPStudy或其他MySQL服务）")
        
        choice = input("\n请选择 (1/2): ").strip()
        
        if choice == '2':
            print("\n🔧 初始化MySQL数据库...")
            try:
                from init_mysql_data import init_mysql_database
                if init_mysql_database():
                    print("\n✅ MySQL数据库初始化成功！")
                    print("现在可以运行: python run_meituan.py mysql")
                else:
                    print("\n❌ MySQL数据库初始化失败")
                    return
            except ImportError as e:
                print(f"❌ 导入失败: {e}")
                print("请确保已安装所有依赖: pip install -r requirements.txt")
                return
        else:
            print("\n🔧 初始化SQLite数据库...")
            try:
                from init_data import init_database
                init_database()
                print("\n✅ SQLite数据库初始化成功！")
                print("现在可以运行: python run_meituan.py")
            except Exception as e:
                print(f"❌ 初始化失败: {e}")
                return
        return
    
    # 启动应用
    use_mysql = len(sys.argv) > 1 and sys.argv[1] == 'mysql'
    
    try:
        app = create_app_with_config(use_mysql)
        
        print(f"\n🚀 启动美团外卖系统...")
        print(f"📱 访问地址: http://localhost:5000")
        print(f"👤 管理员账号: admin / admin123")
        print(f"👤 测试用户: testuser / 123456")
        print(f"\n按 Ctrl+C 停止服务器")
        print("=" * 60)
        
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        print("\n💡 可能的解决方案:")
        print("1. 检查数据库是否已初始化: python run_meituan.py init")
        print("2. 检查依赖是否已安装: pip install -r requirements.txt")
        if use_mysql:
            print("3. 检查MySQL服务是否启动（PHPStudy）")
            print("4. 检查数据库连接配置（config_mysql.py）")

if __name__ == '__main__':
    main() 