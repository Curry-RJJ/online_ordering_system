from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import RestaurantCategory, Restaurant
from app import db

restaurant_category_bp = Blueprint('restaurant_category', __name__, url_prefix='/restaurant-category')

@restaurant_category_bp.route('/admin')
@login_required
def admin_categories():
    """餐厅分类管理列表（管理员功能）"""
    if current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('restaurant.list_restaurants'))
    
    categories = RestaurantCategory.query.order_by(RestaurantCategory.sort_order).all()
    
    # 统计每个分类下的餐厅数量
    category_stats = {}
    for category in categories:
        count = Restaurant.query.filter_by(cuisine_type=category.name).count()
        category_stats[category.id] = count
    
    return render_template('restaurant/category_list.html', 
                         categories=categories,
                         category_stats=category_stats)

@restaurant_category_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_category():
    """添加餐厅分类"""
    if current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('restaurant.list_restaurants'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        icon = request.form.get('icon', '')
        sort_order = request.form.get('sort_order', 0, type=int)
        
        # 检查分类名是否已存在
        existing = RestaurantCategory.query.filter_by(name=name).first()
        if existing:
            flash('该分类名称已存在')
            return redirect(url_for('restaurant_category.add_category'))
        
        category = RestaurantCategory(
            name=name,
            icon=icon,
            sort_order=sort_order
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash('餐厅分类添加成功')
        return redirect(url_for('restaurant_category.admin_categories'))
    
    return render_template('restaurant/category_add.html')

@restaurant_category_bp.route('/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    """编辑餐厅分类"""
    if current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('restaurant.list_restaurants'))
    
    category = RestaurantCategory.query.get_or_404(category_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        
        # 检查分类名是否已被其他分类使用
        existing = RestaurantCategory.query.filter_by(name=name).first()
        if existing and existing.id != category.id:
            flash('该分类名称已存在')
            return redirect(url_for('restaurant_category.edit_category', category_id=category_id))
        
        # 如果分类名称改变，更新所有使用该分类的餐厅
        if category.name != name:
            Restaurant.query.filter_by(cuisine_type=category.name).update({'cuisine_type': name})
        
        category.name = name
        category.icon = request.form.get('icon', '')
        category.sort_order = request.form.get('sort_order', 0, type=int)
        
        db.session.commit()
        flash('餐厅分类更新成功')
        return redirect(url_for('restaurant_category.admin_categories'))
    
    return render_template('restaurant/category_edit.html', category=category)

@restaurant_category_bp.route('/<int:category_id>/delete')
@login_required
def delete_category(category_id):
    """删除餐厅分类"""
    if current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('restaurant.list_restaurants'))
    
    category = RestaurantCategory.query.get_or_404(category_id)
    
    # 检查是否有餐厅使用该分类
    restaurant_count = Restaurant.query.filter_by(cuisine_type=category.name).count()
    if restaurant_count > 0:
        flash(f'无法删除：有 {restaurant_count} 家餐厅正在使用该分类')
        return redirect(url_for('restaurant_category.admin_categories'))
    
    db.session.delete(category)
    db.session.commit()
    
    flash('餐厅分类删除成功')
    return redirect(url_for('restaurant_category.admin_categories'))

@restaurant_category_bp.route('/list')
def get_categories():
    """获取所有餐厅分类（API）"""
    categories = RestaurantCategory.query.order_by(RestaurantCategory.sort_order).all()
    
    return jsonify({
        'categories': [{
            'id': c.id,
            'name': c.name,
            'icon': c.icon
        } for c in categories]
    }) 