from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, AdminApplication, MerchantApplication, Address, Restaurant
from app import db
from sqlalchemy.exc import IntegrityError

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            hashed_pw = generate_password_hash(password)
            new_user = User(username=username, password=hashed_pw)
            db.session.add(new_user)
            db.session.commit()
            flash('注册成功，请登录')
            return redirect(url_for('auth.login'))
        except IntegrityError:
            db.session.rollback()
            flash('用户名已存在')
            return redirect(url_for('auth.register'))

    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('登录成功')
            # 获取登录前想要访问的页面
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            # 默认跳转到餐厅列表（主页）
            return redirect(url_for('restaurant.list_restaurants'))
        else:
            flash('用户名或密码错误')
            return redirect(url_for('auth.login'))

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已退出登录')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form.get('email')
        phone = request.form.get('phone')
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != current_user.id:
            flash('用户名已被占用')
            return redirect(url_for('auth.profile'))
        
        current_user.username = username
        current_user.email = email
        current_user.phone = phone
        
        if new_password:
            if not old_password or not check_password_hash(current_user.password, old_password):
                flash('原密码错误')
                return redirect(url_for('auth.profile'))
            current_user.password = generate_password_hash(new_password)
        
        db.session.commit()
        flash('资料更新成功')
        return redirect(url_for('auth.profile'))
    
    # 获取用户地址
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    
    # 获取用户的管理员申请记录
    admin_applications = AdminApplication.query.filter_by(user_id=current_user.id).order_by(
        AdminApplication.timestamp.desc()
    ).all()
    
    # 获取用户的商家申请记录
    merchant_applications = MerchantApplication.query.filter_by(user_id=current_user.id).order_by(
        MerchantApplication.timestamp.desc()
    ).all()
    
    return render_template('auth/profile.html', 
                         user=current_user, 
                         addresses=addresses,
                         admin_applications=admin_applications,
                         merchant_applications=merchant_applications)

@auth_bp.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('restaurant.list_restaurants'))
    
    users = User.query.all()
    return render_template('auth/admin_users.html', users=users)

@auth_bp.route('/admin/users/<int:user_id>/delete')
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('restaurant.list_restaurants'))
    
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('不能删除自己的账户')
        return redirect(url_for('auth.admin_users'))
    
    db.session.delete(user)
    db.session.commit()
    flash('用户已删除')
    return redirect(url_for('auth.admin_users'))

@auth_bp.route('/admin/users/<int:user_id>/toggle_role')
@login_required
def toggle_user_role(user_id):
    if current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('restaurant.list_restaurants'))
    
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('不能修改自己的权限')
        return redirect(url_for('auth.admin_users'))
    
    user.role = 'admin' if user.role == 'user' else 'user'
    db.session.commit()
    flash(f'用户 {user.username} 的角色已更新为 {user.role}')
    return redirect(url_for('auth.admin_users'))

@auth_bp.route('/admin/users/<int:user_id>/change_role', methods=['POST'])
@login_required
def change_user_role(user_id):
    """管理员修改用户角色（支持选择具体角色）"""
    if current_user.role != 'admin':
        flash('权限不足', 'danger')
        return redirect(url_for('restaurant.list_restaurants'))
    
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('不能修改自己的权限', 'warning')
        return redirect(url_for('auth.admin_users'))
    
    new_role = request.form.get('new_role')
    
    # 验证角色有效性
    if new_role not in ['user', 'merchant', 'admin']:
        flash('无效的角色类型', 'danger')
        return redirect(url_for('auth.admin_users'))
    
    # 角色名称映射
    role_names = {
        'user': '普通用户',
        'merchant': '商家管理员',
        'admin': '管理员'
    }
    
    old_role_name = role_names.get(user.role, user.role)
    new_role_name = role_names.get(new_role, new_role)
    
    # 如果角色没有变化
    if user.role == new_role:
        flash(f'用户 {user.username} 已经是{new_role_name}了', 'info')
        return redirect(url_for('auth.admin_users'))
    
    # 如果从商家管理员切换到其他角色，清除餐厅绑定
    if user.role == 'merchant' and new_role != 'merchant':
        old_restaurant = None
        if user.restaurant_id:
            from app.models import Restaurant
            old_restaurant = Restaurant.query.get(user.restaurant_id)
        user.restaurant_id = None
    
    # 更新角色
    user.role = new_role
    db.session.commit()
    
    # 构建提示信息
    message = f'用户 {user.username} 的角色已从「{old_role_name}」更新为「{new_role_name}」'
    
    # 如果清除了餐厅绑定，添加提示
    if user.role != 'merchant' and old_role_name == '商家管理员' and 'old_restaurant' in locals() and old_restaurant:
        message += f'，已解除与餐厅「{old_restaurant.name}」的绑定'
    
    flash(message, 'success')
    return redirect(url_for('auth.admin_users'))

