from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Dish, Restaurant
from app.services import cart_service
from app.api import api_bp
from app.api.errors import ok, bad_request, not_found
from app.api.schemas import AddCartItemSchema, UpdateCartItemSchema


def _build_cart_response(user_id: int) -> dict:
    """构建购物车详情响应数据（API 与页面逻辑共同的核心计算）"""
    cart_data = cart_service.get_cart(user_id)
    if not cart_data:
        return {'items': [], 'total_amount': 0, 'restaurants': []}

    dish_ids = list(cart_data.keys())
    dishes = {d.id: d for d in Dish.query.filter(Dish.id.in_(dish_ids)).all()}
    restaurant_ids = {d.restaurant_id for d in dishes.values()}
    restaurants = {r.id: r for r in
                   Restaurant.query.filter(Restaurant.id.in_(restaurant_ids)).all()}

    items = []
    total_amount = 0
    restaurants_summary = {}

    for dish_id, quantity in cart_data.items():
        dish = dishes.get(dish_id)
        if not dish or not dish.available:
            continue
        restaurant = restaurants.get(dish.restaurant_id)
        if not restaurant:
            continue

        item_total = round(dish.price * quantity, 2)
        items.append({
            'dish_id': dish_id,
            'dish_name': dish.name,
            'dish_image': dish.image,
            'price': dish.price,
            'quantity': quantity,
            'item_total': item_total,
            'restaurant_id': restaurant.id,
            'restaurant_name': restaurant.name,
        })
        total_amount = round(total_amount + item_total, 2)

        if restaurant.id not in restaurants_summary:
            restaurants_summary[restaurant.id] = {
                'restaurant_id': restaurant.id,
                'restaurant_name': restaurant.name,
                'delivery_fee': restaurant.delivery_fee,
                'min_order': restaurant.min_order,
            }

    return {
        'items': items,
        'total_amount': total_amount,
        'restaurants': list(restaurants_summary.values()),
    }


# ──────────────────────────────────────────────
# 路由
# ──────────────────────────────────────────────

@api_bp.route('/cart', methods=['GET'])
@jwt_required()
def api_get_cart():
    """查看购物车"""
    user_id = int(get_jwt_identity())
    return ok(_build_cart_response(user_id))


@api_bp.route('/cart/items', methods=['POST'])
@jwt_required()
def api_add_to_cart():
    """
    添加商品到购物车
    ---
    Body: { "dish_id": 1, "quantity": 1 }
    """
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    errors = AddCartItemSchema().validate(data)
    if errors:
        return bad_request('请求参数错误', data=errors)

    cleaned = AddCartItemSchema().load(data)
    dish_id = cleaned['dish_id']
    quantity = cleaned['quantity']

    dish = Dish.query.get(dish_id)
    if not dish:
        return not_found('菜品不存在')
    if not dish.available:
        return bad_request('该菜品已下架')

    cart_service.incr_item(user_id, dish_id, quantity)
    return ok({
        'cart_size': cart_service.size(user_id),
        'message': f'已将 {dish.name} × {quantity} 加入购物车'
    })


@api_bp.route('/cart/items/<int:dish_id>', methods=['PUT'])
@jwt_required()
def api_update_cart_item(dish_id):
    """
    更新购物车中某菜品的数量
    ---
    Body: { "quantity": 2 }
    """
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    errors = UpdateCartItemSchema().validate(data)
    if errors:
        return bad_request('请求参数错误', data=errors)

    quantity = UpdateCartItemSchema().load(data)['quantity']
    current_cart = cart_service.get_cart(user_id)
    if dish_id not in current_cart:
        return not_found('该商品不在购物车中')

    cart_service.set_item(user_id, dish_id, quantity)

    dish = Dish.query.get(dish_id)
    subtotal = round(dish.price * quantity, 2) if dish else 0
    return ok({'dish_id': dish_id, 'quantity': quantity, 'subtotal': subtotal})


@api_bp.route('/cart/items/<int:dish_id>', methods=['DELETE'])
@jwt_required()
def api_remove_cart_item(dish_id):
    """从购物车移除某菜品"""
    user_id = int(get_jwt_identity())
    cart_service.remove_item(user_id, dish_id)
    return ok(message='已移除')


@api_bp.route('/cart', methods=['DELETE'])
@jwt_required()
def api_clear_cart():
    """清空购物车"""
    user_id = int(get_jwt_identity())
    cart_service.clear(user_id)
    return ok(message='购物车已清空')
