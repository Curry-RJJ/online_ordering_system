from flask import request
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from werkzeug.security import check_password_hash, generate_password_hash
from app.models import User
from app import db
from app.api import api_bp
from app.api.errors import ok, created, bad_request, unauthorized, not_found


def _user_dict(user: User) -> dict:
    return {
        'id': user.id,
        'username': user.username,
        'role': user.role,
        'phone': user.phone,
        'email': user.email,
        'avatar': user.avatar,
    }


@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    """
    用户登录
    ---
    Body: { "username": "...", "password": "..." }
    Response: { access_token, refresh_token, user }
    """
    data = request.get_json(silent=True)
    if not data:
        return bad_request('请求体不能为空')

    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    if not username or not password:
        return bad_request('用户名和密码不能为空')

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, password):
        return unauthorized('用户名或密码错误')

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return ok({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': _user_dict(user)
    }, message='登录成功')


@api_bp.route('/auth/register', methods=['POST'])
def api_register():
    """
    用户注册
    ---
    Body: { "username": "...", "password": "...", "phone": "..." }
    """
    data = request.get_json(silent=True)
    if not data:
        return bad_request('请求体不能为空')

    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    phone = (data.get('phone') or '').strip()

    if not username or len(username) < 3:
        return bad_request('用户名至少3个字符')
    if not password or len(password) < 6:
        return bad_request('密码至少6个字符')

    if User.query.filter_by(username=username).first():
        return bad_request('用户名已存在')

    user = User(
        username=username,
        password=generate_password_hash(password),
        phone=phone,
        role='user'
    )
    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return created({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': _user_dict(user)
    }, message='注册成功')


@api_bp.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def api_refresh():
    """
    刷新 Access Token
    ---
    Header: Authorization: Bearer <refresh_token>
    """
    user_id = get_jwt_identity()
    new_token = create_access_token(identity=user_id)
    return ok({'access_token': new_token}, message='Token 已刷新')


@api_bp.route('/auth/me', methods=['GET'])
@jwt_required()
def api_me():
    """获取当前登录用户信息"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return not_found('用户不存在')
    return ok(_user_dict(user))
