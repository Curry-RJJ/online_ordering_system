"""
数据库迁移脚本
用于更新数据库结构，添加新字段
"""

from app import create_app, db
from app.models import Dish
from sqlalchemy import text

def migrate_database():
    """执行数据库迁移"""
    app = create_app()
    
    with app.app_context():
        # 检查并添加新字段
        try:
            # 检查 discount_rate 字段是否存在
            result = db.session.execute(text("PRAGMA table_info(dish)"))
            columns = [row[1] for row in result]
            
            if 'discount_rate' not in columns:
                print("添加 discount_rate 字段...")
                db.session.execute(text("ALTER TABLE dish ADD COLUMN discount_rate FLOAT"))
                db.session.commit()
                print("✓ discount_rate 字段添加成功")
            
            if 'ingredients' not in columns:
                print("添加 ingredients 字段...")
                db.session.execute(text("ALTER TABLE dish ADD COLUMN ingredients VARCHAR(200)"))
                db.session.commit()
                print("✓ ingredients 字段添加成功")
            
            # === 餐厅（restaurant）表字段检查 ===
            result = db.session.execute(text("PRAGMA table_info(restaurant)"))
            r_columns = [row[1] for row in result]

            if 'cuisine_type' not in r_columns:
                print("添加 restaurant.cuisine_type 字段...")
                db.session.execute(text("ALTER TABLE restaurant ADD COLUMN cuisine_type VARCHAR(50)"))
                db.session.commit()
                print("✓ restaurant.cuisine_type 字段添加成功")

            if 'business_hours' not in r_columns:
                print("添加 restaurant.business_hours 字段...")
                db.session.execute(text("ALTER TABLE restaurant ADD COLUMN business_hours VARCHAR(100)"))
                db.session.commit()
                print("✓ restaurant.business_hours 字段添加成功")

            if 'delivery_fee' not in r_columns:
                print("添加 restaurant.delivery_fee 字段...")
                db.session.execute(text("ALTER TABLE restaurant ADD COLUMN delivery_fee FLOAT DEFAULT 0"))
                db.session.commit()
                print("✓ restaurant.delivery_fee 字段添加成功")

            if 'min_order' not in r_columns:
                print("添加 restaurant.min_order 字段...")
                db.session.execute(text("ALTER TABLE restaurant ADD COLUMN min_order FLOAT DEFAULT 0"))
                db.session.commit()
                print("✓ restaurant.min_order 字段添加成功")

            print("\n数据库迁移完成！")
            
        except Exception as e:
            print(f"迁移过程中出现错误: {e}")
            db.session.rollback()

if __name__ == '__main__':
    migrate_database() 