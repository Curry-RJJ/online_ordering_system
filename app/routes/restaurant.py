from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models import Restaurant, Dish, Category, Review, CartItem, RestaurantChangeRequest
from app.utils import save_uploaded_image, delete_image_file, create_image_directories
from app import db
from sqlalchemy import func, or_
import json

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
        # 确保图片目录存在
        create_image_directories()
        
        # 处理Logo上传
        logo_path = ''
        logo_file = request.files.get('logo')
        if logo_file and logo_file.filename:
            new_logo_path = save_uploaded_image(logo_file, 'logos', max_size=(200, 200))
            if new_logo_path:
                logo_path = new_logo_path
                flash(f'Logo上传成功: {new_logo_path}', 'success')
            else:
                flash('Logo上传失败，请检查文件格式', 'warning')
        
        # 处理Banner上传
        banner_path = ''
        banner_file = request.files.get('banner')
        if banner_file and banner_file.filename:
            new_banner_path = save_uploaded_image(banner_file, 'banners', max_size=(800, 300))
            if new_banner_path:
                banner_path = new_banner_path
                flash(f'横幅上传成功: {new_banner_path}', 'success')
            else:
                flash('横幅上传失败，请检查文件格式', 'warning')
        
        # 创建餐厅对象
        restaurant = Restaurant(
            name=request.form['name'],
            description=request.form.get('description', ''),
            address=request.form.get('address', ''),
            phone=request.form.get('phone', ''),
            business_hours=request.form.get('business_hours', ''),
            delivery_fee=float(request.form.get('delivery_fee', 0)),
            min_order=float(request.form.get('min_order', 0)),
            cuisine_type=request.form.get('cuisine_type', ''),
            rating=float(request.form.get('rating', 4.5)),
            review_count=int(request.form.get('review_count', 0)),
            status='open' if request.form.get('is_open') == 'on' else 'closed',
            logo=logo_path,
            banner=banner_path
        )
        
        db.session.add(restaurant)
        db.session.commit()
        
        flash('餐厅添加成功', 'success')
        return redirect(url_for('restaurant.admin_restaurants'))
    
    return render_template('restaurant/add.html')

