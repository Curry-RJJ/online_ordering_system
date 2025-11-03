from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models import Restaurant, Dish, Category, Review, CartItem
from app.utils import save_uploaded_image, delete_image_file, create_image_directories
from app import db
from sqlalchemy import func, or_

restaurant_bp = Blueprint('restaurant', __name__, url_prefix='/restaurant')

@restaurant_bp.route('/')
def list_restaurants():
    """餐厅列表页面"""
    try:
        # 获取搜索关键词
        keyword = request.args.get('keyword', '')
        category_id = request.args.get('category', type=int)
        sort_by = request.args.get('sort', 'rating')  # rating, distance, sales
        
        # 构建查询
        query = Restaurant.query.filter_by(status='open')
        
        if keyword:
            # 同时搜索餐厅名称和菜品名称
            dish_restaurants = db.session.query(Restaurant.id).join(Dish).filter(
                Dish.name.contains(keyword),
                Dish.available == True
            ).distinct().subquery()
            
            query = query.filter(
                or_(
                    Restaurant.name.contains(keyword),
                    Restaurant.id.in_(dish_restaurants)
                )
            )
        
        if category_id:
            # 筛选特定分类的餐厅
            query = query.join(Dish).join(Category).filter(Category.id == category_id)

        # 排序
        if sort_by == 'rating':
            query = query.order_by(Restaurant.rating.desc())
        elif sort_by == 'sales':
            query = query.order_by(Restaurant.review_count.desc())
        else:
            query = query.order_by(Restaurant.created_at.desc())
        
        restaurants = query.distinct().all()
        
        # 获取所有分类用于筛选
        all_categories = Category.query.order_by(Category.sort_order).all()
        
        return render_template('restaurant/list.html', 
                             restaurants=restaurants, 
                             categories=all_categories,
                             keyword=keyword,
                             current_category=category_id,
                             sort_by=sort_by)
    except Exception as e:
        # 记录错误
        current_app.logger.error(f"Error in list_restaurants: {e}")
        # 显示一个通用的错误页面
        return render_template('errors/500.html'), 500

@restaurant_bp.route('/<int:restaurant_id>')
def restaurant_detail(restaurant_id):
    """餐厅详情页面"""
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    
    # 获取菜品分类
    categories = db.session.query(Category).join(Dish).filter(
        Dish.restaurant_id == restaurant_id,
        Dish.available == True
    ).distinct().all()
    
    # 获取推荐菜品
    recommended_dishes = Dish.query.filter_by(
        restaurant_id=restaurant_id,
        is_recommended=True,
        available=True
    ).limit(6).all()
    
    # 获取所有菜品（按分类分组）
    dishes_by_category = {}
    for category in categories:
        dishes = Dish.query.filter_by(
            restaurant_id=restaurant_id,
            category_id=category.id,
            available=True
        ).order_by(Dish.sales_count.desc()).all()
        dishes_by_category[category.name] = dishes
    
    # 获取评价
    reviews = Review.query.filter_by(restaurant_id=restaurant_id)\
                         .order_by(Review.created_at.desc())\
                         .limit(10).all()
    
    # 获取用户购物车数量（如果已登录）
    cart_count = 0
    if current_user.is_authenticated:
        cart_count = CartItem.query.filter_by(user_id=current_user.id)\
                                  .join(Dish)\
                                  .filter(Dish.restaurant_id == restaurant_id)\
                                  .count()
    
    return render_template('restaurant/detail.html',
                         restaurant=restaurant,
                         categories=categories,
                         recommended_dishes=recommended_dishes,
                         dishes_by_category=dishes_by_category,
                         reviews=reviews,
                         cart_count=cart_count)

@restaurant_bp.route('/<int:restaurant_id>/menu')
def restaurant_menu(restaurant_id):
    """餐厅菜单页面（AJAX加载）"""
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    category_id = request.args.get('category_id', type=int)
    
    query = Dish.query.filter_by(restaurant_id=restaurant_id, available=True)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    dishes = query.order_by(Dish.sales_count.desc()).all()
    
    return jsonify({
        'dishes': [{
            'id': dish.id,
            'name': dish.name,
            'description': dish.description,
            'price': dish.price,
            'original_price': dish.original_price,
            'image': dish.image,
            'sales_count': dish.sales_count,
            'rating': dish.rating,
            'is_recommended': dish.is_recommended,
            'is_spicy': dish.is_spicy
        } for dish in dishes]
    })

@restaurant_bp.route('/search')
def search_restaurants():
    """搜索餐厅"""
    keyword = request.args.get('q', '')
    
    if not keyword:
        return jsonify({'restaurants': []})
    
    restaurants = Restaurant.query.filter(
        Restaurant.name.contains(keyword),
        Restaurant.status == 'open'
    ).limit(10).all()
    
    return jsonify({
        'restaurants': [{
            'id': r.id,
            'name': r.name,
            'description': r.description,
            'logo': r.logo,
            'rating': r.rating,
            'delivery_fee': r.delivery_fee,
            'min_order': r.min_order
        } for r in restaurants]
    })

