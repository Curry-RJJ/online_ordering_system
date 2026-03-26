from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import Order, Dish, Restaurant, OrderItem, Review
from app import db
from datetime import datetime
try:
    from app.tasks.order_tasks import notify_order_status_change as _notify_status
    _CELERY_ENABLED = True
except Exception:
    _CELERY_ENABLED = False

order_bp = Blueprint('order', __name__, url_prefix='/order')

@order_bp.route('/create/<int:dish_id>', methods=['GET', 'POST'])
@login_required
def create_order(dish_id):
    # 单菜品直接下单已废弃，点餐请通过购物车结算
    dish = Dish.query.get_or_404(dish_id)
    flash('请通过购物车下单', 'info')
    return redirect(url_for('restaurant.restaurant_detail', restaurant_id=dish.restaurant_id))

@order_bp.route('/')
@login_required
def list_orders():
    if current_user.role == 'admin':
        # 管理员查看所有订单
        orders = Order.query.order_by(Order.created_at.desc()).all()
    elif current_user.role == 'merchant' and current_user.restaurant_id:
        # 商家管理员查看自己餐厅的订单
        orders = Order.query.filter_by(restaurant_id=current_user.restaurant_id).order_by(Order.created_at.desc()).all()
    else:
        # 普通用户查看自己的订单
        orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()

    return render_template('order/list.html', orders=orders)

@order_bp.route('/edit/<int:order_id>', methods=['GET', 'POST'])
@login_required
def edit_order(order_id):
    # 购物车模式下不支持编辑已下单订单，重定向到详情页
    flash('订单提交后不支持修改，如需更改请取消后重新下单', 'info')
    return redirect(url_for('order.order_detail', order_id=order_id))

@order_bp.route('/delete/<int:order_id>')
@login_required
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    
    if order.user_id != current_user.id and current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('order.list_orders'))
    
    # BUG-06 修复：使用英文状态值
    if order.status not in ['pending']:
        flash('订单已处理，无法删除')
        return redirect(url_for('order.list_orders'))
    
    db.session.delete(order)
    db.session.commit()
    flash('订单已删除')
    return redirect(url_for('order.list_orders'))