@restaurant_bp.route('/<int:restaurant_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_restaurant(restaurant_id):
    """编辑餐厅（管理员和商家管理员功能）"""
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    
    # 权限检查
    if current_user.role == 'admin':
        # 管理员可以直接编辑
        pass
    elif current_user.role == 'merchant' and current_user.restaurant_id == restaurant_id:
        # 商家管理员只能编辑自己的商家，且需要审核
        pass
    else:
        flash('权限不足')
        return redirect(url_for('restaurant.list_restaurants'))
    
    if request.method == 'POST':
        # 确保图片目录存在
        create_image_directories()
        
        # 准备修改数据
        change_data = {
            'name': request.form['name'],
            'description': request.form.get('description', ''),
            'address': request.form.get('address', ''),
            'phone': request.form.get('phone', ''),
            'business_hours': request.form.get('business_hours', ''),
            'delivery_fee': float(request.form.get('delivery_fee', 0)),
            'min_order': float(request.form.get('min_order', 0)),
        }
        
        # 处理图片上传（商家管理员也需要上传图片）
        logo_file = request.files.get('logo_file')
        if logo_file and logo_file.filename:
            new_logo_path = save_uploaded_image(logo_file, 'logos', max_size=(200, 200))
            if new_logo_path:
                change_data['logo'] = new_logo_path
        elif request.form.get('logo_url'):
            change_data['logo'] = request.form.get('logo_url', '')
        
        banner_file = request.files.get('banner_file')
        if banner_file and banner_file.filename:
            new_banner_path = save_uploaded_image(banner_file, 'banners', max_size=(800, 300))
            if new_banner_path:
                change_data['banner'] = new_banner_path
        elif request.form.get('banner_url'):
            change_data['banner'] = request.form.get('banner_url', '')
        
        if current_user.role == 'admin':
            # 管理员直接修改
            restaurant.name = change_data['name']
            restaurant.description = change_data['description']
            restaurant.address = change_data['address']
            restaurant.phone = change_data['phone']
            restaurant.business_hours = change_data['business_hours']
            restaurant.delivery_fee = change_data['delivery_fee']
            restaurant.min_order = change_data['min_order']
            restaurant.status = request.form.get('status', 'open')
            restaurant.rating = float(request.form.get('rating', 4.5))
            
            # 应用图片修改
            if 'logo' in change_data:
                if restaurant.logo and not restaurant.logo.startswith('http'):
                    delete_image_file(restaurant.logo)
                restaurant.logo = change_data['logo']
                flash(f'Logo上传成功: {change_data["logo"]}', 'success')
            
            if 'banner' in change_data:
                if restaurant.banner and not restaurant.banner.startswith('http'):
                    delete_image_file(restaurant.banner)
                restaurant.banner = change_data['banner']
            
            db.session.commit()
            flash('餐厅信息更新成功')
            return redirect(url_for('restaurant.admin_restaurants'))
        else:
            # 商家管理员提交审核请求
            reason = request.form.get('change_reason', '')
            change_request = RestaurantChangeRequest(
                merchant_id=current_user.id,
                request_type='restaurant_edit',
                restaurant_id=restaurant_id,
                change_data=json.dumps(change_data, ensure_ascii=False),
                reason=reason
            )
            db.session.add(change_request)
            db.session.commit()
            flash('修改申请已提交，等待管理员审核')
            return redirect(url_for('restaurant.merchant_dashboard'))
    
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

@restaurant_bp.route('/merchant/dashboard')
@login_required
def merchant_dashboard():
    """商家管理员仪表板"""
    if current_user.role != 'merchant':
        flash('权限不足')
        return redirect(url_for('restaurant.list_restaurants'))
    
    if not current_user.restaurant_id:
        flash('您还未被分配商家，请先申请管理商家')
        return redirect(url_for('auth.apply_restaurant'))
    
    restaurant = Restaurant.query.get_or_404(current_user.restaurant_id)
    
    # 获取待审核的修改请求
    pending_requests = RestaurantChangeRequest.query.filter_by(
        merchant_id=current_user.id,
        status='pending'
    ).order_by(RestaurantChangeRequest.timestamp.desc()).all()
    
    # 获取所有修改请求历史
    all_requests = RestaurantChangeRequest.query.filter_by(
        merchant_id=current_user.id
    ).order_by(RestaurantChangeRequest.timestamp.desc()).limit(20).all()
    
    # 获取商家的菜品
    dishes = Dish.query.filter_by(restaurant_id=current_user.restaurant_id).all()
    
    return render_template('merchant/dashboard.html',
                         restaurant=restaurant,
                         pending_requests=pending_requests,
                         all_requests=all_requests,
                         dishes=dishes)

@restaurant_bp.route('/admin/change_requests')
@login_required
def admin_change_requests():
    """管理员审核商家修改请求"""
    if current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('restaurant.list_restaurants'))
    
    # 获取所有待审核的请求
    pending_requests = RestaurantChangeRequest.query.filter_by(
        status='pending'
    ).order_by(RestaurantChangeRequest.timestamp.desc()).all()
    
    # 获取已处理的请求
    processed_requests = RestaurantChangeRequest.query.filter(
        RestaurantChangeRequest.status.in_(['approved', 'rejected'])
    ).order_by(RestaurantChangeRequest.reviewed_at.desc()).limit(50).all()
    
    return render_template('admin_change_requests.html',
                         pending_requests=pending_requests,
                         processed_requests=processed_requests)