@restaurant_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_restaurant():
    """添加餐厅（管理员功能）"""
    if current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('restaurant.list_restaurants'))
    
    if request.method == 'POST':
        restaurant = Restaurant(
            name=request.form['name'],
            description=request.form.get('description', ''),
            address=request.form.get('address', ''),
            phone=request.form.get('phone', ''),
            business_hours=request.form.get('business_hours', ''),
            delivery_fee=float(request.form.get('delivery_fee', 0)),
            min_order=float(request.form.get('min_order', 0)),
            logo=request.form.get('logo', ''),
            banner=request.form.get('banner', '')
        )
        
        db.session.add(restaurant)
        db.session.commit()
        
        flash('餐厅添加成功')
        return redirect(url_for('restaurant.list_restaurants'))
    
    return render_template('restaurant/add.html')

@restaurant_bp.route('/<int:restaurant_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_restaurant(restaurant_id):
    """编辑餐厅（管理员功能）"""
    if current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('restaurant.list_restaurants'))
    
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    
    if request.method == 'POST':
        # 确保图片目录存在
        create_image_directories()
        
        # 基本信息更新
        restaurant.name = request.form['name']
        restaurant.description = request.form.get('description', '')
        restaurant.address = request.form.get('address', '')
        restaurant.phone = request.form.get('phone', '')
        restaurant.business_hours = request.form.get('business_hours', '')
        restaurant.delivery_fee = float(request.form.get('delivery_fee', 0))
        restaurant.min_order = float(request.form.get('min_order', 0))
        restaurant.status = request.form.get('status', 'open')
        restaurant.rating = float(request.form.get('rating', 4.5))
        
        # 处理Logo图片上传
        logo_file = request.files.get('logo_file')
        if logo_file and logo_file.filename:
            # 删除旧的logo文件
            if restaurant.logo:
                delete_image_file(restaurant.logo)
            
            # 保存新的logo
            new_logo_path = save_uploaded_image(logo_file, 'logos', max_size=(200, 200))
            if new_logo_path:
                restaurant.logo = new_logo_path
                flash(f'Logo上传成功: {new_logo_path}', 'success')
            else:
                flash('Logo图片上传失败，请检查文件格式和大小（最大5MB）', 'error')
        elif request.form.get('logo_url'):
            # 如果没有上传文件但有URL，使用URL
            restaurant.logo = request.form.get('logo_url', '')
        
        # 处理Banner图片上传
        banner_file = request.files.get('banner_file')
        if banner_file and banner_file.filename:
            # 删除旧的banner文件
            if restaurant.banner:
                delete_image_file(restaurant.banner)
            
            # 保存新的banner
            new_banner_path = save_uploaded_image(banner_file, 'banners', max_size=(800, 300))
            if new_banner_path:
                restaurant.banner = new_banner_path
            else:
                flash('Banner图片上传失败，请检查文件格式')
        elif request.form.get('banner_url'):
            # 如果没有上传文件但有URL，使用URL
            restaurant.banner = request.form.get('banner_url', '')
        
        db.session.commit()
        flash('餐厅信息更新成功')
        return redirect(url_for('restaurant.admin_restaurants'))
    
    return render_template('restaurant/edit.html', restaurant=restaurant)

@restaurant_bp.route('/admin')
@login_required
def admin_restaurants():
    """餐厅管理列表（管理员功能）"""
    if current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('restaurant.list_restaurants'))
    
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    keyword = request.args.get('keyword', '')
    status = request.args.get('status', '')
    
    # 构建查询
    query = Restaurant.query
    
    if keyword:
        query = query.filter(Restaurant.name.contains(keyword))
    
    if status:
        query = query.filter_by(status=status)
    
    # 分页
    pagination = query.paginate(page=page, per_page=10, error_out=False)
    restaurants = pagination.items
    
    return render_template('restaurant/admin_list.html', 
                         restaurants=restaurants,
                         pagination=pagination)

@restaurant_bp.route('/<int:restaurant_id>/toggle_status', methods=['POST'])
@login_required
def toggle_status(restaurant_id):
    """切换餐厅状态（管理员功能）"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'})
    
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status in ['open', 'closed']:
        restaurant.status = new_status
        db.session.commit()
        return jsonify({'success': True, 'message': '状态更新成功'})
    
    return jsonify({'success': False, 'message': '无效的状态'})

@restaurant_bp.route('/<int:restaurant_id>/delete')
@login_required
def delete_restaurant(restaurant_id):
    """删除餐厅（管理员功能）"""
    if current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('restaurant.list_restaurants'))
    
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    
    try:
        db.session.delete(restaurant)
        db.session.commit()
        flash('餐厅删除成功')
    except Exception as e:
        db.session.rollback()
        flash('删除失败：该餐厅可能有关联的菜品或订单')
    
    return redirect(url_for('restaurant.admin_restaurants')) 