from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_
from app.models import Restaurant, Dish, Category, Review
from app import db, cache
from app.api import api_bp
from app.api.errors import ok, not_found


# ──────────────────────────────────────────────
# 序列化辅助
# ──────────────────────────────────────────────

def _restaurant_dict(r) -> dict:
    return dict(id=r.id, name=r.name, description=r.description,
                logo=r.logo, banner=r.banner, address=r.address,
                phone=r.phone, cuisine_type=r.cuisine_type,
                business_hours=r.business_hours, delivery_fee=r.delivery_fee,
                min_order=r.min_order, rating=r.rating,
                review_count=r.review_count, status=r.status)


def _dish_dict(d) -> dict:
    return dict(id=d.id, name=d.name, description=d.description,
                price=d.price, original_price=d.original_price,
                image=d.image, sales_count=d.sales_count, rating=d.rating,
                is_recommended=d.is_recommended, is_spicy=d.is_spicy,
                available=d.available, category_id=d.category_id)


def _category_dict(c) -> dict:
    return dict(id=c.id, name=c.name, icon=c.icon)


def _review_dict(r) -> dict:
    return dict(id=r.id, rating=r.rating, content=r.content,
                created_at=r.created_at.strftime('%Y-%m-%d %H:%M'),
                username=r.user.username if r.user else '匿名')


# ──────────────────────────────────────────────
# 路由
# ──────────────────────────────────────────────

@api_bp.route('/restaurants', methods=['GET'])
def api_list_restaurants():
    """
    餐厅列表（支持搜索、分类筛选、排序、分页）
    ---
    Query: keyword, category, sort(rating|sales|newest), page, per_page
    注：sort=sales 实际按 review_count（评价数）排序，字段名保留向后兼容
    """
    keyword = request.args.get('keyword', '').strip()
    category_id = request.args.get('category', type=int)
    sort_by = request.args.get('sort', 'rating')
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    # 命中缓存（与页面路由共享同一套缓存 key）
    from app.routes.restaurant import _get_list_version
    version = _get_list_version()
    cache_key = f'api_restaurant_list_v{version}:{keyword}:{category_id}:{sort_by}:{page}:{per_page}'
    cached = cache.get(cache_key)

    if cached is None:
        query = Restaurant.query.filter_by(status='open')

        if keyword:
            dish_sub = db.session.query(Restaurant.id).join(Dish).filter(
                Dish.name.contains(keyword), Dish.available == True
            ).distinct().subquery()
            query = query.filter(or_(
                Restaurant.name.contains(keyword),
                Restaurant.id.in_(dish_sub)
            ))

        if category_id:
            query = query.join(Dish).join(Category).filter(Category.id == category_id)

        if sort_by == 'sales':
            query = query.order_by(Restaurant.review_count.desc())
        elif sort_by == 'newest':
            query = query.order_by(Restaurant.created_at.desc())
        else:
            query = query.order_by(Restaurant.rating.desc())

        pagination = query.distinct().paginate(page=page, per_page=per_page, error_out=False)

        cached = {
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages,
            'restaurants': [_restaurant_dict(r) for r in pagination.items]
        }
        cache.set(cache_key, cached, timeout=300)

    return ok(cached)


@api_bp.route('/restaurants/<int:restaurant_id>', methods=['GET'])
def api_restaurant_detail(restaurant_id):
    """
    餐厅详情 + 完整菜单（按分类分组）
    ---
    复用与页面路由相同的缓存 key
    """
    menu_cache_key = f'restaurant_menu:{restaurant_id}'
    menu_cached = cache.get(menu_cache_key)

    if menu_cached is None:
        restaurant = Restaurant.query.get_or_404(restaurant_id)

        categories_raw = db.session.query(Category).join(Dish).filter(
            Dish.restaurant_id == restaurant_id,
            Dish.available == True
        ).distinct().all()

        recommended_raw = Dish.query.filter_by(
            restaurant_id=restaurant_id, is_recommended=True, available=True
        ).limit(6).all()

        dishes_by_category = {}
        for cat in categories_raw:
            dishes = Dish.query.filter_by(
                restaurant_id=restaurant_id, category_id=cat.id, available=True
            ).order_by(Dish.sales_count.desc()).all()
            dishes_by_category[cat.name] = [_dish_dict(d) for d in dishes]

        from app.routes.restaurant import _to_restaurant_dict, _to_category_dict, _to_dish_dict
        menu_cached = {
            'restaurant': _to_restaurant_dict(restaurant),
            'categories': [_to_category_dict(c) for c in categories_raw],
            'recommended_dishes': [_to_dish_dict(d) for d in recommended_raw],
            'dishes_by_category': dishes_by_category,
        }
        cache.set(menu_cache_key, menu_cached, timeout=600)

    # 评价实时获取
    from sqlalchemy.orm import joinedload
    reviews = Review.query.options(joinedload(Review.user)) \
                          .filter_by(restaurant_id=restaurant_id) \
                          .order_by(Review.created_at.desc()) \
                          .limit(10).all()

    result = dict(menu_cached)
    result['reviews'] = [_review_dict(r) for r in reviews]
    return ok(result)