@auth_bp.route('/apply_admin', methods=['GET', 'POST'])
@login_required
def apply_admin():
    """申请管理员或商家管理员"""
    if request.method == 'POST':
        application_type = request.form.get('application_type', 'admin')  # admin/merchant
        reason = request.form.get('reason')
        
        # 检查是否已有待处理的申请
        existing = AdminApplication.query.filter_by(
            user_id=current_user.id, 
            status='pending',
            application_type=application_type
        ).first()
        
        if existing:
            flash('你已有待处理的申请，请等待审核。')
            return redirect(url_for('auth.profile'))

        application = AdminApplication(
            user_id=current_user.id, 
            reason=reason,
            application_type=application_type
        )
        db.session.add(application)
        db.session.commit()
        
        type_text = '管理员' if application_type == 'admin' else '商家管理员'
        flash(f'{type_text}申请已提交，等待审核。')
        return redirect(url_for('auth.profile'))

    # 获取用户的申请记录
    applications = AdminApplication.query.filter_by(user_id=current_user.id).order_by(
        AdminApplication.timestamp.desc()
    ).all()
    
    return render_template('apply_admin.html', applications=applications)

@auth_bp.route('/admin/applications')
@login_required
def admin_applications():
    """管理员审核申请列表"""
    if current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('restaurant.list_restaurants'))
    
    # 获取所有待审核的申请
    admin_applications = AdminApplication.query.filter_by(status='pending').all()
    merchant_applications = MerchantApplication.query.filter_by(status='pending').all()
    
    return render_template('admin_applications.html', 
                         admin_applications=admin_applications,
                         merchant_applications=merchant_applications)

@auth_bp.route('/admin/applications/<int:app_id>/approve')
@login_required
def approve_application(app_id):
    """审核通过管理员申请"""
    if current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('restaurant.list_restaurants'))
    
    application = AdminApplication.query.get_or_404(app_id)
    application.status = 'approved'
    
    # 根据申请类型设置角色
    if application.application_type == 'admin':
        application.user.role = 'admin'
    elif application.application_type == 'merchant':
        application.user.role = 'merchant'
    
    db.session.commit()
    
    type_text = '管理员' if application.application_type == 'admin' else '商家管理员'
    flash(f'{type_text}申请已通过')
    return redirect(url_for('auth.admin_applications'))

@auth_bp.route('/admin/applications/<int:app_id>/reject')
@login_required
def reject_application(app_id):
    if current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('restaurant.list_restaurants'))
    
    application = AdminApplication.query.get_or_404(app_id)
    application.status = 'rejected'
    db.session.commit()
    flash('申请已拒绝')
    return redirect(url_for('auth.admin_applications'))

@auth_bp.route('/address/add', methods=['POST'])
@login_required
def add_address():
    """添加收货地址"""
    name = request.form.get('name')
    phone = request.form.get('phone')
    address = request.form.get('address')
    is_default = request.form.get('is_default') == 'on'
    
    if not all([name, phone, address]):
        flash('请填写完整的地址信息')
        return redirect(url_for('auth.profile'))
    
    # 如果设为默认地址，先将其他地址设为非默认
    if is_default:
        Address.query.filter_by(user_id=current_user.id, is_default=True).update({'is_default': False})
    
    new_address = Address(
        user_id=current_user.id,
        name=name,
        phone=phone,
        address=address,
        is_default=is_default
    )
    
    db.session.add(new_address)
    db.session.commit()
    
    flash('地址添加成功')
    return redirect(url_for('auth.profile'))

@auth_bp.route('/address/<int:address_id>/edit', methods=['POST'])
@login_required
def edit_address(address_id):
    """编辑收货地址"""
    address = Address.query.filter_by(id=address_id, user_id=current_user.id).first()
    
    if not address:
        flash('地址不存在')
        return redirect(url_for('auth.profile'))
    
    address.name = request.form.get('name')
    address.phone = request.form.get('phone')
    address.address = request.form.get('address')
    is_default = request.form.get('is_default') == 'on'
    
    # 如果设为默认地址，先将其他地址设为非默认
    if is_default and not address.is_default:
        Address.query.filter_by(user_id=current_user.id, is_default=True).update({'is_default': False})
    
    address.is_default = is_default
    db.session.commit()
    
    flash('地址更新成功')
    return redirect(url_for('auth.profile'))

@auth_bp.route('/address/<int:address_id>/delete')
@login_required
def delete_address(address_id):
    """删除收货地址"""
    address = Address.query.filter_by(id=address_id, user_id=current_user.id).first()
    
    if not address:
        flash('地址不存在')
        return redirect(url_for('auth.profile'))
    
    db.session.delete(address)
    db.session.commit()
    
    flash('地址删除成功')
    return redirect(url_for('auth.profile'))

@auth_bp.route('/address/<int:address_id>/set_default')
@login_required
def set_default_address(address_id):
    """设置默认地址"""
    address = Address.query.filter_by(id=address_id, user_id=current_user.id).first()
    
    if not address:
        flash('地址不存在')
        return redirect(url_for('auth.profile'))
    
    # 先将其他地址设为非默认
    Address.query.filter_by(user_id=current_user.id, is_default=True).update({'is_default': False})
    
    # 设置当前地址为默认
    address.is_default = True
    db.session.commit()
    
    flash('默认地址设置成功')
    return redirect(url_for('auth.profile'))

