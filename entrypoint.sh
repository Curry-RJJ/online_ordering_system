#!/bin/bash

# 如果传入了自定义命令（如 pytest），跳过 MySQL 等待和 DB 初始化，直接执行
if [ "$#" -gt 0 ]; then
    exec "$@"
fi

# 等待MySQL完全启动
echo "等待MySQL数据库启动..."
while ! nc -z mysql 3306 2>/dev/null; do
  echo "等待中..."
  sleep 2
done
echo "MySQL已启动！"

# 等待额外几秒确保MySQL完全就绪
sleep 5

# 初始化数据库
echo "初始化数据库..."
python << 'END'
from app import create_app, db
from app.models import User
from app.bootstrap_admin import get_initial_admin_credentials
from werkzeug.security import generate_password_hash
import os

app = create_app()
with app.app_context():
    db.create_all()
    print("数据库表创建成功！")

    if User.query.count() == 0:
        print("开始初始化数据...")
        try:
            cred = get_initial_admin_credentials()
            admin = User(
                username=cred['username'],
                password=generate_password_hash(cred['password']),
                role='admin',
                phone=cred['phone'],
                email=cred['email'],
                location_confirmed=True,
            )
            db.session.add(admin)

            flask_env = os.environ.get('FLASK_ENV', 'production')
            seed_demo = (
                os.environ.get('SEED_DEMO_USERS', '').lower() in ('1', 'true', 'yes')
                or flask_env == 'development'
            )
            if seed_demo:
                test_user = User(
                    username='testuser',
                    password=generate_password_hash('Test123456'),
                    role='user',
                    phone='13900139000',
                    email='test@user.com',
                    location_confirmed=True,
                )
                db.session.add(test_user)

            db.session.commit()
            print("数据初始化成功！")
            print("管理员用户名: %s" % cred['username'])
            if os.environ.get('INITIAL_ADMIN_PASSWORD', '').strip():
                print("管理员密码: 已使用环境变量 INITIAL_ADMIN_PASSWORD（请勿在日志中泄露）。")
            elif flask_env == 'development':
                print("管理员密码: 开发环境未设置 INITIAL_ADMIN_PASSWORD，已使用默认 BrandNew123（请尽快登录并修改）。")
            if seed_demo:
                print("已创建演示用户 testuser / Test123456。")
        except Exception as e:
            print(f"初始化数据时出错: {e}")
            import traceback
            traceback.print_exc()
            raise
    else:
        print("数据库已有数据，跳过初始化。")
END

# 启动应用
echo "启动Flask应用..."
if [ "$FLASK_ENV" = "development" ]; then
    echo "以开发模式启动..."
    python run.py
else
    echo "以生产模式启动（使用Gunicorn）..."
    # 2C2G：workers 过多易导致内存争用；以 2 workers × 4 threads 为基线，压测后再调（性能优化方案 P0）
    gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 4 --timeout 120 --access-logfile logs/access.log --error-logfile logs/error.log run:app
fi

