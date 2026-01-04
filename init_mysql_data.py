#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL数据初始化脚本 - 用于Docker容器启动时
"""

from werkzeug.security import generate_password_hash

# 创建管理员用户
admin = User(
    username='admin',
    password=generate_password_hash('admin123'),
    role='admin',
    phone='13800138000',
    email='admin@meituan.com'
)
db.session.add(admin)

# 创建测试用户
test_user = User(
    username='testuser',
    password=generate_password_hash('123456'),
    role='user',
    phone='13900139000',
    email='test@user.com'
)
db.session.add(test_user)

db.session.commit()
print("✓ 管理员账号创建完成: admin / admin123")
print("✓ 测试用户创建完成: testuser / 123456")
