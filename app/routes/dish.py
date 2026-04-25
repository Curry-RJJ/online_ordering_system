from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import Dish, Restaurant, Category, RestaurantChangeRequest, OrderItem
from app.cos_presign import validate_cos_web_path
from app.utils import save_uploaded_image, delete_image_file, create_image_directories
from app import db
from app.routes.restaurant import _invalidate_restaurant_cache
from sqlalchemy.orm import joinedload
import json

dish_bp = Blueprint('dish', __name__, url_prefix='/dish')

@dish_bp.route('/')
def list_dishes():
    dishes = Dish.query.all()
    return render_template('dish/list.html', dishes=dishes)

@dish_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_dish():
    # 权限检查
    if current_user.role == 'admin':
        pass
    elif current_user.role == 'merchant' and current_user.restaurant_id:
        pass
    else:
        flash('权限不足')
        return redirect(url_for('dish.list_dishes'))

    if request.method == 'POST':
        # 基本信息
        name = request.form['name']
        # BUG-12 修复：数字字段加 try/except 防止非法输入导致 500
        try:
            price = float(request.form['price'])
        except (ValueError, TypeError, KeyError):
            flash('价格格式不正确')
            return redirect(request.referrer or url_for('dish.add_dish'))
        description = request.form.get('description', '')
        restaurant_id = request.form.get('restaurant_id', type=int)
        category_id = request.form.get('category_id', type=int) or None
        ingredients = request.form.get('ingredients', '')

        # 商家管理员只能为自己的商家添加菜品
        if current_user.role == 'merchant':
            restaurant_id = current_user.restaurant_id

        # 价格信息
        try:
            original_price = float(request.form.get('original_price') or 0) or None
        except (ValueError, TypeError):
            original_price = None
        try:
            discount_rate = float(request.form.get('discount_rate') or 0) or None
        except (ValueError, TypeError):
            discount_rate = None

        # 其他信息
        try:
            rating = float(request.form.get('rating', 4.5))
        except (ValueError, TypeError):
            rating = 4.5
        try:
            sales_count = int(request.form.get('sales_count', 0))
        except (ValueError, TypeError):
            sales_count = 0
        
        # 处理菜品图片上传（浏览器直传 COS 时由隐藏域 cos_image_path 提交）
        image = ''
        cos_path = request.form.get('cos_image_path', '').strip()
        if cos_path and validate_cos_web_path(cos_path, 'dishes'):
            image = cos_path
        else:
            image_file = request.files.get('image_file')
            if image_file and image_file.filename:
                create_image_directories()
                new_image_path = save_uploaded_image(image_file, 'dishes', max_size=(600, 400))
                if new_image_path:
                    image = new_image_path
                else:
                    flash('菜品图片上传失败，请检查文件格式')
            elif request.form.get('image_url'):
                image = request.form.get('image_url', '')
        
        # 状态设置
        available = request.form.get('available') == 'on'
        is_recommended = request.form.get('is_recommended') == 'on'
        is_spicy = request.form.get('is_spicy') == 'on'

        if current_user.role == 'admin':
            # 管理员直接添加
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
            _invalidate_restaurant_cache(restaurant_id)
            flash('菜品添加成功')
            return redirect(url_for('dish.admin_dishes'))
        else:
            # 商家管理员提交审核
            change_data = {
                'name': name,
                'price': price,
                'description': description,
                'restaurant_id': restaurant_id,
                'category_id': category_id,
                'ingredients': ingredients,
                'original_price': original_price,
                'discount_rate': discount_rate,
                'rating': rating,
                'sales_count': sales_count,
                'image': image,
                'available': available,
                'is_recommended': is_recommended,
                'is_spicy': is_spicy
            }
            reason = request.form.get('change_reason', '')
            change_request = RestaurantChangeRequest(
                merchant_id=current_user.id,
                request_type='dish_add',
                restaurant_id=restaurant_id,
                change_data=json.dumps(change_data, ensure_ascii=False),
                reason=reason
            )
            db.session.add(change_request)
            db.session.commit()
            flash('菜品添加申请已提交，等待管理员审核')
            return redirect(url_for('restaurant.merchant_dashboard'))

    # 获取所有餐厅和分类
    if current_user.role == 'admin':
        restaurants = Restaurant.query.all()
    else:
        restaurants = Restaurant.query.filter_by(id=current_user.restaurant_id).all()
    
    categories = Category.query.all()
    
    return render_template('dish/add.html',
                         restaurants=restaurants,
                         categories=categories)

