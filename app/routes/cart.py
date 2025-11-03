from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import CartItem, Dish, Restaurant, Order, OrderItem, Address
from app import db
import uuid
from datetime import datetime

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')

@cart_bp.route('/add', methods=['POST'])
@login_required
def add_to_cart():
    """添加商品到购物车"""
    dish_id = request.json.get('dish_id')
    quantity = request.json.get('quantity', 1)
    
    if not dish_id:
        return jsonify({'success': False, 'message': '商品ID不能为空'})
    
    dish = Dish.query.get_or_404(dish_id)
    
    if not dish.available:
        return jsonify({'success': False, 'message': '商品已下架'})
    
    # 检查是否已在购物车中
    cart_item = CartItem.query.filter_by(
        user_id=current_user.id,
        dish_id=dish_id
    ).first()
    
    if cart_item:
        # 更新数量
        cart_item.quantity += quantity
    else:
        # 新增购物车项
        cart_item = CartItem(
            user_id=current_user.id,
            dish_id=dish_id,
            quantity=quantity
        )
        db.session.add(cart_item)
    
    db.session.commit()
    
    # 获取购物车总数量
    cart_count = CartItem.query.filter_by(user_id=current_user.id).count()
    
    return jsonify({
        'success': True,
        'message': '已添加到购物车',
        'cart_count': cart_count
    })

@cart_bp.route('/')
@login_required
def view_cart():
    """查看购物车"""
    try:
        # 获取购物车商品（按餐厅分组）
        cart_items = db.session.query(CartItem, Dish, Restaurant).join(
            Dish, CartItem.dish_id == Dish.id
        ).join(
            Restaurant, Dish.restaurant_id == Restaurant.id
        ).filter(
            CartItem.user_id == current_user.id
        ).all()
    except Exception as e:
        print(f"Error fetching cart items: {e}")
        cart_items = []
    
    # 按餐厅分组
    restaurants_cart = {}
    total_amount = 0
    
    for cart_item, dish, restaurant in cart_items:
        if restaurant.id not in restaurants_cart:
            restaurants_cart[restaurant.id] = {
                'restaurant': restaurant,
                'items': [],
                'subtotal': 0
            }
        
        item_total = dish.price * cart_item.quantity
        restaurants_cart[restaurant.id]['items'].append({
            'cart_item': cart_item,
            'dish': dish,
            'total': item_total
        })
        restaurants_cart[restaurant.id]['subtotal'] += item_total
        total_amount += item_total
    
    # 获取用户地址
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    default_address = Address.query.filter_by(
        user_id=current_user.id,
        is_default=True
    ).first()
    
    # 计算最终总价（包含配送费）
    delivery_fee_total = sum(cart_data['restaurant'].delivery_fee for cart_data in restaurants_cart.values())
    final_total = total_amount + delivery_fee_total
    
    return render_template('cart/view.html',
                         restaurants_cart=restaurants_cart,
                         total_amount=total_amount,
                         final_total=final_total,
                         addresses=addresses,
                         default_address=default_address)

@cart_bp.route('/update', methods=['POST'])
@login_required
def update_cart():
    """更新购物车商品数量"""
    cart_item_id = request.json.get('cart_item_id')
    quantity = request.json.get('quantity', 1)
    
    if quantity < 1:
        return jsonify({'success': False, 'message': '数量不能小于1'})
    
    cart_item = CartItem.query.filter_by(
        id=cart_item_id,
        user_id=current_user.id
    ).first()
    
    if not cart_item:
        return jsonify({'success': False, 'message': '购物车项不存在'})
    
    cart_item.quantity = quantity
    db.session.commit()
    
    # 计算新的小计
    subtotal = cart_item.dish.price * quantity
    
    return jsonify({
        'success': True,
        'subtotal': subtotal
    })

@cart_bp.route('/remove', methods=['POST'])
@login_required
def remove_from_cart():
    """从购物车移除商品"""
    cart_item_id = request.json.get('cart_item_id')
    
    cart_item = CartItem.query.filter_by(
        id=cart_item_id,
        user_id=current_user.id
    ).first()
    
    if not cart_item:
        return jsonify({'success': False, 'message': '购物车项不存在'})
    
    db.session.delete(cart_item)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '已从购物车移除'})

@cart_bp.route('/clear')
@login_required
def clear_cart():
    """清空购物车"""
    CartItem.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    
    flash('购物车已清空')
    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """结算页面"""
    if request.method == 'POST':
        # 获取表单数据
        address_id = request.form.get('address_id')
        remark = request.form.get('remark', '')
        
        if not address_id:
            flash('请选择收货地址')
            return redirect(url_for('cart.checkout'))
        
        address = Address.query.filter_by(
            id=address_id,
            user_id=current_user.id
        ).first()
        
        if not address:
            flash('收货地址不存在')
            return redirect(url_for('cart.checkout'))
        
        # 获取购物车商品
        cart_items = db.session.query(CartItem, Dish, Restaurant).join(
            Dish, CartItem.dish_id == Dish.id
        ).join(
            Restaurant, Dish.restaurant_id == Restaurant.id
        ).filter(
            CartItem.user_id == current_user.id
        ).all()
        
        if not cart_items:
            flash('购物车为空')
            return redirect(url_for('cart.view_cart'))
        
        # 按餐厅分组创建订单
        for restaurant_id in set(item[2].id for item in cart_items):
            restaurant_items = [item for item in cart_items if item[2].id == restaurant_id]
            restaurant = restaurant_items[0][2]
            
            # 计算订单金额
            subtotal = sum(item[1].price * item[0].quantity for item in restaurant_items)
            delivery_fee = restaurant.delivery_fee
            total_amount = subtotal + delivery_fee
            
            # 创建订单
            order = Order(
                order_no=generate_order_no(),
                user_id=current_user.id,
                restaurant_id=restaurant_id,
                delivery_name=address.name,
                delivery_phone=address.phone,
                delivery_address=address.address,
                subtotal=subtotal,
                delivery_fee=delivery_fee,
                total_amount=total_amount,
                remark=remark
            )
            
            db.session.add(order)
            db.session.flush()  # 获取订单ID
            
            # 创建订单项
            for cart_item, dish, _ in restaurant_items:
                order_item = OrderItem(
                    order_id=order.id,
                    dish_id=dish.id,
                    quantity=cart_item.quantity,
                    price=dish.price,
                    subtotal=dish.price * cart_item.quantity
                )
                db.session.add(order_item)
                
                # 更新菜品销量
                dish.sales_count += cart_item.quantity
        
        # 清空购物车
        CartItem.query.filter_by(user_id=current_user.id).delete()
        
        db.session.commit()
        
        flash('订单提交成功')
        return redirect(url_for('order.list_orders'))
    
    # GET请求，显示结算页面
    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/count')
@login_required
def cart_count():
    """获取购物车商品数量"""
    count = CartItem.query.filter_by(user_id=current_user.id).count()
    return jsonify({'success': True, 'count': count})

def generate_order_no():
    """生成订单号"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_str = str(uuid.uuid4()).replace('-', '')[:6]
    return f"ORD{timestamp}{random_str}".upper() 