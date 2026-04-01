from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, session
from flask_login import login_required, current_user
from app.models import Restaurant, Dish, Category, Review, CartItem, RestaurantChangeRequest, OrderItem
from app.utils import (
    save_uploaded_image,
    delete_image_file,
    create_image_directories,
    haversine,
    is_outside_haversine_bbox,
)
from app import db, cache
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload
import json

# ──────────────────────────────────────────────
# 缓存辅助函数
# ──────────────────────────────────────────────

_LIST_VER_KEY = 'restaurant_list_ver'
# 菜单聚合缓存版本：单店 bump `menu_ver:{id}`；影响全站菜单语义时 bump `menu_ver_global`（如菜品分类变更）
_MENU_VER_GLOBAL = 'menu_ver_global'


def _to_restaurant_dict(r):
    return dict(id=r.id, name=r.name, description=r.description, logo=r.logo,
                banner=r.banner, address=r.address, phone=r.phone,
                cuisine_type=r.cuisine_type, business_hours=r.business_hours,
                delivery_fee=r.delivery_fee, min_order=r.min_order,
                rating=r.rating, review_count=r.review_count,
                status=r.status, is_active=r.is_active,
                latitude=r.latitude, longitude=r.longitude)


def _to_category_dict(c):
    return dict(id=c.id, name=c.name, icon=c.icon, sort_order=c.sort_order)


def _to_dish_dict(d):
    return dict(id=d.id, name=d.name, description=d.description,
                price=d.price, original_price=d.original_price,
                discount_rate=d.discount_rate, image=d.image,
                ingredients=d.ingredients, sales_count=d.sales_count,
                rating=d.rating, is_recommended=d.is_recommended,
                is_spicy=d.is_spicy, available=d.available,
                restaurant_id=d.restaurant_id, category_id=d.category_id)


def _get_list_version():
    v = cache.get(_LIST_VER_KEY)
    if v is None:
        v = 1
        cache.set(_LIST_VER_KEY, v, timeout=0)
    return v


def restaurant_menu_cache_key(restaurant_id):
    """详情页与 API 共用的菜单聚合缓存键（版本号参与键名，失效时 bump 而非依赖模糊 delete）。"""
    local = cache.get(f'menu_ver:{restaurant_id}') or 0
    glo = cache.get(_MENU_VER_GLOBAL) or 0
    return f'restaurant_menu:{restaurant_id}:{local}:{glo}'


def restaurant_ajax_menu_cache_key(restaurant_id, category_id=None):
    """分类 AJAX 菜单缓存键（含 category_id 维度）。"""
    local = cache.get(f'menu_ver:{restaurant_id}') or 0
    glo = cache.get(_MENU_VER_GLOBAL) or 0
    cat = category_id if category_id is not None else 'all'
    return f'restaurant_menu_ajax:{restaurant_id}:{cat}:{local}:{glo}'


def _invalidate_restaurant_cache(restaurant_id=None):
    """使餐厅菜单/列表相关缓存失效：单店 bump 本地版本；全局 bump 影响所有店菜单语义（如菜品分类 CRUD）。"""
    if restaurant_id:
        k = f'menu_ver:{restaurant_id}'
        cache.set(k, (cache.get(k) or 0) + 1, timeout=0)
    else:
        cache.set(_MENU_VER_GLOBAL, (cache.get(_MENU_VER_GLOBAL) or 0) + 1, timeout=0)
    v = cache.get(_LIST_VER_KEY) or 0
    cache.set(_LIST_VER_KEY, v + 1, timeout=0)

restaurant_bp = Blueprint('restaurant', __name__, url_prefix='/restaurant')

@restaurant_bp.route('/set-location', methods=['POST'])
@login_required
def set_user_location():
    """更新 session 中的用户位置（列表页「切换位置」按钮调用）"""
    data = request.get_json() or {}
    try:
        lat = float(data['lat'])
        lng = float(data['lng'])
    except (KeyError, TypeError, ValueError):
        return jsonify({'success': False, 'message': '坐标无效'}), 400
    session['user_lat']     = lat
    session['user_lng']     = lng
    session['user_address'] = data.get('address', '')
    return jsonify({'success': True})