@auth_bp.route('/merchant/apply_restaurant', methods=['GET', 'POST'])
@login_required
def apply_restaurant():
    """商家管理员申请管理商家"""
    if current_user.role != 'merchant':
        flash('只有商家管理员可以申请管理商家')
        return redirect(url_for('restaurant.list_restaurants'))
    
    if request.method == 'POST':
        application_type = request.form.get('application_type')  # existing/new
        reason = request.form.get('reason')
        
        if application_type == 'existing':
            # 申请管理现有商家
            restaurant_id = request.form.get('restaurant_id')
            if not restaurant_id:
                flash('请选择要申请的商家')
                return redirect(url_for('auth.apply_restaurant'))
            
            # 检查商家是否存在
            restaurant = Restaurant.query.get(restaurant_id)
            if not restaurant:
                flash('商家不存在')
                return redirect(url_for('auth.apply_restaurant'))
            
            # 检查是否已有待处理的申请
            existing = MerchantApplication.query.filter_by(
                user_id=current_user.id,
                restaurant_id=restaurant_id,
                status='pending'
            ).first()
            
            if existing:
                flash('你已对该商家提交了待处理的申请')
                return redirect(url_for('auth.profile'))
            
            application = MerchantApplication(
                user_id=current_user.id,
                application_type='existing',
                restaurant_id=restaurant_id,
                reason=reason
            )
            
        elif application_type == 'new':
            # 申请创建新商家
            restaurant_name = request.form.get('restaurant_name')
            restaurant_description = request.form.get('restaurant_description')
            restaurant_address = request.form.get('restaurant_address')
            restaurant_phone = request.form.get('restaurant_phone')
            cuisine_type = request.form.get('cuisine_type')
            
            if not restaurant_name:
                flash('请填写商家名称')
                return redirect(url_for('auth.apply_restaurant'))
            
            # 先创建商家（状态为下线）
            new_restaurant = Restaurant(
                name=restaurant_name,
                description=restaurant_description,
                address=restaurant_address,
                phone=restaurant_phone,
                cuisine_type=cuisine_type,
                status='closed',
                is_active=False  # 下线状态，不显示在主页
            )
            db.session.add(new_restaurant)
            db.session.flush()  # 获取新商家的ID
            
            application = MerchantApplication(
                user_id=current_user.id,
                application_type='new',
                restaurant_id=new_restaurant.id,
                restaurant_name=restaurant_name,
                restaurant_description=restaurant_description,
                restaurant_address=restaurant_address,
                restaurant_phone=restaurant_phone,
                cuisine_type=cuisine_type,
                reason=reason
            )
        else:
            flash('无效的申请类型')
            return redirect(url_for('auth.apply_restaurant'))
        
        db.session.add(application)
        db.session.commit()
        
        flash('商家申请已提交，等待管理员审核')
        return redirect(url_for('auth.profile'))
    
    # GET请求，显示申请页面
    restaurants = Restaurant.query.filter_by(is_active=True).all()
    merchant_applications = MerchantApplication.query.filter_by(
        user_id=current_user.id
    ).order_by(MerchantApplication.timestamp.desc()).all()
    
    return render_template('merchant/apply_restaurant.html', 
                         restaurants=restaurants,
                         applications=merchant_applications)

@auth_bp.route('/admin/merchant_applications/<int:app_id>/approve')
@login_required
def approve_merchant_application(app_id):
    """审核通过商家管理员申请"""
    if current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('restaurant.list_restaurants'))
    
    application = MerchantApplication.query.get_or_404(app_id)
    
    if application.status != 'pending':
        flash('该申请已处理')
        return redirect(url_for('auth.admin_applications'))
    
    application.status = 'approved'
    
    # 将用户关联到商家
    user = application.user
    user.restaurant_id = application.restaurant_id
    
    if application.application_type == 'new':
        # 新商家申请通过，但保持下线状态
        restaurant = Restaurant.query.get(application.restaurant_id)
        if restaurant:
            restaurant.is_active = False  # 保持下线
            restaurant.status = 'closed'
    
    db.session.commit()
    
    flash(f'已通过 {user.username} 对商家 {application.restaurant.name if application.restaurant else ""} 的申请')
    return redirect(url_for('auth.admin_applications'))

@auth_bp.route('/admin/merchant_applications/<int:app_id>/reject')
@login_required
def reject_merchant_application(app_id):
    """拒绝商家管理员申请"""
    if current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('restaurant.list_restaurants'))
    
    application = MerchantApplication.query.get_or_404(app_id)
    
    if application.status != 'pending':
        flash('该申请已处理')
        return redirect(url_for('auth.admin_applications'))
    
    application.status = 'rejected'
    
    # 如果是新建商家的申请被拒绝，删除创建的商家
    if application.application_type == 'new' and application.restaurant_id:
        restaurant = Restaurant.query.get(application.restaurant_id)
        if restaurant and not restaurant.is_active:
            db.session.delete(restaurant)
    
    db.session.commit()
    
    flash('申请已拒绝')
    return redirect(url_for('auth.admin_applications'))
