from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import Dish, Restaurant, Order, OrderItem, Address
from app import db
from app.services import cart_service
from types import SimpleNamespace
import uuid
from datetime import datetime

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')


@cart_bp.route('/add', methods=['POST'])
@login_required
def add_to_cart():
    dish_id = request.json.get('dish_id')
    quantity = request.json.get('quantity', 1)

    if not dish_id:
        return jsonify({'success': False, 'message': '商品ID不能为空'})

    dish = Dish.query.get_or_404(dish_id)
    if not dish.available:
        return jsonify({'success': False, 'message': '商品已下架'})

    cart_service.incr_item(current_user.id, dish_id, quantity)
    return jsonify({
        'success': True,
        'message': '已添加到购物车',
        'cart_count': cart_service.size(current_user.id)
    })


@cart_bp.route('/')
@login_required
def view_cart():
    cart_data = cart_service.get_cart(current_user.id)
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    default_address = next((a for a in addresses if a.is_default), None)

    if not cart_data:
        return render_template('cart/view.html',
                               restaurants_cart={}, total_amount=0,
                               final_total=0, addresses=addresses,
                               default_address=default_address)

    dish_ids = list(cart_data.keys())
    dishes = {d.id: d for d in Dish.query.filter(Dish.id.in_(dish_ids)).all()}
    restaurant_ids = {d.restaurant_id for d in dishes.values()}
    restaurants = {r.id: r for r in
                   Restaurant.query.filter(Restaurant.id.in_(restaurant_ids)).all()}

    restaurants_cart = {}
    total_amount = 0

    for dish_id, quantity in cart_data.items():
        dish = dishes.get(dish_id)
        if not dish or not dish.available:
            continue
        restaurant = restaurants.get(dish.restaurant_id)
        if not restaurant:
            continue

        if restaurant.id not in restaurants_cart:
            restaurants_cart[restaurant.id] = {
                'restaurant': restaurant, 'items': [], 'subtotal': 0
            }

        item_total = round(dish.price * quantity, 2)
        restaurants_cart[restaurant.id]['items'].append({
            'cart_item': SimpleNamespace(id=dish_id, quantity=quantity),
            'dish': dish,
            'total': item_total
        })
        restaurants_cart[restaurant.id]['subtotal'] = round(
            restaurants_cart[restaurant.id]['subtotal'] + item_total, 2)
        total_amount = round(total_amount + item_total, 2)

    delivery_fee_total = sum(c['restaurant'].delivery_fee for c in restaurants_cart.values())
    final_total = round(total_amount + delivery_fee_total, 2)

    return render_template('cart/view.html',
                           restaurants_cart=restaurants_cart,
                           total_amount=total_amount,
                           final_total=final_total,
                           addresses=addresses,
                           default_address=default_address)


@cart_bp.route('/update', methods=['POST'])
@login_required
def update_cart():
    dish_id = request.json.get('cart_item_id')
    quantity = request.json.get('quantity', 1)

    if not dish_id:
        return jsonify({'success': False, 'message': '商品ID不能为空'})
    if quantity < 1:
        return jsonify({'success': False, 'message': '数量不能小于1'})

    current_cart = cart_service.get_cart(current_user.id)
    if int(dish_id) not in current_cart:
        return jsonify({'success': False, 'message': '购物车项不存在'})

    cart_service.set_item(current_user.id, dish_id, quantity)
    dish = Dish.query.get(dish_id)
    subtotal = round(dish.price * quantity, 2) if dish else 0
    return jsonify({'success': True, 'subtotal': subtotal})


@cart_bp.route('/remove', methods=['POST'])
@login_required
def remove_from_cart():
    dish_id = request.json.get('cart_item_id')
    if not dish_id:
        return jsonify({'success': False, 'message': '商品ID不能为空'})
    cart_service.remove_item(current_user.id, dish_id)
    return jsonify({'success': True, 'message': '已从购物车移除'})


@cart_bp.route('/clear')
@login_required
def clear_cart():
    cart_service.clear(current_user.id)
    flash('购物车已清空')
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if request.method == 'POST':
        address_id = request.form.get('address_id')
        remark = request.form.get('remark', '')

        if not address_id:
            flash('请选择收货地址')
            return redirect(url_for('cart.checkout'))

        address = Address.query.filter_by(id=address_id, user_id=current_user.id).first()
        if not address:
            flash('收货地址不存在')
            return redirect(url_for('cart.checkout'))

        cart_data = cart_service.get_cart(current_user.id)
        if not cart_data:
            flash('购物车为空')
            return redirect(url_for('cart.view_cart'))

        _create_orders(cart_data, address, remark, current_user.id)
        cart_service.clear(current_user.id)
        flash('订单提交成功')
        return redirect(url_for('order.list_orders'))

    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/count')
@login_required
def cart_count():
    return jsonify({'success': True, 'count': cart_service.size(current_user.id)})


# ──────────────────────────────────────────────
# 内部工具
# ──────────────────────────────────────────────

def _create_orders(cart_data: dict, address, remark: str, user_id: int):
    """根据购物车数据按餐厅分组创建订单（页面路由和 API 共用）"""
    dish_ids = list(cart_data.keys())
    dishes = {d.id: d for d in Dish.query.filter(Dish.id.in_(dish_ids)).all()}
    restaurant_ids = {d.restaurant_id for d in dishes.values()}
    restaurants_map = {r.id: r for r in
                       Restaurant.query.filter(Restaurant.id.in_(restaurant_ids)).all()}

    restaurant_items: dict = {}
    for dish_id, quantity in cart_data.items():
        dish = dishes.get(dish_id)
        if not dish:
            continue
        restaurant_items.setdefault(dish.restaurant_id, []).append((dish, quantity))

    for restaurant_id, items in restaurant_items.items():
        restaurant = restaurants_map[restaurant_id]
        subtotal = round(sum(d.price * q for d, q in items), 2)
        total_amount = round(subtotal + restaurant.delivery_fee, 2)

        order = Order(
            order_no=generate_order_no(),
            user_id=user_id,
            restaurant_id=restaurant_id,
            delivery_name=address.name,
            delivery_phone=address.phone,
            delivery_address=address.address,
            subtotal=subtotal,
            delivery_fee=restaurant.delivery_fee,
            total_amount=total_amount,
            remark=remark
        )
        db.session.add(order)
        db.session.flush()

        for dish, quantity in items:
            db.session.add(OrderItem(
                order_id=order.id,
                dish_id=dish.id,
                quantity=quantity,
                price=dish.price,
                subtotal=round(dish.price * quantity, 2)
            ))
            dish.sales_count += quantity

    db.session.commit()


def generate_order_no() -> str:
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"ORD{timestamp}{str(uuid.uuid4()).replace('-', '')[:6]}".upper()
