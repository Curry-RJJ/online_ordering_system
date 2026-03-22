"""统一 API 响应格式"""
from flask import jsonify


def ok(data=None, message='success'):
    return jsonify({'code': 200, 'message': message, 'data': data}), 200


def created(data=None, message='创建成功'):
    return jsonify({'code': 201, 'message': message, 'data': data}), 201


def bad_request(message='请求参数错误', data=None):
    return jsonify({'code': 400, 'message': message, 'data': data}), 400


def unauthorized(message='未授权，请先登录'):
    return jsonify({'code': 401, 'message': message, 'data': None}), 401


def forbidden(message='权限不足'):
    return jsonify({'code': 403, 'message': message, 'data': None}), 403


def not_found(message='资源不存在'):
    return jsonify({'code': 404, 'message': message, 'data': None}), 404


def server_error(message='服务器内部错误'):
    return jsonify({'code': 500, 'message': message, 'data': None}), 500
