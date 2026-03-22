"""
API 输入校验 Schema
使用 marshmallow 集中定义，路由函数只负责业务逻辑。

用法：
    errors = LoginSchema().validate(request.get_json() or {})
    if errors:
        return bad_request("请求参数错误", data=errors)
"""
import re
from marshmallow import Schema, fields, validate, validates, ValidationError


# ──────────────────────────────────────────────
# 自定义校验器
# ──────────────────────────────────────────────

def _phone_validator(value: str):
    if value and not re.match(r'^1[3-9]\d{9}$', value):
        raise ValidationError('手机号格式不正确，请输入11位大陆手机号')


# ──────────────────────────────────────────────
# Auth Schemas
# ──────────────────────────────────────────────

class LoginSchema(Schema):
    username = fields.Str(
        required=True,
        validate=validate.Length(min=1, error='用户名不能为空'),
        error_messages={'required': '用户名不能为空'}
    )
    password = fields.Str(
        required=True,
        validate=validate.Length(min=1, error='密码不能为空'),
        error_messages={'required': '密码不能为空'}
    )


class RegisterSchema(Schema):
    username = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=32,
                                 error='用户名长度在3到32个字符之间'),
        error_messages={'required': '用户名不能为空'}
    )
    password = fields.Str(
        required=True,
        validate=validate.Length(min=6, max=128,
                                 error='密码长度在6到128个字符之间'),
        error_messages={'required': '密码不能为空'}
    )
    phone = fields.Str(
        load_default='',
        validate=_phone_validator
    )
    email = fields.Email(
        load_default='',
        error_messages={'validator_failed': '邮箱格式不正确'}
    )


# ──────────────────────────────────────────────
# Cart Schemas
# ──────────────────────────────────────────────

class AddCartItemSchema(Schema):
    dish_id = fields.Int(
        required=True,
        validate=validate.Range(min=1, error='dish_id 必须为正整数'),
        error_messages={'required': 'dish_id 不能为空', 'invalid': 'dish_id 必须为整数'}
    )
    quantity = fields.Int(
        load_default=1,
        validate=validate.Range(min=1, max=99,
                                error='数量必须在1到99之间')
    )


class UpdateCartItemSchema(Schema):
    quantity = fields.Int(
        required=True,
        validate=validate.Range(min=1, max=99,
                                error='数量必须在1到99之间'),
        error_messages={'required': 'quantity 不能为空', 'invalid': 'quantity 必须为整数'}
    )


# ──────────────────────────────────────────────
# Order Schemas
# ──────────────────────────────────────────────

class CreateOrderSchema(Schema):
    address_id = fields.Int(
        required=True,
        validate=validate.Range(min=1, error='address_id 必须为正整数'),
        error_messages={'required': 'address_id 不能为空', 'invalid': 'address_id 必须为整数'}
    )
    remark = fields.Str(
        load_default='',
        validate=validate.Length(max=200, error='备注最多200个字符')
    )