@restaurant_bp.route('/')
def list_restaurants():
    """餐厅列表页面"""
    try:
        keyword     = request.args.get('keyword', '')
        category_id = request.args.get('category', type=int)
        sort_by     = request.args.get('sort', 'rating')

        # 读取用户位置（首次登录时已写入 session）
        user_lat     = session.get('user_lat')
        user_lng     = session.get('user_lng')
        user_address = session.get('user_address', '')
        has_location = (user_lat is not None and user_lng is not None)

        # 无位置时 distance 排序无意义，回退到评分（BUG-13 修复）
        if sort_by == 'distance' and not has_location:
            sort_by = 'rating'

        # 有位置时每人结果不同，不走公共缓存
        cache_key = None
        cached    = None
        if not has_location:
            version   = _get_list_version()
            cache_key = f'restaurant_list_v{version}:{keyword}:{category_id}:{sort_by}'
            cached    = cache.get(cache_key)

        if cached is None:
            query = Restaurant.query.filter_by(status='open')

            if keyword:
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
                query = query.join(Dish).join(Category).filter(Category.id == category_id)

            # 有位置时先不排序，后面按距离处理；无位置时数据库排序
            if not has_location:
                if sort_by == 'rating':
                    query = query.order_by(Restaurant.rating.desc())
                elif sort_by == 'sales':
                    query = query.order_by(Restaurant.review_count.desc())
                else:
                    query = query.order_by(Restaurant.created_at.desc())

            restaurants_raw  = query.distinct().all()
            categories_raw   = Category.query.order_by(Category.sort_order).all()

            # 计算全站平均评分
            rated = [r for r in restaurants_raw if r.review_count and r.review_count > 0]
            avg_rating = round(sum(r.rating for r in rated) / len(rated), 1) if rated else None

            if has_location:
                # 计算距离，过滤 > 10 km；先矩形边界预筛再 Haversine，减少大列表下的三角运算
                result = []
                for r in restaurants_raw:
                    d = _to_restaurant_dict(r)
                    if r.latitude and r.longitude:
                        if is_outside_haversine_bbox(
                            user_lat, user_lng, r.latitude, r.longitude, 10.0
                        ):
                            continue
                        dist = haversine(user_lat, user_lng, r.latitude, r.longitude)
                        if dist > 10.0:
                            continue        # 超出范围，丢弃
                        d['distance'] = round(dist, 1)
                    else:
                        d['distance'] = None  # 无坐标餐厅仍显示，排在末尾
                    result.append(d)

                # 按选择的维度排序
                if sort_by == 'distance':
                    result.sort(key=lambda x: (x['distance'] is None, x['distance'] or 999))
                elif sort_by == 'rating':
                    result.sort(key=lambda x: -(x['rating'] or 0))
                elif sort_by == 'sales':
                    result.sort(key=lambda x: -(x['review_count'] or 0))

                restaurants_list = result
            else:
                restaurants_list = [_to_restaurant_dict(r) for r in restaurants_raw]
                for r in restaurants_list:
                    r['distance'] = None

            cached = {
                'restaurants': restaurants_list,
                'categories':  [_to_category_dict(c) for c in categories_raw],
                'avg_rating':  avg_rating,
            }
            # 无位置时写入公共缓存
            if cache_key:
                cache.set(cache_key, cached, timeout=300)

        return render_template('restaurant/list.html',
                               restaurants=cached['restaurants'],
                               categories=cached['categories'],
                               avg_rating=cached.get('avg_rating'),
                               keyword=keyword,
                               current_category=category_id,
                               sort_by=sort_by,
                               user_address=user_address,
                               has_location=has_location)
    except Exception as e:
        current_app.logger.error(f"Error in list_restaurants: {e}")
        return render_template('errors/500.html'), 500

