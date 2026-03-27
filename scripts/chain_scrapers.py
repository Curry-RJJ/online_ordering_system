"""
图片爬取工具
- Bing Images 优先（国内/香港/本地均可访问），失败自动回退百度
- 内置缓存：同一关键词只下载一次
"""

from __future__ import annotations

import os
import re
import time
import requests

# ──────────────────────────────────────────────
# HTTP 请求头
# ──────────────────────────────────────────────
_UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
       '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

_BING_HEADERS = {
    'User-Agent': _UA,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Referer': 'https://www.bing.com/',
}
_BAIDU_HEADERS = {
    'User-Agent': _UA,
    'Referer': 'https://image.baidu.com/',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}
_DOWNLOAD_HEADERS = {'User-Agent': _UA}

# ──────────────────────────────────────────────
# 模块级缓存：keyword → 已保存的相对静态路径
# ──────────────────────────────────────────────
_image_cache: dict = {}


def _safe_filename(text: str, max_len: int = 40) -> str:
    safe = re.sub(r'[^\w\u4e00-\u9fff\-]', '_', text)
    return safe[:max_len]


# ──────────────────────────────────────────────
# Bing Images 搜索
# ──────────────────────────────────────────────
def _search_bing_images(keyword: str, count: int = 5) -> list:
    """
    从 Bing Images 提取原始图片 URL（murl 字段）。
    国内、香港、本地均可访问，比 Google 稳定。
    """
    try:
        resp = requests.get(
            'https://www.bing.com/images/search',
            params={'q': keyword, 'form': 'HDRSC2', 'first': '1'},
            headers=_BING_HEADERS,
            timeout=10,
        )
        # Bing 在 HTML 中以 "murl":"https://..." 格式嵌入原始图片 URL
        urls = re.findall(r'"murl":"(https?://[^"]+)"', resp.text)
        return urls[:count]
    except Exception as e:
        print(f'  [Bing] 搜索失败 "{keyword}"，回退百度: {e}')
        return []


# ──────────────────────────────────────────────
# 百度图片搜索（回退方案）
# ──────────────────────────────────────────────
def _search_baidu_images(keyword: str, count: int = 5) -> list:
    try:
        resp = requests.get(
            'https://image.baidu.com/search/acjson',
            params={
                'tn': 'resultjson_com', 'ipn': 'rj', 'ct': '201326592',
                'fp': 'result', 'queryWord': keyword, 'cl': '2', 'lm': '-1',
                'ie': 'utf-8', 'oe': 'utf-8', 'st': '-1', 'ic': '0',
                'word': keyword, 'face': '0', 'istype': '2', 'nc': '1',
                'fr': '', 'pn': '0', 'rn': str(count + 5),
            },
            headers=_BAIDU_HEADERS,
            timeout=10,
        )
        urls = []
        for item in resp.json().get('data', []):
            if not isinstance(item, dict):
                continue
            u = item.get('middleURL') or item.get('hoverURL') or item.get('objURL') or ''
            if u.startswith('http'):
                urls.append(u)
            if len(urls) >= count:
                break
        return urls
    except Exception as e:
        print(f'  [百度] 搜索失败 "{keyword}": {e}')
        return []


# ──────────────────────────────────────────────
# 图片下载
# ──────────────────────────────────────────────
def _download_image(url: str, save_path: str) -> bool:
    try:
        resp = requests.get(url, headers=_DOWNLOAD_HEADERS, timeout=15, stream=True)
        if resp.status_code != 200:
            return False
        content_type = resp.headers.get('content-type', '')
        if 'image' not in content_type and not any(
                save_path.endswith(ext) for ext in ('.jpg', '.jpeg', '.png', '.webp')):
            return False
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'wb') as f:
            for chunk in resp.iter_content(8192):
                if chunk:
                    f.write(chunk)
        if os.path.getsize(save_path) < 2048:
            os.remove(save_path)
            return False
        return True
    except Exception:
        if os.path.exists(save_path):
            try:
                os.remove(save_path)
            except Exception:
                pass
        return False


def _fetch_and_save(keyword: str, save_path: str,
                    static_path: str, placeholder: str) -> str:
    """
    Google 优先搜索并下载，失败回退百度。
    成功返回 static_path，全部失败返回 placeholder。
    """
    if os.path.exists(save_path):
        return static_path

    # 1. 尝试 Bing（国内/香港/本地均可访问）
    urls = _search_bing_images(keyword, count=5)
    source = 'Bing'

    # 2. Bing 无结果则回退百度
    if not urls:
        urls = _search_baidu_images(keyword, count=5)
        source = '百度'

    time.sleep(0.3)

    for url in urls:
        if _download_image(url, save_path):
            print(f'  [图片/{source}] {keyword[:20]}', end=' ')
            return static_path

    return placeholder


# ──────────────────────────────────────────────
# 公开接口
# ──────────────────────────────────────────────

def get_or_download_logo(brand_key: str, logo_keyword: str,
                         static_dir: str) -> str:
    """
    获取品牌 logo 图片的静态路径。
    - 优先使用缓存
    - 其次检查文件是否已存在
    - 否则从百度下载
    返回相对路径 /static/images/logos/<brand_key>.jpg
    """
    cache_key = f'logo:{brand_key}'
    if cache_key in _image_cache:
        return _image_cache[cache_key]

    filename = f'{brand_key}.jpg'
    save_path = os.path.join(static_dir, 'images', 'logos', filename)
    static_path = f'/static/images/logos/{filename}'
    placeholder = '/static/images/logos/placeholder.png'

    result = _fetch_and_save(logo_keyword, save_path, static_path, placeholder)
    _image_cache[cache_key] = result
    return result


def get_or_download_dish_image(dish_name: str, image_keyword: str,
                                static_dir: str) -> str:
    """
    获取菜品图片的静态路径。
    - 同名菜品复用同一张图片（缓存 key = image_keyword）
    返回相对路径 /static/images/dishes/<safe_name>.jpg
    """
    cache_key = f'dish:{image_keyword}'
    if cache_key in _image_cache:
        return _image_cache[cache_key]

    filename = f'{_safe_filename(image_keyword)}.jpg'
    save_path = os.path.join(static_dir, 'images', 'dishes', filename)
    static_path = f'/static/images/dishes/{filename}'
    placeholder = '/static/images/dishes/placeholder.png'

    result = _fetch_and_save(image_keyword, save_path, static_path, placeholder)
    _image_cache[cache_key] = result
    return result