@dish_bp.route('/edit/<int:dish_id>', methods=['GET', 'POST'])
@login_required
def edit_dish(dish_id):
    dish = Dish.query.get_or_404(dish_id)

    # 权限检查
    if current_user.role == 'admin':
        pass
    elif current_user.role == 'merchant' and current_user.restaurant_id == dish.restaurant_id:
        pass
    else:
        flash('权限不足')
        return redirect(url_for('dish.list_dishes'))

    if request.method == 'POST':
        # 确保图片目录存在
        create_image_directories()
        
        # BUG-12 修复：数字字段加 try/except
        def _safe_float(val, default=0.0):
            try:
                return float(val) if val else default
            except (ValueError, TypeError):
                return default

        def _safe_int(val, default=0):
            try:
                return int(val) if val else default
            except (ValueError, TypeError):
                return default

        # 准备修改数据
        change_data = {
            'name': request.form['name'],
            'price': _safe_float(request.form.get('price'), 0.0),
            'description': request.form.get('description', ''),
            'category_id': request.form.get('category_id', type=int) or None,
            'ingredients': request.form.get('ingredients', ''),
            'original_price': _safe_float(request.form.get('original_price'), 0.0) or None,
            'discount_rate': _safe_float(request.form.get('discount_rate'), 0.0) or None,
            'rating': _safe_float(request.form.get('rating'), 4.5),
            'sales_count': _safe_int(request.form.get('sales_count'), 0),
            'available': request.form.get('available') == 'on',
            'is_recommended': request.form.get('is_recommended') == 'on',
            'is_spicy': request.form.get('is_spicy') == 'on'
        }
        
        # 处理图片上传（浏览器直传 COS 时由隐藏域 cos_image_path 提交）
        cos_path = request.form.get('cos_image_path', '').strip()
        if cos_path and validate_cos_web_path(cos_path, 'dishes'):
            change_data['image'] = cos_path
        else:
            image_file = request.files.get('image_file')
            if image_file and image_file.filename:
                new_image_path = save_uploaded_image(image_file, 'dishes', max_size=(600, 400))
                if new_image_path:
                    change_data['image'] = new_image_path
            elif request.form.get('image_url'):
                change_data['image'] = request.form.get('image_url', '')
        
        if current_user.role == 'admin':
            # 管理员直接修改
            # 如果有新图片，删除旧图片
            if 'image' in change_data and change_data['image'] != dish.image:
                if dish.image and not dish.image.startswith('http'):
                    delete_image_file(dish.image)
            
            # 应用所有修改
            for key, value in change_data.items():
                setattr(dish, key, value)

            db.session.commit()
            _invalidate_restaurant_cache(dish.restaurant_id)
            flash('菜品修改成功')
            return redirect(url_for('dish.admin_dishes'))
        else:
            # 商家管理员提交审核
            reason = request.form.get('change_reason', '')
            change_request = RestaurantChangeRequest(
                merchant_id=current_user.id,
                request_type='dish_edit',
                restaurant_id=dish.restaurant_id,
                dish_id=dish_id,
                change_data=json.dumps(change_data, ensure_ascii=False),
                reason=reason
            )
            db.session.add(change_request)
            db.session.commit()
            flash('菜品修改申请已提交，等待管理员审核')
            return redirect(url_for('restaurant.merchant_dashboard'))

    # 获取所有餐厅和分类
    if current_user.role == 'admin':
        restaurants = Restaurant.query.all()
    else:
        restaurants = Restaurant.query.filter_by(id=current_user.restaurant_id).all()
    
    categories = Category.query.all()
    
    return render_template('dish/edit.html', 
                         dish=dish,
                         restaurants=restaurants,
                         categories=categories)

