#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美团风格订餐系统 - 数据初始化脚本
添加农耕记、尊宝披萨等知名餐厅和真实菜品数据
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Restaurant, Category, Dish, Address
from werkzeug.security import generate_password_hash

def init_database():
    """初始化数据库和基础数据"""
    import os
    # 本地执行 init_data 时默认按开发处理；生产请设置 FLASK_ENV 与 INITIAL_ADMIN_PASSWORD
    os.environ.setdefault('FLASK_ENV', 'development')

    from app.bootstrap_admin import get_initial_admin_credentials

    app = create_app()

    with app.app_context():
        # 删除所有表并重新创建
        db.drop_all()
        db.create_all()

        print("🗄️ 数据库表创建完成")

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
        print("👤 用户创建完成")
        
        # 创建用户地址
        address1 = Address(
            user_id=test_user.id,
            name='张三',
            phone='13900139000',
            address='北京市朝阳区三里屯SOHO 1号楼1001室',
            is_default=True
        )
        
        address2 = Address(
            user_id=test_user.id,
            name='李四',
            phone='13800138001',
            address='北京市海淀区中关村大街1号',
            is_default=False
        )
        
        db.session.add_all([address1, address2])
        db.session.commit()
        print("📍 用户地址创建完成")
        
        # 创建菜品分类 - 使用直观的Emoji图标
        categories_data = [
            {'name': '热菜', 'icon': None, 'sort_order': 1},  # 🍲
            {'name': '凉菜', 'icon': None, 'sort_order': 2},  # 🥗
            {'name': '主食', 'icon': None, 'sort_order': 3},  # 🍚
            {'name': '汤品', 'icon': None, 'sort_order': 4},  # 🍜
            {'name': '饮品', 'icon': None, 'sort_order': 5},  # 🥤
            {'name': '甜品', 'icon': None, 'sort_order': 6},  # 🍰
            {'name': '披萨', 'icon': None, 'sort_order': 7},  # 🍕
            {'name': '意面', 'icon': None, 'sort_order': 8},  # 🍝
            {'name': '小食', 'icon': None, 'sort_order': 9},  # 🍟
        ]
        
        categories = {}
        for cat_data in categories_data:
            category = Category(**cat_data)
            db.session.add(category)
            categories[cat_data['name']] = category
        
        db.session.commit()
        print("📂 菜品分类创建完成")
        
        # 创建餐厅数据
        restaurants_data = [
            {
                'name': '农耕记（三里屯店）',
                'description': '精选优质食材，传承经典湘菜，让您品味地道湖南风情',
                'logo': '/static/images/restaurants/nonggengji_logo.jpg',
                'banner': '/static/images/restaurants/nonggengji_banner.jpg',
                'address': '北京市朝阳区三里屯路19号三里屯太古里南区',
                'phone': '010-64161234',
                'business_hours': '10:30-22:00',
                'delivery_fee': 6.0,
                'min_order': 20.0,
                'rating': 4.6,
                'review_count': 2847,
                'status': 'open'
            },
            {
                'name': '尊宝披萨（国贸店）',
                'description': '意式手工披萨，新鲜食材现做现烤，给您正宗意大利风味',
                'logo': '/static/images/restaurants/zunbao_logo.jpg',
                'banner': '/static/images/restaurants/zunbao_banner.jpg',
                'address': '北京市朝阳区建国门外大街1号国贸商城',
                'phone': '010-65051234',
                'business_hours': '11:00-23:00',
                'delivery_fee': 8.0,
                'min_order': 35.0,
                'rating': 4.5,
                'review_count': 1923,
                'status': 'open'
            },
            {
                'name': '海底捞火锅（王府井店）',
                'description': '优质服务，新鲜食材，让您享受极致火锅体验',
                'logo': '/static/images/restaurants/haidilao_logo.jpg',
                'banner': '/static/images/restaurants/haidilao_banner.jpg',
                'address': '北京市东城区王府井大街138号',
                'phone': '010-65121234',
                'business_hours': '10:00-02:00',
                'delivery_fee': 0.0,
                'min_order': 50.0,
                'rating': 4.8,
                'review_count': 5632,
                'status': 'open'
            },
            {
                'name': '麦当劳（中关村店）',
                'description': '经典美式快餐，24小时为您服务',
                'logo': '/static/images/restaurants/mcdonalds_logo.jpg',
                'banner': '/static/images/restaurants/mcdonalds_banner.jpg',
                'address': '北京市海淀区中关村大街27号',
                'phone': '010-62551234',
                'business_hours': '24小时营业',
                'delivery_fee': 9.0,
                'min_order': 15.0,
                'rating': 4.2,
                'review_count': 8934,
                'status': 'open'
            },
            {
                'name': '星巴克咖啡（三里屯店）',
                'description': '精品咖啡，舒适环境，您的第三空间',
                'logo': '/static/images/restaurants/starbucks_logo.jpg',
                'banner': '/static/images/restaurants/starbucks_banner.jpg',
                'address': '北京市朝阳区三里屯路11号',
                'phone': '010-64161235',
                'business_hours': '06:30-22:30',
                'delivery_fee': 6.0,
                'min_order': 25.0,
                'rating': 4.4,
                'review_count': 3421,
                'status': 'open'
            },
            {
                'name': '肯德基（西单店）',
                'description': '美味炸鸡，经典快餐，全家人的选择',
                'logo': '/static/images/restaurants/kfc_logo.jpg',
                'banner': '/static/images/restaurants/kfc_banner.jpg',
                'address': '北京市西城区西单北大街133号',
                'phone': '010-66661234',
                'business_hours': '06:00-24:00',
                'delivery_fee': 9.0,
                'min_order': 20.0,
                'rating': 4.3,
                'review_count': 7234,
                'status': 'open'
            },
            {
                'name': '必胜客（望京店）',
                'description': '意式休闲餐厅，披萨意面，欢聚时光',
                'logo': '/static/images/restaurants/pizzahut_logo.jpg',
                'banner': '/static/images/restaurants/pizzahut_banner.jpg',
                'address': '北京市朝阳区望京街10号望京SOHO',
                'phone': '010-64781234',
                'business_hours': '10:00-22:00',
                'delivery_fee': 12.0,
                'min_order': 40.0,
                'rating': 4.4,
                'review_count': 2156,
                'status': 'open'
            },
            {
                'name': '西贝莜面村（大悦城店）',
                'description': '西北风味，手工莜面，传统美食',
                'logo': '/static/images/restaurants/xibei_logo.jpg',
                'banner': '/static/images/restaurants/xibei_banner.jpg',
                'address': '北京市朝阳区朝阳北路101号朝阳大悦城',
                'phone': '010-85951234',
                'business_hours': '10:00-22:00',
                'delivery_fee': 8.0,
                'min_order': 30.0,
                'rating': 4.7,
                'review_count': 3892,
                'status': 'open'
            },
            {
                'name': '外婆家（金融街店）',
                'description': '杭帮菜系，家常美味，温馨如家',
                'logo': '/static/images/restaurants/waipojia_logo.jpg',
                'banner': '/static/images/restaurants/waipojia_banner.jpg',
                'address': '北京市西城区金融大街35号国际企业大厦',
                'phone': '010-66221234',
                'business_hours': '11:00-21:30',
                'delivery_fee': 6.0,
                'min_order': 25.0,
                'rating': 4.5,
                'review_count': 2743,
                'status': 'open'
            },
            {
                'name': '喜茶（三里屯店）',
                'description': '新式茶饮，创意无限，年轻人的选择',
                'logo': '/static/images/restaurants/heytea_logo.jpg',
                'banner': '/static/images/restaurants/heytea_banner.jpg',
                'address': '北京市朝阳区三里屯路12号',
                'phone': '010-64162345',
                'business_hours': '09:00-22:00',
                'delivery_fee': 6.0,
                'min_order': 15.0,
                'rating': 4.6,
                'review_count': 4521,
                'status': 'open'
            },
            {
                'name': '沙县小吃（中关村店）',
                'description': '福建风味，经济实惠，快捷美味',
                'logo': '/static/images/restaurants/shaxian_logo.jpg',
                'banner': '/static/images/restaurants/shaxian_banner.jpg',
                'address': '北京市海淀区中关村大街32号',
                'phone': '010-62553456',
                'business_hours': '06:00-22:00',
                'delivery_fee': 3.0,
                'min_order': 10.0,
                'rating': 4.1,
                'review_count': 1876,
                'status': 'open'
            },
            {
                'name': '黄焖鸡米饭（学院路店）',
                'description': '经典黄焖鸡，营养搭配，一人一锅',
                'logo': '/static/images/restaurants/huangmenji_logo.jpg',
                'banner': '/static/images/restaurants/huangmenji_banner.jpg',
                'address': '北京市海淀区学院路37号',
                'phone': '010-82314567',
                'business_hours': '10:00-21:00',
                'delivery_fee': 4.0,
                'min_order': 15.0,
                'rating': 4.2,
                'review_count': 1234,
                'status': 'open'
            }
        ]
        
        restaurants = {}
        for rest_data in restaurants_data:
            restaurant = Restaurant(**rest_data)
            db.session.add(restaurant)
            restaurants[rest_data['name']] = restaurant
        
        db.session.commit()
        print("🏪 餐厅创建完成")
        
        # 农耕记菜品数据
        nonggengji_dishes = [
            # 热菜
            {'name': '农耕记招牌口水鸡', 'category': '热菜', 'price': 48.0, 'original_price': 58.0, 'description': '选用优质土鸡，配以秘制调料，麻辣鲜香', 'image': '/static/images/dishes/koushuiji.jpg', 'sales_count': 1234, 'rating': 4.7, 'is_recommended': True, 'is_spicy': True},
            {'name': '毛血旺', 'category': '热菜', 'price': 42.0, 'description': '经典川菜，麻辣鲜香，配菜丰富', 'image': '/static/images/dishes/maoxuewang.jpg', 'sales_count': 892, 'rating': 4.6, 'is_spicy': True},
            {'name': '红烧肉', 'category': '热菜', 'price': 38.0, 'description': '肥而不腻，入口即化的经典红烧肉', 'image': '/static/images/dishes/hongshaorou.jpg', 'sales_count': 756, 'rating': 4.5},
            {'name': '宫保鸡丁', 'category': '热菜', 'price': 32.0, 'description': '经典川菜，鸡肉嫩滑，花生香脆', 'image': '/static/images/dishes/gongbaojiding.jpg', 'sales_count': 634, 'rating': 4.4, 'is_spicy': True},
            {'name': '麻婆豆腐', 'category': '热菜', 'price': 28.0, 'description': '嫩滑豆腐配以麻辣调料，下饭神器', 'image': '/static/images/dishes/mapodoufu.jpg', 'sales_count': 523, 'rating': 4.3, 'is_spicy': True},
            {'name': '糖醋里脊', 'category': '热菜', 'price': 35.0, 'description': '酸甜可口，外酥内嫩', 'image': '/static/images/dishes/tangculiji.jpg', 'sales_count': 445, 'rating': 4.2},
            
            # 凉菜
            {'name': '夫妻肺片', 'category': '凉菜', 'price': 26.0, 'description': '经典川菜凉菜，麻辣鲜香', 'image': '/static/images/dishes/fuqifeipian.jpg', 'sales_count': 387, 'rating': 4.5, 'is_spicy': True},
            {'name': '蒜泥白肉', 'category': '凉菜', 'price': 24.0, 'description': '肉片薄如纸，蒜香浓郁', 'image': '/static/images/dishes/suannibarou.jpg', 'sales_count': 298, 'rating': 4.3},
            {'name': '凉拌黄瓜', 'category': '凉菜', 'price': 16.0, 'description': '清爽解腻，开胃小菜', 'image': '/static/images/dishes/liangbanhuanggua.jpg', 'sales_count': 567, 'rating': 4.1},
            
            # 主食
            {'name': '农耕记炒饭', 'category': '主食', 'price': 22.0, 'description': '粒粒分明，配菜丰富的招牌炒饭', 'image': '/static/images/dishes/chaofan.jpg', 'sales_count': 789, 'rating': 4.4, 'is_recommended': True},
            {'name': '手工面条', 'category': '主食', 'price': 18.0, 'description': '现擀现煮，劲道爽滑', 'image': '/static/images/dishes/miantiao.jpg', 'sales_count': 456, 'rating': 4.2},
            {'name': '白米饭', 'category': '主食', 'price': 3.0, 'description': '优质大米，香甜可口', 'image': '/static/images/dishes/baimifan.jpg', 'sales_count': 1234, 'rating': 4.0},
            
            # 汤品
            {'name': '酸辣汤', 'category': '汤品', 'price': 15.0, 'description': '酸辣开胃，暖胃佳品', 'image': '/static/images/dishes/suanlatang.jpg', 'sales_count': 345, 'rating': 4.3, 'is_spicy': True},
            {'name': '紫菜蛋花汤', 'category': '汤品', 'price': 12.0, 'description': '清淡营养，老少皆宜', 'image': '/static/images/dishes/zicaidanhuatang.jpg', 'sales_count': 234, 'rating': 4.1},
            
            # 饮品
            {'name': '鲜榨橙汁', 'category': '饮品', 'price': 18.0, 'description': '新鲜橙子现榨，维C丰富', 'image': '/static/images/dishes/xianzhachangzhi.jpg', 'sales_count': 123, 'rating': 4.2},
            {'name': '柠檬蜂蜜茶', 'category': '饮品', 'price': 16.0, 'description': '清香柠檬配蜂蜜，酸甜解腻', 'image': '/static/images/dishes/ningmengfengmicha.jpg', 'sales_count': 89, 'rating': 4.0},
        ]
        
        # 尊宝披萨菜品数据
        zunbao_dishes = [
            # 披萨
            {'name': '玛格丽特披萨', 'category': '披萨', 'price': 68.0, 'description': '经典意式披萨，番茄酱、马苏里拉奶酪、新鲜罗勒', 'image': '/static/images/dishes/margherita.jpg', 'sales_count': 892, 'rating': 4.6, 'is_recommended': True},
            {'name': '至尊披萨', 'category': '披萨', 'price': 88.0, 'original_price': 98.0, 'description': '丰富配料：意式香肠、火腿、蘑菇、青椒、洋葱', 'image': '/static/images/dishes/supreme.jpg', 'sales_count': 756, 'rating': 4.7, 'is_recommended': True},
            {'name': '夏威夷披萨', 'category': '披萨', 'price': 72.0, 'description': '火腿配菠萝，酸甜口感的经典搭配', 'image': '/static/images/dishes/hawaiian.jpg', 'sales_count': 634, 'rating': 4.3},
            {'name': '意式香肠披萨', 'category': '披萨', 'price': 78.0, 'description': '正宗意式香肠，香味浓郁', 'image': '/static/images/dishes/pepperoni.jpg', 'sales_count': 523, 'rating': 4.5},
            {'name': '四季披萨', 'category': '披萨', 'price': 82.0, 'description': '四种口味一次享受：玛格丽特、火腿蘑菇、海鲜、蔬菜', 'image': '/static/images/dishes/quattro.jpg', 'sales_count': 445, 'rating': 4.4},
            {'name': '海鲜披萨', 'category': '披萨', 'price': 95.0, 'description': '新鲜虾仁、鱿鱼圈、蛤蜊肉，海鲜爱好者首选', 'image': '/static/images/dishes/seafood.jpg', 'sales_count': 387, 'rating': 4.6},
            
            # 意面
            {'name': '意式肉酱面', 'category': '意面', 'price': 45.0, 'description': '经典博洛尼亚肉酱，配手工意面', 'image': '/static/images/dishes/bolognese.jpg', 'sales_count': 567, 'rating': 4.4},
            {'name': '奶油培根面', 'category': '意面', 'price': 42.0, 'description': '浓郁奶油配香脆培根，口感丰富', 'image': '/static/images/dishes/carbonara.jpg', 'sales_count': 456, 'rating': 4.3},
            {'name': '海鲜意面', 'category': '意面', 'price': 58.0, 'description': '新鲜海鲜配意面，鲜美可口', 'image': '/static/images/dishes/seafood_pasta.jpg', 'sales_count': 298, 'rating': 4.5},
            {'name': '蒜香橄榄油面', 'category': '意面', 'price': 35.0, 'description': '简单而经典的意式做法，蒜香浓郁', 'image': '/static/images/dishes/aglio_olio.jpg', 'sales_count': 234, 'rating': 4.2},
            
            # 小食
            {'name': '蒜香面包', 'category': '小食', 'price': 18.0, 'description': '香脆面包配蒜蓉黄油，开胃小食', 'image': '/static/images/dishes/garlic_bread.jpg', 'sales_count': 789, 'rating': 4.1},
            {'name': '鸡翅', 'category': '小食', 'price': 28.0, 'description': '香烤鸡翅，外焦内嫩', 'image': '/static/images/dishes/chicken_wings.jpg', 'sales_count': 345, 'rating': 4.2},
            {'name': '薯条', 'category': '小食', 'price': 22.0, 'description': '金黄酥脆，经典配菜', 'image': '/static/images/dishes/french_fries.jpg', 'sales_count': 678, 'rating': 4.0},
            
            # 饮品
            {'name': '意式浓缩咖啡', 'category': '饮品', 'price': 25.0, 'description': '正宗意式浓缩，香浓醇厚', 'image': '/static/images/dishes/espresso.jpg', 'sales_count': 234, 'rating': 4.3},
            {'name': '卡布奇诺', 'category': '饮品', 'price': 32.0, 'description': '浓缩咖啡配奶泡，经典意式咖啡', 'image': '/static/images/dishes/cappuccino.jpg', 'sales_count': 189, 'rating': 4.4},
            {'name': '柠檬汽水', 'category': '饮品', 'price': 15.0, 'description': '清爽柠檬味，解腻佳品', 'image': '/static/images/dishes/lemonade.jpg', 'sales_count': 123, 'rating': 4.1},
        ]
        
        # 添加农耕记菜品
        nonggengji = restaurants['农耕记（三里屯店）']
        for dish_data in nonggengji_dishes:
            category = categories[dish_data['category']]
            dish = Dish(
                restaurant_id=nonggengji.id,
                category_id=category.id,
                name=dish_data['name'],
                description=dish_data['description'],
                price=dish_data['price'],
                original_price=dish_data.get('original_price'),
                image=dish_data['image'],
                sales_count=dish_data['sales_count'],
                rating=dish_data['rating'],
                is_recommended=dish_data.get('is_recommended', False),
                is_spicy=dish_data.get('is_spicy', False)
            )
            db.session.add(dish)
        
        # 添加尊宝披萨菜品
        zunbao = restaurants['尊宝披萨（国贸店）']
        for dish_data in zunbao_dishes:
            category = categories[dish_data['category']]
            dish = Dish(
                restaurant_id=zunbao.id,
                category_id=category.id,
                name=dish_data['name'],
                description=dish_data['description'],
                price=dish_data['price'],
                original_price=dish_data.get('original_price'),
                image=dish_data['image'],
                sales_count=dish_data['sales_count'],
                rating=dish_data['rating'],
                is_recommended=dish_data.get('is_recommended', False),
                is_spicy=dish_data.get('is_spicy', False)
            )
            db.session.add(dish)
        
        # 添加其他餐厅的一些基础菜品
        other_dishes = [
            # 海底捞
            {'restaurant': '海底捞火锅（王府井店）', 'name': '经典牛肉', 'category': '热菜', 'price': 48.0, 'description': '新鲜牛肉片，涮火锅必选', 'sales_count': 1567},
            {'restaurant': '海底捞火锅（王府井店）', 'name': '手工面条', 'category': '主食', 'price': 8.0, 'description': '现场拉制，劲道爽滑', 'sales_count': 892},
            {'restaurant': '海底捞火锅（王府井店）', 'name': '酸梅汤', 'category': '饮品', 'price': 12.0, 'description': '解腥去腻，开胃饮品', 'sales_count': 456},
            
            # 麦当劳
            {'restaurant': '麦当劳（中关村店）', 'name': '巨无霸', 'category': '热菜', 'price': 22.0, 'description': '经典汉堡，双层牛肉饼', 'sales_count': 2345, 'is_recommended': True},
            {'restaurant': '麦当劳（中关村店）', 'name': '薯条（大）', 'category': '小食', 'price': 12.0, 'description': '金黄酥脆，经典配菜', 'sales_count': 1890},
            {'restaurant': '麦当劳（中关村店）', 'name': '可乐（中杯）', 'category': '饮品', 'price': 8.0, 'description': '冰爽可乐，经典搭配', 'sales_count': 1234},
            
            # 星巴克
            {'restaurant': '星巴克咖啡（三里屯店）', 'name': '美式咖啡', 'category': '饮品', 'price': 28.0, 'description': '经典美式，香醇浓郁', 'sales_count': 1567, 'is_recommended': True},
            {'restaurant': '星巴克咖啡（三里屯店）', 'name': '拿铁', 'category': '饮品', 'price': 35.0, 'description': '浓缩咖啡配蒸奶，口感顺滑', 'sales_count': 1234},
            {'restaurant': '星巴克咖啡（三里屯店）', 'name': '提拉米苏', 'category': '甜品', 'price': 32.0, 'description': '意式经典甜品，层次丰富', 'sales_count': 567},
        ]
        
        # 新增餐厅菜品数据
        new_restaurant_dishes = [
            # 肯德基
            {'restaurant': '肯德基（西单店）', 'name': '香辣鸡腿堡', 'category': '热菜', 'price': 18.0, 'description': '香辣鸡腿配新鲜蔬菜，口感丰富', 'sales_count': 1890, 'is_recommended': True, 'is_spicy': True},
            {'restaurant': '肯德基（西单店）', 'name': '上校鸡块', 'category': '热菜', 'price': 16.0, 'description': '酥脆鸡块，外酥内嫩', 'sales_count': 1456},
            {'restaurant': '肯德基（西单店）', 'name': '蛋挞', 'category': '甜品', 'price': 8.0, 'description': '港式蛋挞，奶香浓郁', 'sales_count': 789},
            {'restaurant': '肯德基（西单店）', 'name': '薯条', 'category': '小食', 'price': 10.0, 'description': '金黄薯条，香脆可口', 'sales_count': 2134},
            {'restaurant': '肯德基（西单店）', 'name': '百事可乐', 'category': '饮品', 'price': 8.0, 'description': '冰爽可乐，经典搭配', 'sales_count': 1567},
            
            # 必胜客
            {'restaurant': '必胜客（望京店）', 'name': '超级至尊披萨', 'category': '披萨', 'price': 89.0, 'description': '丰富配料，满足味蕾', 'sales_count': 1234, 'is_recommended': True},
            {'restaurant': '必胜客（望京店）', 'name': '意式肉丸面', 'category': '意面', 'price': 48.0, 'description': '手工肉丸配意面，浓郁番茄味', 'sales_count': 567},
            {'restaurant': '必胜客（望京店）', 'name': '芝士焗饭', 'category': '主食', 'price': 35.0, 'description': '香浓芝士配米饭，口感丰富', 'sales_count': 789},
            {'restaurant': '必胜客（望京店）', 'name': '提拉米苏', 'category': '甜品', 'price': 28.0, 'description': '经典意式甜品，层次丰富', 'sales_count': 345},
            {'restaurant': '必胜客（望京店）', 'name': '柠檬汽水', 'category': '饮品', 'price': 15.0, 'description': '清爽柠檬味，解腻佳品', 'sales_count': 456},
            
            # 西贝莜面村
            {'restaurant': '西贝莜面村（大悦城店）', 'name': '莜面栲栳栳', 'category': '主食', 'price': 32.0, 'description': '西北特色面食，营养丰富', 'sales_count': 1567, 'is_recommended': True},
            {'restaurant': '西贝莜面村（大悦城店）', 'name': '手抓羊肉', 'category': '热菜', 'price': 68.0, 'description': '新疆风味，肉质鲜美', 'sales_count': 892},
            {'restaurant': '西贝莜面村（大悦城店）', 'name': '大漠风沙鸡', 'category': '热菜', 'price': 58.0, 'description': '西北特色烤鸡，香味浓郁', 'sales_count': 634},
            {'restaurant': '西贝莜面村（大悦城店）', 'name': '酸奶', 'category': '饮品', 'price': 18.0, 'description': '浓稠酸奶，营养健康', 'sales_count': 789},
            {'restaurant': '西贝莜面村（大悦城店）', 'name': '胡萝卜汁', 'category': '饮品', 'price': 22.0, 'description': '新鲜胡萝卜榨汁，维生素丰富', 'sales_count': 345},
            
            # 外婆家
            {'restaurant': '外婆家（金融街店）', 'name': '西湖醋鱼', 'category': '热菜', 'price': 45.0, 'description': '杭州名菜，酸甜可口', 'sales_count': 1234, 'is_recommended': True},
            {'restaurant': '外婆家（金融街店）', 'name': '东坡肉', 'category': '热菜', 'price': 38.0, 'description': '肥而不腻，入口即化', 'sales_count': 892},
            {'restaurant': '外婆家（金融街店）', 'name': '龙井虾仁', 'category': '热菜', 'price': 52.0, 'description': '茶香虾仁，清香淡雅', 'sales_count': 567},
            {'restaurant': '外婆家（金融街店）', 'name': '白切鸡', 'category': '凉菜', 'price': 28.0, 'description': '嫩滑鸡肉，原汁原味', 'sales_count': 789},
            {'restaurant': '外婆家（金融街店）', 'name': '龙井茶', 'category': '饮品', 'price': 25.0, 'description': '正宗西湖龙井，清香回甘', 'sales_count': 456},
            
            # 喜茶
            {'restaurant': '喜茶（三里屯店）', 'name': '芝芝莓莓', 'category': '饮品', 'price': 28.0, 'description': '草莓配芝士奶盖，酸甜可口', 'sales_count': 2345, 'is_recommended': True},
            {'restaurant': '喜茶（三里屯店）', 'name': '多肉葡萄', 'category': '饮品', 'price': 25.0, 'description': '新鲜葡萄粒，果香浓郁', 'sales_count': 1890},
            {'restaurant': '喜茶（三里屯店）', 'name': '金凤茶王', 'category': '饮品', 'price': 22.0, 'description': '经典茶底，回味甘甜', 'sales_count': 1456},
            {'restaurant': '喜茶（三里屯店）', 'name': '芝士蛋糕', 'category': '甜品', 'price': 32.0, 'description': '浓郁芝士，口感顺滑', 'sales_count': 567},
            {'restaurant': '喜茶（三里屯店）', 'name': '抹茶蛋糕', 'category': '甜品', 'price': 35.0, 'description': '日式抹茶，微苦回甘', 'sales_count': 345},
            
            # 沙县小吃
            {'restaurant': '沙县小吃（中关村店）', 'name': '沙县拌面', 'category': '主食', 'price': 8.0, 'description': '经典沙县拌面，香滑爽口', 'sales_count': 1567, 'is_recommended': True},
            {'restaurant': '沙县小吃（中关村店）', 'name': '蒸饺', 'category': '主食', 'price': 6.0, 'description': '皮薄馅大，鲜美可口', 'sales_count': 1234},
            {'restaurant': '沙县小吃（中关村店）', 'name': '馄饨', 'category': '汤品', 'price': 7.0, 'description': '清汤馄饨，温暖人心', 'sales_count': 892},
            {'restaurant': '沙县小吃（中关村店）', 'name': '炖罐', 'category': '汤品', 'price': 12.0, 'description': '营养炖汤，滋补养生', 'sales_count': 456},
            {'restaurant': '沙县小吃（中关村店）', 'name': '豆浆', 'category': '饮品', 'price': 3.0, 'description': '现磨豆浆，营养健康', 'sales_count': 789},
            
            # 黄焖鸡米饭
            {'restaurant': '黄焖鸡米饭（学院路店）', 'name': '黄焖鸡米饭', 'category': '主食', 'price': 18.0, 'description': '经典黄焖鸡配米饭，营养均衡', 'sales_count': 2345, 'is_recommended': True},
            {'restaurant': '黄焖鸡米饭（学院路店）', 'name': '黄焖排骨米饭', 'category': '主食', 'price': 22.0, 'description': '嫩滑排骨，香味浓郁', 'sales_count': 1234},
            {'restaurant': '黄焖鸡米饭（学院路店）', 'name': '黄焖牛肉米饭', 'category': '主食', 'price': 25.0, 'description': '优质牛肉，口感丰富', 'sales_count': 892},
            {'restaurant': '黄焖鸡米饭（学院路店）', 'name': '紫菜蛋花汤', 'category': '汤品', 'price': 6.0, 'description': '清淡营养，暖胃佳品', 'sales_count': 567},
            {'restaurant': '黄焖鸡米饭（学院路店）', 'name': '绿豆汤', 'category': '饮品', 'price': 5.0, 'description': '清热解毒，夏日必备', 'sales_count': 345},
        ]
        
        for dish_data in other_dishes:
            restaurant = restaurants[dish_data['restaurant']]
            category = categories[dish_data['category']]
            dish = Dish(
                restaurant_id=restaurant.id,
                category_id=category.id,
                name=dish_data['name'],
                description=dish_data['description'],
                price=dish_data['price'],
                original_price=dish_data.get('original_price'),
                image=dish_data.get('image', '/static/images/dishes/default.jpg'),
                sales_count=dish_data['sales_count'],
                rating=dish_data.get('rating', 4.0),
                is_recommended=dish_data.get('is_recommended', False),
                is_spicy=dish_data.get('is_spicy', False)
            )
            db.session.add(dish)
        
        # 添加新餐厅菜品
        for dish_data in new_restaurant_dishes:
            restaurant = restaurants[dish_data['restaurant']]
            category = categories[dish_data['category']]
            dish = Dish(
                restaurant_id=restaurant.id,
                category_id=category.id,
                name=dish_data['name'],
                description=dish_data['description'],
                price=dish_data['price'],
                original_price=dish_data.get('original_price'),
                image=dish_data.get('image', '/static/images/dishes/default.jpg'),
                sales_count=dish_data['sales_count'],
                rating=dish_data.get('rating', 4.0),
                is_recommended=dish_data.get('is_recommended', False),
                is_spicy=dish_data.get('is_spicy', False)
            )
            db.session.add(dish)
        
        db.session.commit()
        print("🍽️ 菜品数据创建完成")
        
        print("\n✨ 数据初始化完成！")
        print("\n📊 数据统计:")
        print(f"   用户数量: {User.query.count()}")
        print(f"   餐厅数量: {Restaurant.query.count()}")
        print(f"   分类数量: {Category.query.count()}")
        print(f"   菜品数量: {Dish.query.count()}")
        print(f"   地址数量: {Address.query.count()}")
        
        print("\n🔑 登录信息:")
        print("   管理员: %s（密码见环境变量 INITIAL_ADMIN_PASSWORD；开发未设置时为 BrandNew123）" % cred['username'])
        print("   测试用户: testuser / Test123456")
        
        print("\n🏪 餐厅列表:")
        for restaurant in Restaurant.query.all():
            dish_count = Dish.query.filter_by(restaurant_id=restaurant.id).count()
            print(f"   {restaurant.name}: {dish_count} 道菜品")

if __name__ == '__main__':
    print("=" * 60)
    print("🍽️  美团风格订餐系统 - 数据初始化")
    print("=" * 60)
    
    try:
        init_database()
        print("\n🎉 初始化成功！现在可以启动应用了。")
        print("运行命令: python run.py")
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {str(e)}")
        import traceback
        traceback.print_exc() 