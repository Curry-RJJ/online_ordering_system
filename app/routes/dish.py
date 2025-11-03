from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import Dish, Restaurant, Category
from app.utils import save_uploaded_image, delete_image_file, create_image_directories
from app import db

dish_bp = Blueprint('dish', __name__, url_prefix='/dish')

@dish_bp.route('/')
def list_dishes():
    dishes = Dish.query.all()
    return render_template('dish/list.html', dishes=dishes)

@dish_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_dish():
    if current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('dish.list_dishes'))

    if request.method == 'POST':
        # 确保图片目录存在
        create_image_directories()
        
        # 基本信息
        name = request.form['name']
        price = float(request.form['price'])
        description = request.form.get('description', '')
        restaurant_id = request.form.get('restaurant_id', type=int)
        category_id = request.form.get('category_id', type=int) or None
        ingredients = request.form.get('ingredients', '')
        
        # 价格信息
        original_price = float(request.form.get('original_price') or 0) or None
        discount_rate = float(request.form.get('discount_rate') or 0) or None
        
        # 其他信息
        rating = float(request.form.get('rating', 4.5))
        sales_count = int(request.form.get('sales_count', 0))
        
        # 处理菜品图片上传
        image = ''
        image_file = request.files.get('image_file')
        if image_file and image_file.filename:
            # 保存新的图片
            new_image_path = save_uploaded_image(image_file, 'dishes', max_size=(600, 400))
            if new_image_path:
                image = new_image_path
            else:
                flash('菜品图片上传失败，请检查文件格式')
        elif request.form.get('image_url'):
            # 如果没有上传文件但有URL，使用URL
            image = request.form.get('image_url', '')
        
        # 状态设置
        available = request.form.get('available') == 'on'
        is_recommended = request.form.get('is_recommended') == 'on'
        is_spicy = request.form.get('is_spicy') == 'on'

        new_dish = Dish(
            name=name,
            price=price,
            description=description,
            restaurant_id=restaurant_id,
            category_id=category_id,
            ingredients=ingredients,
            original_price=original_price,
            discount_rate=discount_rate,
            rating=rating,
            sales_count=sales_count,
            image=image,
            available=available,
            is_recommended=is_recommended,
            is_spicy=is_spicy
        )
        
        db.session.add(new_dish)
        db.session.commit()
        flash('菜品添加成功')
        return redirect(url_for('dish.admin_dishes'))

    # 获取所有餐厅和分类
    restaurants = Restaurant.query.all()
    categories = Category.query.all()
    
    return render_template('dish/add.html',
                         restaurants=restaurants,
                         categories=categories)

@dish_bp.route('/edit/<int:dish_id>', methods=['GET', 'POST'])
@login_required
def edit_dish(dish_id):
    dish = Dish.query.get_or_404(dish_id)

    if current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('dish.list_dishes'))

    if request.method == 'POST':
        # 确保图片目录存在
        create_image_directories()
        
        # 基本信息
        dish.name = request.form['name']
        dish.price = float(request.form['price'])
        dish.description = request.form.get('description', '')
        dish.restaurant_id = request.form.get('restaurant_id', type=int)
        dish.category_id = request.form.get('category_id', type=int) or None
        dish.ingredients = request.form.get('ingredients', '')
        
        # 价格信息
        dish.original_price = float(request.form.get('original_price') or 0) or None
        dish.discount_rate = float(request.form.get('discount_rate') or 0) or None
        
        # 其他信息
        dish.rating = float(request.form.get('rating', 4.5))
        dish.sales_count = int(request.form.get('sales_count', 0))
        
        # 处理菜品图片上传
        image_file = request.files.get('image_file')
        if image_file and image_file.filename:
            # 删除旧的图片文件
            if dish.image and not dish.image.startswith('http'):
                delete_image_file(dish.image)
            
            # 保存新的图片
            new_image_path = save_uploaded_image(image_file, 'dishes', max_size=(600, 400))
            if new_image_path:
                dish.image = new_image_path
            else:
                flash('菜品图片上传失败，请检查文件格式')
        elif request.form.get('image_url'):
            # 如果没有上传文件但有URL，使用URL
            dish.image = request.form.get('image_url', '')
        
        # 状态设置
        dish.available = request.form.get('available') == 'on'
        dish.is_recommended = request.form.get('is_recommended') == 'on'
        dish.is_spicy = request.form.get('is_spicy') == 'on'

        db.session.commit()
        flash('菜品修改成功')
        return redirect(url_for('dish.admin_dishes'))

    # 获取所有餐厅和分类
    restaurants = Restaurant.query.all()
    categories = Category.query.all()
    
    return render_template('dish/edit.html', 
                         dish=dish,
                         restaurants=restaurants,
                         categories=categories)

