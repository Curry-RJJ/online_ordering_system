from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Category
from app import db

category_bp = Blueprint('category', __name__, url_prefix='/category')

@category_bp.route('/admin')
@login_required
def admin_categories():
    """分类管理列表"""
    if current_user.role != 'admin':
        flash('权限不足', 'danger')
        return redirect(url_for('restaurant.list_restaurants'))
    
    categories = Category.query.order_by(Category.sort_order).all()
    return render_template('category/admin_list.html', categories=categories)

@category_bp.route('/admin/add', methods=['GET', 'POST'])
@login_required
def add_category():
    """添加新分类"""
    if current_user.role != 'admin':
        flash('权限不足', 'danger')
        return redirect(url_for('restaurant.list_restaurants'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        icon = request.form.get('icon')
        sort_order = request.form.get('sort_order', 0, type=int)

        if not name:
            flash('分类名称不能为空', 'warning')
            return redirect(url_for('category.add_category'))

        if Category.query.filter_by(name=name).first():
            flash('该分类已存在', 'warning')
            return redirect(url_for('category.add_category'))

        new_category = Category(name=name, icon=icon, sort_order=sort_order)
        db.session.add(new_category)
        db.session.commit()
        flash('分类添加成功', 'success')
        return redirect(url_for('category.admin_categories'))

    return render_template('category/form.html')

@category_bp.route('/admin/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    """编辑分类"""
    if current_user.role != 'admin':
        flash('权限不足', 'danger')
        return redirect(url_for('restaurant.list_restaurants'))
        
    category = Category.query.get_or_404(category_id)

    if request.method == 'POST':
        name = request.form.get('name')
        icon = request.form.get('icon')
        sort_order = request.form.get('sort_order', 0, type=int)

        if not name:
            flash('分类名称不能为空', 'warning')
            return redirect(url_for('category.edit_category', category_id=category_id))

        category.name = name
        category.icon = icon
        category.sort_order = sort_order
        db.session.commit()
        flash('分类更新成功', 'success')
        return redirect(url_for('category.admin_categories'))

    return render_template('category/form.html', category=category)

@category_bp.route('/admin/delete/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    """删除分类"""
    if current_user.role != 'admin':
        flash('权限不足', 'danger')
        return redirect(url_for('restaurant.list_restaurants'))
        
    category = Category.query.get_or_404(category_id)

    if category.dishes.count() > 0:
        flash('无法删除：该分类下还有菜品。', 'danger')
        return redirect(url_for('category.admin_categories'))

    db.session.delete(category)
    db.session.commit()
    flash('分类删除成功', 'success')
    return redirect(url_for('category.admin_categories')) 