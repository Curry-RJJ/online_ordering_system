"""
Schema 校验单元测试（纯逻辑，无需启动 Flask App）
对应测试报告：M01 输入校验、M05/M06 请求参数校验
"""
import pytest
from app.api.schemas import (
    LoginSchema, RegisterSchema,
    AddCartItemSchema, UpdateCartItemSchema,
    CreateOrderSchema
)


class TestLoginSchema:
    """TC-AUTH-03/04 相关的参数校验"""

    def test_valid_login(self):
        errors = LoginSchema().validate({'username': 'admin', 'password': 'admin123'})
        assert errors == {}

    def test_missing_password(self):
        errors = LoginSchema().validate({'username': 'admin'})
        assert 'password' in errors

    def test_missing_username(self):
        errors = LoginSchema().validate({'password': 'admin123'})
        assert 'username' in errors

    def test_empty_username(self):
        errors = LoginSchema().validate({'username': '', 'password': 'admin123'})
        assert 'username' in errors

    def test_empty_body(self):
        errors = LoginSchema().validate({})
        assert 'username' in errors
        assert 'password' in errors


class TestRegisterSchema:
    """TC-AUTH-01/02 相关的参数校验"""

    def test_valid_register(self):
        errors = RegisterSchema().validate({
            'username': 'newuser', 'password': 'Test123456'
        })
        assert errors == {}

    def test_username_too_short(self):
        """用户名少于3字符应失败"""
        errors = RegisterSchema().validate({'username': 'ab', 'password': 'Test123456'})
        assert 'username' in errors

    def test_username_too_long(self):
        errors = RegisterSchema().validate({
            'username': 'a' * 33, 'password': 'Test123456'
        })
        assert 'username' in errors

    def test_password_too_short(self):
        """密码少于6字符应失败"""
        errors = RegisterSchema().validate({'username': 'newuser', 'password': '123'})
        assert 'password' in errors

    def test_invalid_phone(self):
        """手机号格式不正确应失败"""
        errors = RegisterSchema().validate({
            'username': 'newuser', 'password': 'Test123456', 'phone': '12345'
        })
        assert 'phone' in errors

    def test_valid_phone(self):
        errors = RegisterSchema().validate({
            'username': 'newuser', 'password': 'Test123456', 'phone': '13900139000'
        })
        assert errors == {}

    def test_phone_is_optional(self):
        """手机号是可选字段"""
        errors = RegisterSchema().validate({'username': 'newuser', 'password': 'Test123456'})
        assert 'phone' not in errors


class TestAddCartItemSchema:
    """TC-CART-01/04/05 相关的参数校验"""

    def test_valid(self):
        errors = AddCartItemSchema().validate({'dish_id': 1, 'quantity': 2})
        assert errors == {}

    def test_missing_dish_id(self):
        errors = AddCartItemSchema().validate({'quantity': 1})
        assert 'dish_id' in errors

    def test_invalid_dish_id_zero(self):
        errors = AddCartItemSchema().validate({'dish_id': 0, 'quantity': 1})
        assert 'dish_id' in errors

    def test_quantity_default_is_1(self):
        """quantity 不传时默认为 1"""
        cleaned = AddCartItemSchema().load({'dish_id': 1})
        assert cleaned['quantity'] == 1

    def test_quantity_too_large(self):
        errors = AddCartItemSchema().validate({'dish_id': 1, 'quantity': 100})
        assert 'quantity' in errors

    def test_quantity_zero(self):
        """TC-CART-04: 数量为0应失败"""
        errors = AddCartItemSchema().validate({'dish_id': 1, 'quantity': 0})
        assert 'quantity' in errors


class TestUpdateCartItemSchema:
    """TC-CART-03/04"""

    def test_valid(self):
        errors = UpdateCartItemSchema().validate({'quantity': 5})
        assert errors == {}

    def test_zero_quantity(self):
        """TC-CART-04: quantity=0 应返回错误"""
        errors = UpdateCartItemSchema().validate({'quantity': 0})
        assert 'quantity' in errors

    def test_negative_quantity(self):
        errors = UpdateCartItemSchema().validate({'quantity': -1})
        assert 'quantity' in errors

    def test_missing_quantity(self):
        errors = UpdateCartItemSchema().validate({})
        assert 'quantity' in errors


class TestCreateOrderSchema:
    """TC-ORD-01"""

    def test_valid(self):
        errors = CreateOrderSchema().validate({'address_id': 1, 'remark': '不要辣'})
        assert errors == {}

    def test_missing_address_id(self):
        errors = CreateOrderSchema().validate({'remark': '不要辣'})
        assert 'address_id' in errors

    def test_remark_is_optional(self):
        errors = CreateOrderSchema().validate({'address_id': 1})
        assert errors == {}

    def test_remark_too_long(self):
        errors = CreateOrderSchema().validate({
            'address_id': 1, 'remark': 'a' * 201
        })
        assert 'remark' in errors
