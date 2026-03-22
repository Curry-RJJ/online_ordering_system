from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Order, OrderItem, Address, Dish, Restaurant
from app import db
from app.services import cart_service
from app.routes.cart import _create_orders, generate_order_no
from app.api import api_bp
from app.api.errors import ok, created, bad_request, not_found, forbidden
from app.api.schemas import CreateOrderSchema
try:
    from app.tasks.order_tasks import notify_new_order as _notify_new_order
    _CELERY_ENABLED = True
except Exception:
    _CELERY_ENABLED = False


def _order_dict(order: Order, include_items: bool = False) -> dict:
    result = {
        'id': order.id,
        'order_no': order.order_no,
        'restaurant_id': order.restaurant_id,
        'status': order.status,
        'payment_status': order.payment_status,
        'subtotal': order.subtotal,
        'delivery_fee': order.delivery_fee,
        'total_amount': order.total_amount,
        'delivery_name': order.delivery_name,
        'delivery_phone': order.delivery_phone,
        'delivery_address': order.delivery_address,
        'remark': order.remark,
        'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
    }
    if include_items:
        result['items'] = [
            {
                'dish_id': item.dish_id,
                'dish_name': item.dish.name if item.dish else '已删除',
                'price': item.price,
                'quantity': item.quantity,
                'subtotal': item.subtotal,
            }
            for item in order.order_items.all()
        ]
    return result


# ──────────────────────────────────────────────
# 路由
# ──────────────────────────────────────────────

@api_bp.route('/orders', methods=['GET'])
@jwt_required()
def api_list_orders():
    """
    获取当前用户的订单列表
    ---
    Query: status(可选过滤), page, per_page
    """
    user_id = int(get_jwt_identity())
    status = request.args.get('status', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 50)

    query = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc())
    if status:
        query = query.filter_by(status=status)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return ok({
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages,
        'orders': [_order_dict(o) for o in pagination.items]
    })


@api_bp.route('/orders/<int:order_id>', methods=['GET'])
@jwt_required()
def api_get_order(order_id):
    """获取订单详情（含订单项）"""
    user_id = int(get_jwt_identity())
    order = Order.query.get(order_id)

    if not order:
        return not_found('订单不存在')
    if order.user_id != user_id:
        return forbidden()

    return ok(_order_dict(order, include_items=True))


@api_bp.route('/orders', methods=['POST'])
@jwt_required()
def api_create_order():
    """
    从购物车创建订单（结算）
    ---
    Body: { "address_id": 1, "remark": "..." }
    """
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    errors = CreateOrderSchema().validate(data)
    if errors:
        return bad_request('请求参数错误', data=errors)

    cleaned = CreateOrderSchema().load(data)
    address_id = cleaned['address_id']
    remark = cleaned['remark']

    address = Address.query.filter_by(id=address_id, user_id=user_id).first()
    if not address:
        return not_found('收货地址不存在')

    cart_data = cart_service.get_cart(user_id)
    if not cart_data:
        return bad_request('购物车为空，请先加入商品')

    try:
        _create_orders(cart_data, address, remark, user_id)
        cart_service.clear(user_id)
    except Exception as e:
        db.session.rollback()
        return bad_request(f'下单失败：{str(e)}')

    latest_orders = Order.query.filter_by(user_id=user_id) \
                               .order_by(Order.created_at.desc()) \
                               .limit(10).all()

    # 异步通知：每笔订单触发一次商家通知任务，不阻塞当前请求
    # Celery Worker 不可用时自动降级，不影响下单主流程
    if _CELERY_ENABLED:
        for order in latest_orders:
            restaurant = Restaurant.query.get(order.restaurant_id)
            restaurant_name = restaurant.name if restaurant else '未知餐厅'
            try:
                _notify_new_order.delay(
                    order_id=order.id,
                    order_no=order.order_no,
                    restaurant_name=restaurant_name,
                    total_amount=float(order.total_amount),
                )
            except Exception:
                pass

    return created({
        'orders': [_order_dict(o) for o in latest_orders]
    }, message='下单成功')


@api_bp.route('/orders/<int:order_id>/cancel', methods=['PATCH'])
@jwt_required()
def api_cancel_order(order_id):
    """
    取消订单（仅限 pending 状态）
    ---
    """
    user_id = int(get_jwt_identity())
    order = Order.query.get(order_id)

    if not order:
        return not_found('订单不存在')
    if order.user_id != user_id:
        return forbidden()
    if order.status != 'pending':
        return bad_request(f'当前订单状态（{order.status}）不可取消')

    order.status = 'cancelled'
    db.session.commit()
    return ok(_order_dict(order), message='订单已取消')