@dish_bp.route('/delete/<int:dish_id>')
@login_required
def delete_dish(dish_id):
    if current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('dish.list_dishes'))

    dish = Dish.query.get_or_404(dish_id)
    
    # 检查是否有关联的购物车项
    cart_items_count = dish.cart_items.count()
    if cart_items_count > 0:
        flash(f'无法删除：该菜品在 {cart_items_count} 个购物车中，请先清理相关购物车项', 'danger')
        return redirect(url_for('dish.admin_dishes'))
    
    # 检查是否有关联的订单项
    order_items_count = dish.order_items.count()
    if order_items_count > 0:
        flash(f'无法删除：该菜品已有 {order_items_count} 个订单记录，建议使用下架功能而不是删除', 'danger')
        return redirect(url_for('dish.admin_dishes'))
    
    try:
        db.session.delete(dish)
        db.session.commit()
        flash('菜品已删除', 'success')
    except Exception as e:
        db.session.rollback()
        flash('删除失败，请联系系统管理员', 'danger')
        
    return redirect(url_for('dish.admin_dishes'))

@dish_bp.route('/admin')
@login_required
def admin_dishes():
    """菜品管理列表（管理员功能）"""
    if current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('dish.list_dishes'))
    
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    keyword = request.args.get('keyword', '')
    restaurant_id = request.args.get('restaurant_id', type=int)
    available = request.args.get('available', '')
    
    # 构建查询
    query = Dish.query
    
    if keyword:
        query = query.filter(Dish.name.contains(keyword))
    
    if restaurant_id:
        query = query.filter_by(restaurant_id=restaurant_id)
    
    if available != '':
        query = query.filter_by(available=bool(int(available)))
    
    # 分页
    pagination = query.paginate(page=page, per_page=10, error_out=False)
    dishes = pagination.items
    
    # 获取所有餐厅用于筛选
    restaurants = Restaurant.query.all()
    
    return render_template('dish/admin_list.html', 
                         dishes=dishes,
                         restaurants=restaurants,
                         pagination=pagination)

@dish_bp.route('/<int:dish_id>/toggle_available', methods=['POST'])
@login_required
def toggle_available(dish_id):
    """切换菜品上下架状态（管理员功能）"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'})
    
    dish = Dish.query.get_or_404(dish_id)
    data = request.get_json()
    new_status = data.get('available')
    
    if new_status is not None:
        dish.available = new_status
        db.session.commit()
        return jsonify({'success': True, 'message': '状态更新成功'})
    
    return jsonify({'success': False, 'message': '无效的状态'})

@dish_bp.route('/delete/<int:dish_id>/force', methods=['POST'])
@login_required
def force_delete_dish(dish_id):
    """强制删除菜品（会清理相关数据）"""
    if current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('dish.list_dishes'))

    dish = Dish.query.get_or_404(dish_id)
    
    try:
        # 先删除相关的购物车项
        from app.models import CartItem
        CartItem.query.filter_by(dish_id=dish_id).delete()
        
        # 注意：不删除订单项，因为这会影响历史订单数据
        # 如果真的需要删除，可以先检查订单状态，只删除未完成的订单中的项目
        
        # 删除菜品
        db.session.delete(dish)
        db.session.commit()
        flash('菜品及相关购物车数据已强制删除', 'success')
    except Exception as e:
        db.session.rollback()
        flash('强制删除失败，请联系系统管理员', 'danger')
        
    return redirect(url_for('dish.admin_dishes'))
