from flask import request
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from werkzeug.security import check_password_hash, generate_password_hash
from app.models import User
from app import db, limiter
from app.api import api_bp
from app.api.errors import ok, created, bad_request, unauthorized, not_found
from app.api.schemas import LoginSchema, RegisterSchema


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
@limiter.limit('10 per minute', error_message='登录尝试过于频繁，请1分钟后重试')
def api_login():
    """
    用户登录
    ---
    Body: { "username": "...", "password": "..." }
    Response: { access_token, refresh_token, user }
    """
    data = request.get_json(silent=True) or {}
    errors = LoginSchema().validate(data)
    if errors:
        return bad_request('请求参数错误', data=errors)

    username = data['username'].strip()
    password = data['password']

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
@limiter.limit('100 per minute', error_message='注册请求过于频繁，请1分钟后重试')
def api_register():
    """
    用户注册
    ---
    Body: { "username": "...", "password": "...", "phone": "..." }
    """
    data = request.get_json(silent=True) or {}
    errors = RegisterSchema().validate(data)
    if errors:
        return bad_request('请求参数错误', data=errors)

    cleaned = RegisterSchema().load(data)
    username = cleaned['username'].strip()

    if User.query.filter_by(username=username).first():
        return bad_request('用户名已存在')

    user = User(
        username=username,
        password=generate_password_hash(cleaned['password']),
        phone=cleaned.get('phone', ''),
        email=cleaned.get('email', ''),
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