@order_bp.route('/admin_delete/<int:order_id>', methods=['POST'])
@login_required
def admin_delete_order(order_id):
    """管理员删除订单功能 - 可以删除任何状态的订单"""
    if current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('order.list_orders'))
    
    order = Order.query.get_or_404(order_id)
    
    try:
        # 删除订单（会自动删除关联的订单项，因为设置了cascade='all, delete-orphan'）
        db.session.delete(order)
        db.session.commit()
        flash(f'订单 {order.order_no} 已成功删除', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除订单失败：{str(e)}', 'error')
    
    return redirect(url_for('order.list_orders'))

@order_bp.route('/user_delete/<int:order_id>', methods=['POST'])
@login_required
def user_delete_order(order_id):
    """普通用户删除订单（仅限已完成或已取消的订单）"""
    order = Order.query.get(order_id)
    
    # 如果订单不存在
    if not order:
        flash('订单不存在或已被删除', 'warning')
        return redirect(url_for('order.list_orders'))
    
    # 权限检查：只能删除自己的订单
    if order.user_id != current_user.id:
        flash('权限不足', 'danger')
        return redirect(url_for('order.list_orders'))
    
    # 状态检查：只能删除已完成或已取消的订单
    if order.status not in ['completed', 'cancelled']:
        flash('只能删除已完成或已取消的订单', 'warning')
        return redirect(url_for('order.list_orders'))
    
    try:
        order_no = order.order_no
        db.session.delete(order)
        db.session.commit()
        flash(f'订单 {order_no} 已删除', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败: {str(e)}', 'danger')
    
    return redirect(url_for('order.list_orders'))

@order_bp.route('/cancel/<int:order_id>', methods=['GET', 'POST'])
@login_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    
    if order.user_id != current_user.id:
        flash('权限不足', 'danger')
        return redirect(url_for('order.list_orders'))
    
    # 修复：使用英文状态值进行判断
    if order.status not in ['pending', 'confirmed']:
        flash('当前订单状态无法取消', 'warning')
        return redirect(url_for('order.list_orders'))
    
    # 修复：设置英文状态值
    order.status = 'cancelled'
    db.session.commit()
    flash('订单已取消', 'success')
    return redirect(url_for('order.list_orders'))

@order_bp.route('/update_status/<int:order_id>', methods=['POST'])
@login_required
def update_status(order_id):
    order = Order.query.get_or_404(order_id)
    
    # 权限检查：管理员或该订单所属餐厅的商家管理员
    if current_user.role == 'admin':
        # 管理员可以更新任何订单
        pass
    elif current_user.role == 'merchant' and current_user.restaurant_id == order.restaurant_id:
        # 商家管理员只能更新自己餐厅的订单
        pass
    else:
        flash('权限不足')
        return redirect(url_for('order.list_orders'))
    
    new_status = request.form.get('status', '')

    # BUG-08 修复：加入状态机校验，防止随意跳转状态
    valid_transitions = {
        'pending': ['confirmed', 'cancelled'],
        'confirmed': ['preparing', 'cancelled'],
        'preparing': ['delivering', 'cancelled'],
        'delivering': ['completed'],
        'completed': [],
        'cancelled': [],
    }
    allowed = valid_transitions.get(order.status, [])
    if new_status not in allowed:
        flash(f'不允许从「{order.status}」切换到「{new_status}」', 'warning')
        return redirect(url_for('order.list_orders'))

    # 更新时间戳
    from datetime import datetime
    if new_status == 'confirmed' and not order.confirmed_at:
        order.confirmed_at = datetime.utcnow()
    elif new_status == 'completed' and not order.delivered_at:
        order.delivered_at = datetime.utcnow()

    order.status = new_status
    db.session.commit()

    # 异步通知用户订单状态变更，Celery 不可用时降级跳过
    if _CELERY_ENABLED:
        try:
            user_phone = order.user.phone if order.user and order.user.phone else ''
            _notify_status.delay(
                order_id=order.id,
                order_no=order.order_no,
                new_status=new_status,
                user_phone=user_phone,
            )
        except Exception:
            pass

    flash('订单状态已更新')
    return redirect(url_for('order.list_orders'))

@order_bp.route('/detail/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    
    # 权限检查：订单所属用户、管理员或该订单所属餐厅的商家管理员
    if current_user.role == 'admin':
        # 管理员可以查看任何订单
        pass
    elif current_user.role == 'merchant' and current_user.restaurant_id == order.restaurant_id:
        # 商家管理员可以查看自己餐厅的订单
        pass
    elif order.user_id == current_user.id:
        # 用户可以查看自己的订单
        pass
    else:
        flash('权限不足')
        return redirect(url_for('order.list_orders'))
    
    has_review = Review.query.filter_by(
        order_id=order_id, user_id=current_user.id
    ).first() is not None
    return render_template('order/detail.html', order=order, has_review=has_review)

@order_bp.route('/merchant/manage')
@login_required
def merchant_manage_orders():
    """商家管理员的订单管理页面"""
    if current_user.role != 'merchant' or not current_user.restaurant_id:
        flash('权限不足')
        return redirect(url_for('restaurant.list_restaurants'))
    
    # 获取餐厅信息
    restaurant = Restaurant.query.get_or_404(current_user.restaurant_id)
    
    # 获取订单列表（默认显示所有订单，可以通过状态筛选）
    status_filter = request.args.get('status', 'all')
    
    if status_filter == 'all':
        orders = Order.query.filter_by(restaurant_id=restaurant.id).order_by(Order.created_at.desc()).all()
    else:
        orders = Order.query.filter_by(restaurant_id=restaurant.id, status=status_filter).order_by(Order.created_at.desc()).all()
    
    # 统计数据
    total_orders = Order.query.filter_by(restaurant_id=restaurant.id).count()
    pending_orders = Order.query.filter_by(restaurant_id=restaurant.id, status='pending').count()
    confirmed_orders = Order.query.filter_by(restaurant_id=restaurant.id, status='confirmed').count()
    preparing_orders = Order.query.filter_by(restaurant_id=restaurant.id, status='preparing').count()
    delivering_orders = Order.query.filter_by(restaurant_id=restaurant.id, status='delivering').count()
    completed_orders = Order.query.filter_by(restaurant_id=restaurant.id, status='completed').count()
    cancelled_orders = Order.query.filter_by(restaurant_id=restaurant.id, status='cancelled').count()
    
    # 今日订单统计
    from datetime import date
    today = date.today()
    today_orders = Order.query.filter(
        Order.restaurant_id == restaurant.id,
        db.func.date(Order.created_at) == today
    ).count()
    
    # 今日营业额
    today_revenue = db.session.query(db.func.sum(Order.total_amount)).filter(
        Order.restaurant_id == restaurant.id,
        Order.status.in_(['confirmed', 'preparing', 'delivering', 'completed']),
        db.func.date(Order.created_at) == today
    ).scalar() or 0
    
    stats = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'preparing_orders': preparing_orders,
        'delivering_orders': delivering_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
        'today_orders': today_orders,
        'today_revenue': today_revenue
    }
    
    # BUG-14 修复：补充 status_filter_name 供模板显示
    status_name_map = {
        'all': '全部订单',
        'pending': '待处理',
        'confirmed': '已确认',
        'preparing': '准备中',
        'delivering': '配送中',
        'completed': '已完成',
        'cancelled': '已取消',
    }
    status_filter_name = status_name_map.get(status_filter, '全部订单')

    return render_template('order/merchant_manage.html',
                         restaurant=restaurant,
                         orders=orders,
                         stats=stats,
                         status_filter=status_filter,
                         status_filter_name=status_filter_name)

@order_bp.route('/merchant/update_status/<int:order_id>', methods=['POST'])
@login_required
def merchant_update_status(order_id):
    """商家管理员快速更新订单状态（AJAX接口）"""
    if current_user.role != 'merchant' or not current_user.restaurant_id:
        return jsonify({'success': False, 'message': '权限不足'})
    
    order = Order.query.get_or_404(order_id)
    
    # 验证订单属于该商家
    if order.restaurant_id != current_user.restaurant_id:
        return jsonify({'success': False, 'message': '无权操作此订单'})
    
    data = request.get_json()
    new_status = data.get('status')
    
    # 验证状态转换的合法性
    valid_transitions = {
        'pending': ['confirmed', 'cancelled'],
        'confirmed': ['preparing', 'cancelled'],
        'preparing': ['delivering'],
        'delivering': ['completed'],
        'completed': [],
        'cancelled': []
    }
    
    if new_status not in valid_transitions.get(order.status, []):
        return jsonify({'success': False, 'message': f'无法从{order.status}状态转换到{new_status}状态'})
    
    # 更新状态
    order.status = new_status
    
    # 更新时间戳
    if new_status == 'confirmed' and not order.confirmed_at:
        order.confirmed_at = datetime.utcnow()
    elif new_status == 'completed' and not order.delivered_at:
        order.delivered_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': '订单状态已更新', 'new_status': new_status})

@order_bp.route('/merchant/delete/<int:order_id>', methods=['POST'])
@login_required
def merchant_delete_order(order_id):
    """商家管理员删除订单（仅限已完成或已取消的订单）"""
    if current_user.role != 'merchant' or not current_user.restaurant_id:
        flash('权限不足', 'danger')
        return redirect(url_for('order.merchant_manage_orders'))
    
    order = Order.query.get(order_id)
    
    # 如果订单不存在
    if not order:
        flash('订单不存在或已被删除', 'warning')
        return redirect(url_for('order.merchant_manage_orders'))
    
    # 验证订单属于该商家
    if order.restaurant_id != current_user.restaurant_id:
        flash('无权操作此订单', 'danger')
        return redirect(url_for('order.merchant_manage_orders'))
    
    # 状态检查：只能删除已完成或已取消的订单
    if order.status not in ['completed', 'cancelled']:
        flash('只能删除已完成或已取消的订单', 'warning')
        return redirect(url_for('order.merchant_manage_orders'))
    
    try:
        order_no = order.order_no
        db.session.delete(order)
        db.session.commit()
        flash(f'订单 {order_no} 已删除', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败: {str(e)}', 'danger')

    return redirect(url_for('order.merchant_manage_orders'))


# ── 评价功能 ─────────────────────────────────────────────────────────────────

@order_bp.route('/<int:order_id>/review', methods=['GET', 'POST'])
@login_required
def submit_review(order_id):
    """提交订单评价"""
    order = Order.query.get_or_404(order_id)

    if order.user_id != current_user.id:
        flash('权限不足', 'danger')
        return redirect(url_for('order.list_orders'))

    if order.status != 'completed':
        flash('只有已完成的订单才能评价', 'warning')
        return redirect(url_for('order.order_detail', order_id=order_id))

    existing = Review.query.filter_by(order_id=order_id, user_id=current_user.id).first()
    if existing:
        flash('您已评价过此订单', 'info')
        return redirect(url_for('order.order_detail', order_id=order_id))

    if request.method == 'POST':
        try:
            rating = int(request.form.get('rating', 0))
        except (ValueError, TypeError):
            rating = 0

        if rating not in range(1, 6):
            flash('请选择 1-5 星评分', 'warning')
            return render_template('order/review.html', order=order)

        content = request.form.get('content', '').strip()

        review = Review(
            user_id=current_user.id,
            restaurant_id=order.restaurant_id,
            order_id=order_id,
            rating=rating,
            content=content or None,
        )
        db.session.add(review)

        # 加权平均更新餐厅评分
        restaurant = Restaurant.query.get(order.restaurant_id)
        if restaurant:
            old_count = restaurant.review_count or 0
            old_rating = restaurant.rating or 0.0
            new_count = old_count + 1
            new_rating = round((old_rating * old_count + rating) / new_count, 1)
            restaurant.review_count = new_count
            restaurant.rating = new_rating

        db.session.commit()

        # 清除列表缓存，评分立即刷新
        from app import cache as _cache
        _cache.clear()

        flash('评价提交成功，感谢您的反馈！', 'success')
        return redirect(url_for('order.order_detail', order_id=order_id))

    return render_template('order/review.html', order=order)
