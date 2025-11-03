from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, AdminApplication, Address
from app import db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return redirect(url_for('auth.register'))

        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash('注册成功，请登录')
        return redirect(url_for('auth.login'))

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
    return render_template('auth/profile.html', user=current_user, addresses=addresses)

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

@auth_bp.route('/apply_admin', methods=['GET', 'POST'])
@login_required
def apply_admin():
    if request.method == 'POST':
        reason = request.form.get('reason')
        existing = AdminApplication.query.filter_by(user_id=current_user.id, status='pending').first()
        if existing:
            flash('你已有待处理的申请，请等待审核。')
            return redirect(url_for('restaurant.list_restaurants'))

        application = AdminApplication(user_id=current_user.id, reason=reason)
        db.session.add(application)
        db.session.commit()
        flash('管理员申请已提交，等待审核。')
        return redirect(url_for('restaurant.list_restaurants'))

    return render_template('apply_admin.html')

@auth_bp.route('/admin/applications')
@login_required
def admin_applications():
    if current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('restaurant.list_restaurants'))
    applications = AdminApplication.query.filter_by(status='pending').all()
    return render_template('admin_applications.html', applications=applications)

@auth_bp.route('/admin/applications/<int:app_id>/approve')
@login_required
def approve_application(app_id):
    if current_user.role != 'admin':
        flash('权限不足')
        return redirect(url_for('restaurant.list_restaurants'))
    application = AdminApplication.query.get_or_404(app_id)
    application.status = 'approved'
    application.user.role = 'admin'
    db.session.commit()
    flash('申请已通过')
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