@restaurant_bp.route('/admin/change_requests/<int:request_id>/approve', methods=['POST'])
@login_required
def approve_change_request(request_id):
    """审核通过修改请求"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'})
    
    change_request = RestaurantChangeRequest.query.get_or_404(request_id)
    
    if change_request.status != 'pending':
        return jsonify({'success': False, 'message': '该请求已处理'})
    
    try:
        from datetime import datetime
        
        # 根据请求类型应用修改
        if change_request.request_type == 'restaurant_edit':
            restaurant = Restaurant.query.get(change_request.restaurant_id)
            if restaurant:
                change_data = json.loads(change_request.change_data)
                
                # 处理图片更新，删除旧图片
                if 'logo' in change_data and change_data['logo'] != restaurant.logo:
                    if restaurant.logo and not restaurant.logo.startswith('http'):
                        delete_image_file(restaurant.logo)
                
                if 'banner' in change_data and change_data['banner'] != restaurant.banner:
                    if restaurant.banner and not restaurant.banner.startswith('http'):
                        delete_image_file(restaurant.banner)
                
                # 应用所有修改
                for key, value in change_data.items():
                    if hasattr(restaurant, key):
                        setattr(restaurant, key, value)
        
        elif change_request.request_type == 'dish_add':
            change_data = json.loads(change_request.change_data)
            new_dish = Dish(**change_data)
            db.session.add(new_dish)
        
        elif change_request.request_type == 'dish_edit':
            dish = Dish.query.get(change_request.dish_id)
            if dish:
                change_data = json.loads(change_request.change_data)
                
                # 处理图片更新，删除旧图片
                if 'image' in change_data and change_data['image'] != dish.image:
                    if dish.image and not dish.image.startswith('http'):
                        delete_image_file(dish.image)
                
                # 应用所有修改
                for key, value in change_data.items():
                    if hasattr(dish, key):
                        setattr(dish, key, value)
        
        elif change_request.request_type == 'dish_delete':
            dish = Dish.query.get(change_request.dish_id)
            if dish:
                db.session.delete(dish)
        
        # 更新请求状态
        change_request.status = 'approved'
        change_request.reviewed_at = datetime.utcnow()
        change_request.reviewer_id = current_user.id
        
        db.session.commit()
        return jsonify({'success': True, 'message': '审核通过'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'审核失败: {str(e)}'})

@restaurant_bp.route('/admin/change_requests/<int:request_id>/reject', methods=['POST'])
@login_required
def reject_change_request(request_id):
    """拒绝修改请求"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'})
    
    change_request = RestaurantChangeRequest.query.get_or_404(request_id)
    
    if change_request.status != 'pending':
        return jsonify({'success': False, 'message': '该请求已处理'})
    
    try:
        from datetime import datetime
        
        # 如果是餐厅修改请求且包含图片，删除已上传的图片文件
        if change_request.request_type == 'restaurant_edit':
            change_data = json.loads(change_request.change_data)
            if 'logo' in change_data and not change_data['logo'].startswith('http'):
                delete_image_file(change_data['logo'])
            if 'banner' in change_data and not change_data['banner'].startswith('http'):
                delete_image_file(change_data['banner'])
        
        # 如果是添加菜品请求且包含图片，删除图片
        elif change_request.request_type == 'dish_add':
            change_data = json.loads(change_request.change_data)
            if 'image' in change_data and not change_data['image'].startswith('http'):
                delete_image_file(change_data['image'])
        
        # 如果是编辑菜品请求且包含图片，删除图片
        elif change_request.request_type == 'dish_edit':
            change_data = json.loads(change_request.change_data)
            if 'image' in change_data and not change_data['image'].startswith('http'):
                delete_image_file(change_data['image'])
        
        change_request.status = 'rejected'
        change_request.reviewed_at = datetime.utcnow()
        change_request.reviewer_id = current_user.id
        
        db.session.commit()
        return jsonify({'success': True, 'message': '已拒绝'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})

@restaurant_bp.route('/merchant/<int:restaurant_id>/toggle_status', methods=['POST'])
@login_required
def merchant_toggle_status(restaurant_id):
    """商家管理员切换营业状态"""
    if current_user.role != 'merchant' or current_user.restaurant_id != restaurant_id:
        return jsonify({'success': False, 'message': '权限不足'})
    
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status not in ['open', 'closed']:
        return jsonify({'success': False, 'message': '无效的状态'})
    
    restaurant.status = new_status
    db.session.commit()
    
    status_text = '营业中' if new_status == 'open' else '已打烊'
    return jsonify({'success': True, 'message': f'商家状态已更新为：{status_text}'}) 