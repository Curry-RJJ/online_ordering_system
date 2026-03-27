"""
第七步：爬取 200 家深圳连锁餐厅 + 生成菜单

用法（在 Docker 容器内执行）：
    python scripts/seed_restaurants_amap.py

功能：
1. 创建餐厅分类（RestaurantCategory）
2. 创建菜品分类（Category，全局）
3. 调高德 API 搜索 35 个连锁品牌
   - 福田区 100 家
   - 其他区 100 家
4. 为每家餐厅：
   - 从百度爬取品牌 logo
   - 根据品牌内置精准菜单生成菜品
   - 从百度爬取菜品图片（同名菜复用）
5. 幂等性：按高德 POI ID 去重，可安全重跑
"""

from __future__ import annotations

import os
import sys
import re
import time
import random
import argparse
import requests

# ── 路径配置，使脚本在任意工作目录下均可运行 ──
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT, '.env'))
except ImportError:
    pass  # Docker 环境变量已由 docker-compose 注入，无需 dotenv

from app import create_app, db
from app.models import Restaurant, Dish, Category, RestaurantCategory

try:
    from scripts.menu_templates import (
        RESTAURANT_CATEGORIES, DISH_CATEGORIES, BRAND_INFO, CHAIN_MENUS,
    )
    from scripts.chain_scrapers import get_or_download_logo, get_or_download_dish_image
except ImportError:
    from menu_templates import (
        RESTAURANT_CATEGORIES, DISH_CATEGORIES, BRAND_INFO, CHAIN_MENUS,
    )
    from chain_scrapers import get_or_download_logo, get_or_download_dish_image

# ──────────────────────────────────────────────
# 配置
# ──────────────────────────────────────────────
FUTIAN_TARGET  = 100   # 福田区目标数量
OTHER_TARGET   = 100   # 其他区目标数量
AMAP_SLEEP     = 0.4   # 每次高德 API 调用后等待（秒）
AMAP_PAGE_SIZE = 25    # 高德每页最多返回数量

# 测试模式：只搜 3 个品牌，每个品牌取 1 家，共 3 家
TEST_BRANDS = ['kfc', 'starbucks', 'haidilao']
TEST_LIMIT  = 1   # 每个品牌最多取几家

STATIC_DIR = os.path.join(ROOT, 'app', 'static')

# POI ID 在 description 中的存储前缀
_POI_PREFIX = '[AMAP:'
_POI_RE     = re.compile(r'\[AMAP:([^\]]+)\]')


# ──────────────────────────────────────────────
# 高德 API 封装
# ──────────────────────────────────────────────
def _amap_key() -> str:
    from flask import current_app
    key = current_app.config.get('AMAP_WEB_KEY') or os.environ.get('AMAP_WEB_KEY', '')
    if not key:
        raise RuntimeError('AMAP_WEB_KEY 未设置，请检查 .env 文件')
    return key


