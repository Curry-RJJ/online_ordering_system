#!/bin/bash

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
python << END
from app import create_app, db
from app.models import User, Restaurant, Dish, Category, RestaurantCategory, Order, OrderItem
import os

app = create_app()
with app.app_context():
    # 创建所有表
    db.create_all()
    print("数据库表创建成功！")
    
    # 检查是否需要初始化数据
    if User.query.count() == 0:
        print("开始初始化测试数据...")
        try:
            # 导入并执行初始化脚本
            exec(open('init_mysql_data.py').read())
            print("测试数据初始化成功！")
        except Exception as e:
            print(f"初始化数据时出错（可忽略）: {e}")
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
    gunicorn --bind 0.0.0.0:5000 --workers 4 --threads 2 --timeout 120 --access-logfile logs/access.log --error-logfile logs/error.log run:app
fi