@restaurant_bp.route('/<int:restaurant_id>')
def restaurant_detail(restaurant_id):
    """餐厅详情页面"""
    menu_cache_key = restaurant_menu_cache_key(restaurant_id)
    menu_cached = cache.get(menu_cache_key)

    if menu_cached is None:
        restaurant_obj = Restaurant.query.get_or_404(restaurant_id)

        categories_raw = db.session.query(Category).join(Dish).filter(
            Dish.restaurant_id == restaurant_id,
            Dish.available == True
        ).distinct().all()

        recommended_raw = Dish.query.filter_by(
            restaurant_id=restaurant_id,
            is_recommended=True,
            available=True
        ).limit(6).all()

        dishes_by_category = {}
        for cat in categories_raw:
            dishes = Dish.query.filter_by(
                restaurant_id=restaurant_id,
                category_id=cat.id,
                available=True
            ).order_by(Dish.sales_count.desc()).all()
            dishes_by_category[cat.name] = [_to_dish_dict(d) for d in dishes]

        menu_cached = {
            'restaurant': _to_restaurant_dict(restaurant_obj),
            'categories': [_to_category_dict(c) for c in categories_raw],
            'recommended_dishes': [_to_dish_dict(d) for d in recommended_raw],
            'dishes_by_category': dishes_by_category,
        }
        cache.set(menu_cache_key, menu_cached, timeout=600)

    # 评价实时获取（数量少、时效性强）
    reviews = Review.query.options(joinedload(Review.user))\
                          .filter_by(restaurant_id=restaurant_id)\
                          .order_by(Review.created_at.desc())\
                          .limit(10).all()

    # 购物车数量为用户私有数据，不缓存
    cart_count = 0
    if current_user.is_authenticated:
        cart_count = CartItem.query.filter_by(user_id=current_user.id)\
                                   .join(Dish)\
                                   .filter(Dish.restaurant_id == restaurant_id)\
                                   .count()

    return render_template('restaurant/detail.html',
                           restaurant=menu_cached['restaurant'],
                           categories=menu_cached['categories'],
                           recommended_dishes=menu_cached['recommended_dishes'],
                           dishes_by_category=menu_cached['dishes_by_category'],
                           reviews=reviews,
                           cart_count=cart_count)

