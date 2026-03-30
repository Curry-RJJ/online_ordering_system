"""
注册 / 改密密码策略：长度、字母与数字、zxcvbn 评分（可配置最低分，默认 2）。
"""
from __future__ import annotations

import os
import re
from typing import Optional, Tuple

from zxcvbn import zxcvbn

PWD_MIN_LEN = 8
PWD_MAX_LEN = 128


def _zxcvbn_min_score() -> int:
    try:
        from flask import current_app, has_app_context

        if has_app_context():
            return int(current_app.config.get('PASSWORD_ZXCVBN_MIN_SCORE', 2))
    except Exception:
        pass
    return int(os.environ.get('PASSWORD_ZXCVBN_MIN_SCORE', '2'))


def validate_password(
    password: str,
    *,
    username: Optional[str] = None,
    email: Optional[str] = None,
) -> Tuple[bool, str]:
    if password is None:
        return False, '密码不能为空'
    if len(password) < PWD_MIN_LEN or len(password) > PWD_MAX_LEN:
        return False, f'密码长度须在 {PWD_MIN_LEN}～{PWD_MAX_LEN} 个字符之间'
    if not re.search(r'[A-Za-z]', password):
        return False, '密码须至少包含一个英文字母'
    if not re.search(r'\d', password):
        return False, '密码须至少包含一个数字'

    user_inputs = []
    if username:
        user_inputs.append(username)
    if email and isinstance(email, str) and '@' in email:
        user_inputs.append(email.split('@', 1)[0])

    result = zxcvbn(password, user_inputs=user_inputs)
    min_score = _zxcvbn_min_score()
    if result['score'] < min_score:
        feedback = result.get('feedback') or {}
        warn = (feedback.get('warning') or '').strip()
        suggestions = feedback.get('suggestions') or []
        hint = warn or (suggestions[0] if suggestions else '')
        if hint:
            return False, f'密码强度不足：{hint}'
        return False, '密码过于简单，请避免常见词语、重复或规律性字符'
    return True, ''