def search_amap(keyword: str, city: str = '深圳',
                offset: int = 0) -> list[dict]:
    """
    调用高德搜索 API，返回 POI 列表。
    失败时返回空列表。
    """
    url = 'https://restapi.amap.com/v3/place/text'
    params = {
        'key':       _amap_key(),
        'keywords':  keyword,
        'types':     '050000',   # 餐饮服务
        'city':      city,
        'citylimit': 'true',
        'offset':    AMAP_PAGE_SIZE,
        'page':      offset // AMAP_PAGE_SIZE + 1,
        'extensions': 'base',
        'output':    'JSON',
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if data.get('status') == '1':
            return data.get('pois', [])
        print(f'  [!] 高德搜索返回异常: {data.get("info")}')
        return []
    except Exception as e:
        print(f'  [!] 高德搜索请求失败 "{keyword}": {e}')
        return []


# ──────────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────────
def get_imported_poi_ids() -> set[str]:
    """从数据库中读取已导入的高德 POI ID 集合（存储在 description 字段）"""
    ids: set[str] = set()
    restaurants = db.session.query(Restaurant.description).filter(
        Restaurant.description.like(f'{_POI_PREFIX}%')
    ).all()
    for (desc,) in restaurants:
        if desc:
            m = _POI_RE.search(desc)
            if m:
                ids.add(m.group(1))
    return ids


def identify_brand(restaurant_name: str) -> str | None:
    """根据餐厅名称匹配品牌 key"""
    name_lower = restaurant_name.lower()
    for brand_key, info in BRAND_INFO.items():
        for kw in info['name_keywords']:
            if kw.lower() in name_lower:
                return brand_key
    return None


def _build_description(poi: dict) -> str:
    """构造写入 description 字段的字符串（含 POI ID 用于去重）"""
    poi_id = poi.get('id', '')
    area = poi.get('business_area', '')
    adname = poi.get('adname', '')
    parts = [f'{_POI_PREFIX}{poi_id}]']
    if adname:
        parts.append(adname)
    if area:
        parts.append(f'{area}附近')
    return ' '.join(parts)


def _random_rating(base: float) -> float:
    return round(max(3.5, min(5.0, base + random.uniform(-0.3, 0.3))), 1)


# ──────────────────────────────────────────────
# 数据初始化（分类表）
# ──────────────────────────────────────────────
def create_restaurant_categories() -> None:
    """创建餐厅分类，已存在则跳过"""
    existing = {c.name for c in RestaurantCategory.query.all()}
    new_cats = []
    for cat in RESTAURANT_CATEGORIES:
        if cat['name'] not in existing:
            new_cats.append(RestaurantCategory(
                name=cat['name'],
                icon=cat.get('icon', ''),
                sort_order=cat.get('sort_order', 0),
            ))
    if new_cats:
        db.session.add_all(new_cats)
        db.session.commit()
        print(f'[初始化] 创建餐厅分类 {len(new_cats)} 个')
    else:
        print('[初始化] 餐厅分类已存在，跳过')


def create_dish_categories() -> dict[str, Category]:
    """
    创建菜品分类，已存在则跳过。
    返回 {name: Category} 映射字典。
    """
    existing = {c.name: c for c in Category.query.all()}
    new_cats = []
    for cat in DISH_CATEGORIES:
        if cat['name'] not in existing:
            obj = Category(
                name=cat['name'],
                sort_order=cat.get('sort_order', 0),
            )
            new_cats.append(obj)
            existing[cat['name']] = obj
    if new_cats:
        db.session.add_all(new_cats)
        db.session.commit()
        print(f'[初始化] 创建菜品分类 {len(new_cats)} 个')
    else:
        print('[初始化] 菜品分类已存在，跳过')
    return existing


# ──────────────────────────────────────────────
# POI 收集
# ──────────────────────────────────────────────
def collect_all_pois(imported_ids: set, test_mode: bool = False) -> tuple:
    """
    搜索所有品牌，将结果按区域分为 futian_list 和 other_list。
    每条记录格式：(poi_dict, brand_key)

    test_mode=True 时只搜 TEST_BRANDS，每个品牌取 TEST_LIMIT 家。
    """
    futian_seen = set(imported_ids)
    other_seen  = set(imported_ids)
    futian_list = []
    other_list  = []

    brand_keys = TEST_BRANDS if test_mode else list(BRAND_INFO.keys())
    total_brands = len(brand_keys)

    for idx, brand_key in enumerate(brand_keys, 1):
        info = BRAND_INFO[brand_key]
        print(f'  [{idx}/{total_brands}] 搜索品牌: {info["name_keywords"][0]} ...',
              end='', flush=True)

        brand_futian = 0
        brand_other  = 0

        keyword = info['name_keywords'][0]

        for page_offset in (0, AMAP_PAGE_SIZE):
            pois = search_amap(keyword, city='深圳', offset=page_offset)
            time.sleep(AMAP_SLEEP)

            if not pois:
                break

            for poi in pois:
                poi_id  = poi.get('id', '')
                adname  = poi.get('adname', '')
                if not poi_id:
                    continue

                is_futian = '福田' in adname

                if is_futian:
                    if poi_id not in futian_seen:
                        # 测试模式：每品牌只取 TEST_LIMIT 家
                        if test_mode and brand_futian >= TEST_LIMIT:
                            continue
                        futian_seen.add(poi_id)
                        futian_list.append((poi, brand_key))
                        brand_futian += 1
                else:
                    if poi_id not in other_seen:
                        if test_mode and brand_other >= TEST_LIMIT:
                            continue
                        other_seen.add(poi_id)
                        other_list.append((poi, brand_key))
                        brand_other += 1

            # 测试模式：第一页够了就不翻页
            if test_mode:
                break

        print(f' 福田 +{brand_futian}, 其他 +{brand_other}')

    return futian_list, other_list


def _balance_by_brand(raw: list[tuple[dict, str]],
                      target: int) -> list[tuple[dict, str]]:
    """
    按品牌轮询排列，确保品牌多样性，然后截取到 target 数量。
    """
    from collections import defaultdict
    by_brand: dict[str, list] = defaultdict(list)
    for item in raw:
        by_brand[item[1]].append(item)

    balanced = []
    brand_order = sorted(by_brand.keys())
    while len(balanced) < target:
        added = False
        for bk in brand_order:
            if by_brand[bk] and len(balanced) < target:
                balanced.append(by_brand[bk].pop(0))
                added = True
        if not added:
            break

    return balanced[:target]


# ──────────────────────────────────────────────
# 单家餐厅导入
# ──────────────────────────────────────────────
def import_restaurant(poi: dict, brand_key: str,
                       dish_cat_map: dict[str, Category]) -> bool:
    """
    将一条高德 POI 写入数据库，包含菜品和图片。
    成功返回 True，失败返回 False。
    """
    info = BRAND_INFO[brand_key]

    # 解析坐标（高德格式：lng,lat）
    location = poi.get('location', '')
    try:
        lng_str, lat_str = location.split(',')
        lng, lat = float(lng_str), float(lat_str)
    except Exception:
        print(f'  [!] 坐标解析失败: {location}，跳过')
        return False

    # 获取品牌 logo（每品牌只下载一次，缓存复用）
    logo_path = get_or_download_logo(
        brand_key, info['logo_keyword'], STATIC_DIR
    )

    # 构造餐厅记录
    restaurant = Restaurant(
        name=poi.get('name', ''),
        description=_build_description(poi),
        logo=logo_path,
        address=poi.get('address', ''),
        phone=(poi.get('tel', '') or '').split(';')[0][:20],
        cuisine_type=info['cuisine_type'],
        business_hours=info['business_hours'],
        delivery_fee=info['delivery_fee'],
        min_order=info['min_order'],
        latitude=lat,
        longitude=lng,
        rating=_random_rating(info['base_rating']),
        review_count=random.randint(50, 500),
        status='open',
        is_active=True,
    )
    db.session.add(restaurant)
    db.session.flush()   # 获取自增 id，不提交事务

    # 写入菜品
    dishes_data = CHAIN_MENUS.get(brand_key, [])
    for dish_data in dishes_data:
        cat_name = dish_data.get('category', '招牌菜')
        category = dish_cat_map.get(cat_name) or dish_cat_map.get('招牌菜')

        # 获取菜品图片（同 image_keyword 复用同一张）
        img_path = get_or_download_dish_image(
            dish_data['name'],
            dish_data.get('image_keyword', dish_data['name']),
            STATIC_DIR,
        )

        dish = Dish(
            restaurant_id=restaurant.id,
            category_id=category.id if category else None,
            name=dish_data['name'],
            description=dish_data.get('description', ''),
            price=dish_data['price'],
            image=img_path,
            ingredients=dish_data.get('ingredients', ''),
            is_recommended=dish_data.get('is_recommended', False),
            is_spicy=dish_data.get('is_spicy', False),
            available=True,
        )
        db.session.add(dish)

    db.session.commit()
    return True


# ──────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='深圳连锁餐厅数据初始化脚本')
    parser.add_argument(
        '--test', action='store_true',
        help=f'测试模式：只搜 {TEST_BRANDS}，每个品牌取 {TEST_LIMIT} 家，快速验证效果',
    )
    args = parser.parse_args()
    test_mode = args.test

    if test_mode:
        print('=' * 60)
        print('  [测试模式] 仅爬取 3 个品牌各 1 家，验证效果')
        print(f'  品牌：{", ".join(TEST_BRANDS)}')
        print('=' * 60)
    else:
        print('=' * 60)
        print('  深圳连锁餐厅数据初始化脚本')
        print('  目标：福田区 100 家 + 其他区 100 家')
        print('=' * 60)

    app = create_app()
    with app.app_context():

        # Step 1: 初始化分类
        print('\n[Step 1] 初始化餐厅分类和菜品分类')
        create_restaurant_categories()
        dish_cat_map = create_dish_categories()

        # Step 2: 加载已导入 POI ID（幂等性保障）
        imported_ids = get_imported_poi_ids()
        print(f'[Step 2] 数据库中已有 {len(imported_ids)} 条 POI 记录')

        # Step 3: 高德 API 搜索
        brand_count = len(TEST_BRANDS) if test_mode else len(BRAND_INFO)
        print(f'\n[Step 3] 开始搜索 {brand_count} 个品牌...')
        futian_raw, other_raw = collect_all_pois(imported_ids, test_mode=test_mode)
        print(f'\n  搜索结果: 福田区候选 {len(futian_raw)} 条,'
              f' 其他区候选 {len(other_raw)} 条')

        # Step 4: 按品牌轮询，均衡取样
        if test_mode:
            # 测试模式：直接合并，不限制数量
            futian_list = futian_raw
            other_list  = other_raw
        else:
            futian_list = _balance_by_brand(futian_raw, FUTIAN_TARGET)
            other_list  = _balance_by_brand(other_raw,  OTHER_TARGET)
        print(f'  实际导入: 福田 {len(futian_list)} 家,'
              f' 其他 {len(other_list)} 家')

        # Step 5: 导入数据库
        all_list = futian_list + other_list
        total    = len(all_list)
        success  = 0
        failed   = 0

        print(f'\n[Step 4] 开始写入数据库，共 {total} 家...\n')

        for i, (poi, brand_key) in enumerate(all_list, 1):
            name   = poi.get('name', '')
            adname = poi.get('adname', '')
            try:
                ok = import_restaurant(poi, brand_key, dish_cat_map)
                if ok:
                    success += 1
                    marker = 'OK'
                else:
                    failed += 1
                    marker = 'FAIL'
            except Exception as e:
                db.session.rollback()
                failed += 1
                marker = 'ERR'
                print(f'  [{i}/{total}] {marker} {name} 导入异常: {e}')
                continue

            print(f'  [{i}/{total}] {marker} {name} ({adname})')

        # Step 6: 汇总
        print('\n' + '=' * 60)
        print(f'  完成！成功导入 {success} 家餐厅，失败 {failed} 家')
        total_dishes = db.session.query(Dish).count()
        total_rests  = db.session.query(Restaurant).count()
        print(f'  数据库现有: {total_rests} 家餐厅，{total_dishes} 道菜品')
        if test_mode:
            print('\n  [测试模式] 请打开网站切换位置到深圳后查看效果')
            print('  [测试模式] 满意后执行完整版: python scripts/seed_restaurants_amap.py')
        print('=' * 60)


if __name__ == '__main__':
    main()
