"""
首次初始化数据库时的管理员账号（正式环境通过环境变量注入，禁止在代码中写死密码）。
"""
from __future__ import annotations

import os
from typing import Any, Dict

from app.password_policy import validate_password


def get_initial_admin_credentials() -> Dict[str, Any]:
    """
    读取 INITIAL_ADMIN_* 环境变量，返回明文密码供 generate_password_hash。

    - 生产环境（FLASK_ENV=production）：必须设置 INITIAL_ADMIN_PASSWORD，且须通过 validate_password。
    - 开发环境（FLASK_ENV=development）：未设置时使用内置默认（满足密码策略，仅本地）。
    """
    username = (os.environ.get('INITIAL_ADMIN_USERNAME') or 'admin').strip() or 'admin'
    email = (os.environ.get('INITIAL_ADMIN_EMAIL') or 'admin@example.com').strip() or 'admin@example.com'
    phone = (os.environ.get('INITIAL_ADMIN_PHONE') or '13800138000').strip() or '13800138000'
    raw = (os.environ.get('INITIAL_ADMIN_PASSWORD') or '').strip()
    flask_env = os.environ.get('FLASK_ENV', 'production')

    if not raw:
        if flask_env == 'development':
            raw = 'BrandNew123'
        else:
            raise ValueError(
                '生产环境首次初始化须设置环境变量 INITIAL_ADMIN_PASSWORD（须满足注册密码策略：'
                '长度 8～128，含字母与数字，且 zxcvbn 分数不低于配置阈值）。'
            )

    ok, msg = validate_password(raw, username=username, email=email)
    if not ok:
        raise ValueError(msg)

    return {
        'username': username,
        'password': raw,
        'email': email,
        'phone': phone,
    }
