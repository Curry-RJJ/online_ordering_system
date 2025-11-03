from app import db
from flask_login import UserMixin
from datetime import datetime
from app import login_manager  # 确保这个导入在上面

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(512), nullable=False) 
    role = db.Column(db.String(10), default='user')  # user/admin/merchant
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    avatar = db.Column(db.String(200), default='/static/images/default_avatar.png')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 用户地址
    addresses = db.relationship('Address', backref='user', lazy='dynamic')
    # 用户订单
    orders = db.relationship('Order', backref='user', lazy='dynamic')
    # 用户评价
    reviews = db.relationship('Review', backref='user', lazy='dynamic')
    # 购物车
    cart_items = db.relationship('CartItem', backref='user', lazy='dynamic')

class Address(db.Model):
    """用户地址"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)  # 收货人姓名
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)  # 详细地址
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Restaurant(db.Model):
    """餐厅/店铺"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    logo = db.Column(db.String(200))
    banner = db.Column(db.String(200))
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    cuisine_type = db.Column(db.String(50))  # 菜系类型（中餐、西餐、日料等）
    business_hours = db.Column(db.String(100))  # 营业时间
    delivery_fee = db.Column(db.Float, default=0)  # 配送费
    min_order = db.Column(db.Float, default=0)  # 起送价
    rating = db.Column(db.Float, default=5.0)  # 评分
    review_count = db.Column(db.Integer, default=0)  # 评价数量
    status = db.Column(db.String(20), default='open')  # open/closed/busy
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 餐厅菜品
    dishes = db.relationship('Dish', backref='restaurant', lazy='dynamic')
    # 餐厅订单
    orders = db.relationship('Order', backref='restaurant', lazy='dynamic')
    # 餐厅评价
    reviews = db.relationship('Review', backref='restaurant', lazy='dynamic')

class RestaurantCategory(db.Model):
    """餐厅分类"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    icon = db.Column(db.String(200))
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Category(db.Model):
    """菜品分类"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    icon = db.Column(db.String(200))
    sort_order = db.Column(db.Integer, default=0)
    
    # 分类下的菜品
    dishes = db.relationship('Dish', backref='category', lazy='dynamic')

class Dish(db.Model):
    """菜品"""
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    original_price = db.Column(db.Float)  # 原价（用于显示折扣）
    discount_rate = db.Column(db.Float)  # 折扣率
    image = db.Column(db.String(200))
    ingredients = db.Column(db.String(200))  # 主要食材
    sales_count = db.Column(db.Integer, default=0)  # 销量
    rating = db.Column(db.Float, default=5.0)  # 评分
    is_recommended = db.Column(db.Boolean, default=False)  # 是否推荐
    is_spicy = db.Column(db.Boolean, default=False)  # 是否辣
    available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 菜品订单项
    order_items = db.relationship('OrderItem', backref='dish', lazy='dynamic')
    # 购物车项
    cart_items = db.relationship('CartItem', backref='dish', lazy='dynamic')

class CartItem(db.Model):
    """购物车项"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    dish_id = db.Column(db.Integer, db.ForeignKey('dish.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    """订单"""
    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(32), unique=True, nullable=False)  # 订单号
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    
    # 收货信息
    delivery_name = db.Column(db.String(50), nullable=False)
    delivery_phone = db.Column(db.String(20), nullable=False)
    delivery_address = db.Column(db.String(200), nullable=False)
    
    # 价格信息
    subtotal = db.Column(db.Float, nullable=False)  # 小计
    delivery_fee = db.Column(db.Float, default=0)  # 配送费
    total_amount = db.Column(db.Float, nullable=False)  # 总金额
    
    # 订单状态
    status = db.Column(db.String(20), default='pending')  # pending/confirmed/preparing/delivering/completed/cancelled
    payment_status = db.Column(db.String(20), default='unpaid')  # unpaid/paid/refunded
    
    # 时间信息
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    
    # 备注
    remark = db.Column(db.Text)
    
    # 订单项
    order_items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')

class OrderItem(db.Model):
    """订单项"""
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    dish_id = db.Column(db.Integer, db.ForeignKey('dish.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)  # 下单时的价格
    subtotal = db.Column(db.Float, nullable=False)  # 小计

class Review(db.Model):
    """评价"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    
    rating = db.Column(db.Integer, nullable=False)  # 1-5星
    content = db.Column(db.Text)
    images = db.Column(db.Text)  # JSON格式存储图片URL
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AdminApplication(db.Model):
    """管理员申请"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='admin_applications')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
