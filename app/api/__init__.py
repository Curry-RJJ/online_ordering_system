from flask import Blueprint

api_bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# 注册各模块路由（必须在 Blueprint 创建后导入，避免循环引用）
from app.api import auth, restaurants, cart, orders  # noqa: E402, F401
