"""
购物车 Service 层
- 使用 Redis Hash 存储：cart:{user_id} → {dish_id: quantity}
- 7 天滑动过期（每次读写重置 TTL）
- 被 app/routes/cart.py 和 app/api/cart.py 共同复用
"""
import redis as redis_lib
from flask import current_app

CART_TTL = 7 * 24 * 3600  # 7 天（秒）


def _get_redis():
    redis_url = (
        current_app.config.get('CACHE_REDIS_URL') or
        current_app.config.get('REDIS_URL') or
        'redis://localhost:6379/0'
    )
    return redis_lib.from_url(redis_url, decode_responses=True)


def _cart_key(user_id: int) -> str:
    return f'cart:{user_id}'


# ──────────────────────────────────────────────
# 公开接口
# ──────────────────────────────────────────────

def get_cart(user_id: int) -> dict:
    """返回 {dish_id(int): quantity(int)}，同时滑动续期 TTL"""
    try:
        r = _get_redis()
        raw = r.hgetall(_cart_key(user_id))
        if raw:
            r.expire(_cart_key(user_id), CART_TTL)
        return {int(k): int(v) for k, v in raw.items()}
    except Exception as e:
        current_app.logger.warning(f'[cart_service] get_cart error: {e}')
        return {}


def incr_item(user_id: int, dish_id: int, delta: int = 1) -> int:
    """增减某菜品数量，返回最新数量"""
    try:
        r = _get_redis()
        key = _cart_key(user_id)
        new_qty = r.hincrby(key, str(dish_id), delta)
        r.expire(key, CART_TTL)
        return new_qty
    except Exception as e:
        current_app.logger.warning(f'[cart_service] incr_item error: {e}')
        return 0


def set_item(user_id: int, dish_id: int, quantity: int) -> None:
    """直接设置某菜品的数量"""
    try:
        r = _get_redis()
        key = _cart_key(user_id)
        r.hset(key, str(dish_id), str(quantity))
        r.expire(key, CART_TTL)
    except Exception as e:
        current_app.logger.warning(f'[cart_service] set_item error: {e}')


def remove_item(user_id: int, dish_id: int) -> None:
    """删除购物车中某菜品"""
    try:
        r = _get_redis()
        key = _cart_key(user_id)
        r.hdel(key, str(dish_id))
        r.expire(key, CART_TTL)
    except Exception as e:
        current_app.logger.warning(f'[cart_service] remove_item error: {e}')


def clear(user_id: int) -> None:
    """清空购物车"""
    try:
        _get_redis().delete(_cart_key(user_id))
    except Exception as e:
        current_app.logger.warning(f'[cart_service] clear error: {e}')


def size(user_id: int) -> int:
    """返回购物车中不同菜品种数（HLEN），并续期 TTL"""
    try:
        r = _get_redis()
        key = _cart_key(user_id)
        count = r.hlen(key)
        if count > 0:
            r.expire(key, CART_TTL)
        return count
    except Exception as e:
        current_app.logger.warning(f'[cart_service] size error: {e}')
        return 0