@restaurant_bp.route('/<int:restaurant_id>/menu')
def restaurant_menu(restaurant_id):
    """餐厅菜单页面（AJAX加载）"""
    category_id = request.args.get('category_id', type=int)
    ajax_cache_key = restaurant_ajax_menu_cache_key(restaurant_id, category_id)
    cached = cache.get(ajax_cache_key)

    if cached is None:
        Restaurant.query.get_or_404(restaurant_id)
        query = Dish.query.filter_by(restaurant_id=restaurant_id, available=True)
        if category_id:
            query = query.filter_by(category_id=category_id)
        dishes = query.order_by(Dish.sales_count.desc()).all()
        cached = {
            'dishes': [{
                'id': d.id, 'name': d.name, 'description': d.description,
                'price': d.price, 'original_price': d.original_price,
                'image': d.image, 'sales_count': d.sales_count,
                'rating': d.rating, 'is_recommended': d.is_recommended,
                'is_spicy': d.is_spicy
            } for d in dishes]
        }
        cache.set(ajax_cache_key, cached, timeout=600)

    return jsonify(cached)

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
        
        # BUG-12 修复：对数字字段加 try/except，防止非法输入导致 500
        try:
            delivery_fee = float(request.form.get('delivery_fee', 0))
        except (ValueError, TypeError):
            delivery_fee = 0.0
        try:
            min_order = float(request.form.get('min_order', 0))
        except (ValueError, TypeError):
            min_order = 0.0
        try:
            rating = float(request.form.get('rating', 4.5))
            rating = max(0.0, min(5.0, rating))
        except (ValueError, TypeError):
            rating = 4.5
        try:
            review_count = int(request.form.get('review_count', 0))
        except (ValueError, TypeError):
            review_count = 0

        # 解析坐标，必须选点
        try:
            latitude  = float(request.form['latitude'])
            longitude = float(request.form['longitude'])
        except (KeyError, ValueError, TypeError):
            flash('请在地图上选择餐厅位置（必填）', 'error')
            return redirect(url_for('restaurant.add_restaurant'))

        # 创建餐厅对象
        restaurant = Restaurant(
            name=request.form['name'],
            description=request.form.get('description', ''),
            address=request.form.get('address', ''),
            phone=request.form.get('phone', ''),
            business_hours=request.form.get('business_hours', ''),
            delivery_fee=delivery_fee,
            min_order=min_order,
            cuisine_type=request.form.get('cuisine_type', ''),
            rating=rating,
            review_count=review_count,
            status='open' if request.form.get('is_open') == 'on' else 'closed',
            logo=logo_path,
            banner=banner_path,
            latitude=latitude,
            longitude=longitude,
        )
        
        db.session.add(restaurant)
        db.session.commit()
        _invalidate_restaurant_cache()
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
        
        # BUG-12 修复：对 delivery_fee / min_order 加 try/except
        try:
            _delivery_fee = float(request.form.get('delivery_fee', 0))
        except (ValueError, TypeError):
            _delivery_fee = 0.0
        try:
            _min_order = float(request.form.get('min_order', 0))
        except (ValueError, TypeError):
            _min_order = 0.0

        # 解析可选坐标
        try:
            _lat = float(request.form['latitude'])  if request.form.get('latitude')  else None
            _lng = float(request.form['longitude']) if request.form.get('longitude') else None
        except (ValueError, TypeError):
            _lat = _lng = None

        # 准备修改数据
        change_data = {
            'name': request.form['name'],
            'description': request.form.get('description', ''),
            'address': request.form.get('address', ''),
            'phone': request.form.get('phone', ''),
            'business_hours': request.form.get('business_hours', ''),
            'delivery_fee': _delivery_fee,
            'min_order': _min_order,
        }
        if _lat is not None:
            change_data['latitude']  = _lat
        if _lng is not None:
            change_data['longitude'] = _lng
        
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
            if 'latitude' in change_data:
                restaurant.latitude  = change_data['latitude']
            if 'longitude' in change_data:
                restaurant.longitude = change_data['longitude']
            try:
                restaurant.rating = float(request.form.get('rating', 4.5))
            except (ValueError, TypeError):
                pass  # 保留原值
            
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
            _invalidate_restaurant_cache(restaurant_id)
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
    
    # BUG-16 修复：支持 busy（忙碌）状态
    if new_status in ['open', 'closed', 'busy']:
        restaurant.status = new_status
        db.session.commit()
        _invalidate_restaurant_cache(restaurant_id)
        return jsonify({'success': True, 'message': '状态更新成功'})

    return jsonify({'success': False, 'message': '无效的状态，允许值：open / closed / busy'})

@restaurant_bp.route('/<int:restaurant_id>/delete')
@login_required
def delete_restaurant(restaurant_id):
    """删除餐厅（管理员功能）"""
    if current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('restaurant.list_restaurants'))
    
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    
    try:
        rid = restaurant.id
        db.session.delete(restaurant)
        db.session.commit()
        _invalidate_restaurant_cache(rid)
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
                # 保留历史订单项，仅将 dish_id 置 null
                OrderItem.query.filter_by(dish_id=dish.id).update({'dish_id': None})
                db.session.delete(dish)
        
        # 更新请求状态
        change_request.status = 'approved'
        change_request.reviewed_at = datetime.utcnow()
        change_request.reviewer_id = current_user.id
        
        db.session.commit()
        _invalidate_restaurant_cache(change_request.restaurant_id)
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
    
    # BUG-16 修复：商家也可以设置 busy（忙碌）状态
    if new_status not in ['open', 'closed', 'busy']:
        return jsonify({'success': False, 'message': '无效的状态，允许值：open / closed / busy'})

    restaurant.status = new_status
    db.session.commit()
    _invalidate_restaurant_cache(restaurant_id)
    status_text = {'open': '营业中', 'closed': '已打烊', 'busy': '忙碌中'}.get(new_status, new_status)
    return jsonify({'success': True, 'message': f'商家状态已更新为：{status_text}'}) 