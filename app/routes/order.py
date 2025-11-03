from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Order, Dish
from app import db

order_bp = Blueprint('order', __name__, url_prefix='/order')

@order_bp.route('/create/<int:dish_id>', methods=['GET', 'POST'])
@login_required
def create_order(dish_id):
    dish = Dish.query.get_or_404(dish_id)

    if request.method == 'POST':
        quantity = int(request.form['quantity'])
        order = Order(user_id=current_user.id, dish_id=dish_id, quantity=quantity)
        db.session.add(order)
        db.session.commit()
        flash('下单成功')
        return redirect(url_for('order.list_orders'))

    return render_template('order/create.html', dish=dish)

@order_bp.route('/')
@login_required
def list_orders():
    if current_user.role == 'admin':
        orders = Order.query.all()
    else:
        orders = Order.query.filter_by(user_id=current_user.id).all()

    return render_template('order/list.html', orders=orders)

@order_bp.route('/edit/<int:order_id>', methods=['GET', 'POST'])
@login_required
def edit_order(order_id):
    order = Order.query.get_or_404(order_id)
    
    if order.user_id != current_user.id and current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('order.list_orders'))
    
    if order.status not in ['未处理', '准备中']:
        flash('订单已确认，无法修改')
        return redirect(url_for('order.list_orders'))
    
    if request.method == 'POST':
        quantity = int(request.form['quantity'])
        order.quantity = quantity
        db.session.commit()
        flash('订单修改成功')
        return redirect(url_for('order.list_orders'))
    
    return render_template('order/edit.html', order=order)

@order_bp.route('/delete/<int:order_id>')
@login_required
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    
    if order.user_id != current_user.id and current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('order.list_orders'))
    
    if order.status not in ['未处理']:
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

@order_bp.route('/cancel/<int:order_id>')
@login_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    
    if order.user_id != current_user.id:
        flash('权限不足')
        return redirect(url_for('order.list_orders'))
    
    if order.status not in ['未处理', '准备中']:
        flash('订单状态无法取消')
        return redirect(url_for('order.list_orders'))
    
    order.status = '已取消'
    db.session.commit()
    flash('订单已取消')
    return redirect(url_for('order.list_orders'))

@order_bp.route('/update_status/<int:order_id>', methods=['POST'])
@login_required
def update_status(order_id):
    if current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('order.list_orders'))

    order = Order.query.get_or_404(order_id)
    new_status = request.form['status']
    order.status = new_status
    db.session.commit()
    flash('订单状态已更新')
    return redirect(url_for('order.list_orders'))

@order_bp.route('/detail/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    
    if order.user_id != current_user.id and current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('order.list_orders'))
    
    return render_template('order/detail.html', order=order)