@dish_bp.route('/delete/<int:dish_id>')
@login_required
def delete_dish(dish_id):
    dish = Dish.query.get_or_404(dish_id)
    
    # 权限检查
    if current_user.role == 'admin':
        pass
    elif current_user.role == 'merchant' and current_user.restaurant_id == dish.restaurant_id:
        pass
    else:
        flash('权限不足')
        return redirect(url_for('dish.list_dishes'))

    # 检查是否有关联的购物车项
    cart_items_count = dish.cart_items.count()
    if cart_items_count > 0:
        flash(f'无法删除：该菜品在 {cart_items_count} 个购物车中，请先清理相关购物车项', 'danger')
        return redirect(url_for('dish.admin_dishes') if current_user.role == 'admin' else url_for('restaurant.merchant_dashboard'))
    
    # 检查是否有关联的订单项
    order_items_count = dish.order_items.count()
    if order_items_count > 0:
        flash(f'无法删除：该菜品已有 {order_items_count} 个订单记录，建议使用下架功能而不是删除', 'danger')
        return redirect(url_for('dish.admin_dishes') if current_user.role == 'admin' else url_for('restaurant.merchant_dashboard'))
    
    if current_user.role == 'admin':
        # 管理员直接删除
        rid = dish.restaurant_id
        try:
            db.session.delete(dish)
            db.session.commit()
            _invalidate_restaurant_cache(rid)
            flash('菜品已删除', 'success')
        except Exception as e:
            db.session.rollback()
            flash('删除失败，请联系系统管理员', 'danger')
        return redirect(url_for('dish.admin_dishes'))
    else:
        # 商家管理员提交删除审核
        reason = f'删除菜品：{dish.name}'
        change_request = RestaurantChangeRequest(
            merchant_id=current_user.id,
            request_type='dish_delete',
            restaurant_id=dish.restaurant_id,
            dish_id=dish_id,
            change_data=json.dumps({'dish_id': dish_id}),
            reason=reason
        )
        db.session.add(change_request)
        db.session.commit()
        flash('菜品删除申请已提交，等待管理员审核')
        return redirect(url_for('restaurant.merchant_dashboard'))

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
    
    # 构建查询（预加载餐厅与分类，避免管理列表模板 N+1）
    query = Dish.query.options(
        joinedload(Dish.restaurant),
        joinedload(Dish.category),
    )

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
        _invalidate_restaurant_cache(dish.restaurant_id)
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
    rid = dish.restaurant_id
    
    try:
        # 保留历史订单项，仅将 dish_id 置 null
        OrderItem.query.filter_by(dish_id=dish_id).update({'dish_id': None})
        # 删除菜品（购物车项通过 cascade 自动删除）
        db.session.delete(dish)
        db.session.commit()
        _invalidate_restaurant_cache(rid)
        flash('菜品已强制删除，历史订单记录已保留', 'success')
    except Exception as e:
        db.session.rollback()
        flash('强制删除失败，请联系系统管理员', 'danger')
        
    return redirect(url_for('dish.admin_dishes'))

@dish_bp.route('/merchant/<int:dish_id>/toggle_available', methods=['POST'])
@login_required
def merchant_toggle_available(dish_id):
    """商家管理员切换菜品上下架状态"""
    dish = Dish.query.get_or_404(dish_id)
    
    # 权限检查：只能操作自己商家的菜品
    if current_user.role != 'merchant' or current_user.restaurant_id != dish.restaurant_id:
        return jsonify({'success': False, 'message': '权限不足'})
    
    data = request.get_json()
    new_status = data.get('available')
    
    if new_status is None:
        return jsonify({'success': False, 'message': '无效的状态'})
    
    dish.available = new_status
    db.session.commit()
    _invalidate_restaurant_cache(dish.restaurant_id)
    
    status_text = '已上架' if new_status else '已下架'
    return jsonify({'success': True, 'message': f'菜品{status_text}'})
