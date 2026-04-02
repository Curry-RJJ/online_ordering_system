import os
import sys
import logging
from typing import Optional, Tuple
from logging.handlers import RotatingFileHandler
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
from PIL import Image
import hashlib


def public_asset_url(path: Optional[str]) -> str:
    """
    将站内资源路径（如 /static/images/...）转为可访问的绝对 URL。
    若设置环境变量 STATIC_CDN_BASE（或 Flask config 同名）为 CDN/ COS 根域名（无尾斜杠），
    则拼接为 CDN 地址；否则仍返回原路径（由浏览器向当前站点请求）。
    已是 http(s) 开头的外链则原样返回。
    """
    if path is None:
        return ''
    p = str(path).strip()
    if not p:
        return ''
    if p.startswith(('http://', 'https://')):
        return p
    if not p.startswith('/'):
        p = '/' + p
    base = ''
    try:
        from flask import has_app_context, current_app
        if has_app_context():
            base = (current_app.config.get('STATIC_CDN_BASE') or '').strip().rstrip('/')
    except Exception:
        pass
    if not base:
        base = os.environ.get('STATIC_CDN_BASE', '').strip().rstrip('/')
    if base:
        return base + p
    return p


def setup_logging(app):
    """
    配置日志系统
    
    在生产环境下使用 StreamHandler 输出到 stdout，
    避免 Gunicorn 多进程下的文件写入冲突问题。
    日志由 Docker/Gunicorn 统一管理和收集。
    """
    if not app.debug:
        # 生产环境：使用 StreamHandler 输出到 stdout
        # 由 Docker 日志驱动和 Gunicorn 统一管理，避免多进程文件锁冲突
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        stream_handler.setLevel(logging.INFO)
        app.logger.addHandler(stream_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('美团外卖系统启动')

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    from flask import current_app
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def generate_filename(original_filename):
    """生成安全的文件名"""
    ext = original_filename.rsplit('.', 1)[1].lower()
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"{timestamp}_{os.urandom(8).hex()}.{ext}"

def format_currency(amount):
    """格式化货币显示"""
    return f"¥{amount:.2f}"

def format_datetime(dt):
    """格式化日期时间显示"""
    if not dt:
        return ''
    return dt.strftime('%Y-%m-%d %H:%M:%S')

# 注：allowed_file 函数已在前面定义（第34-38行），此处删除重复定义

def generate_unique_filename(original_filename):
    """生成唯一的文件名"""
    # 获取文件扩展名
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
    # 生成UUID作为文件名
    unique_name = str(uuid.uuid4())
    return f"{unique_name}.{ext}"

def save_uploaded_image(file, upload_type='dishes', max_size=(800, 600)):
    """
    保存上传的图片文件
    
    Args:
        file: 上传的文件对象
        upload_type: 上传类型 ('dishes', 'restaurants', 'logos', 'banners')
        max_size: 图片最大尺寸 (width, height)
    
    Returns:
        str: 保存的文件相对路径，失败返回None
    """
    # BUG-17 修复：用 logger 替换所有 print 语句
    from flask import current_app
    logger = current_app.logger

    if not file or not file.filename:
        logger.debug("save_uploaded_image: 没有文件或文件名为空")
        return None

    if not allowed_file(file.filename):
        logger.warning(f"save_uploaded_image: 不支持的文件格式: {file.filename}")
        return None

    try:
        filename = generate_unique_filename(file.filename)
        logger.debug(f"save_uploaded_image: 生成文件名: {filename}")

        app_root = os.path.dirname(current_app.instance_path)
        upload_dir = os.path.join(app_root, 'app', 'static', 'images', upload_type)

        os.makedirs(upload_dir, exist_ok=True)
        logger.debug(f"save_uploaded_image: 保存目录: {upload_dir}")

        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        logger.debug(f"save_uploaded_image: 文件保存成功: {file_path}")

        try:
            with Image.open(file_path) as img:
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background

                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                img.save(file_path, 'JPEG', quality=85, optimize=True)
                logger.debug(f"save_uploaded_image: 图片压缩完成，尺寸: {img.size}")
        except Exception as img_error:
            logger.warning(f"save_uploaded_image: 图片处理失败: {img_error}")

        web_path = f"/static/images/{upload_type}/{filename}"
        logger.info(f"save_uploaded_image: 返回路径: {web_path}")
        return web_path

    except Exception as e:
        logger.error(f"save_uploaded_image: 图片保存失败: {e}", exc_info=True)
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.debug("save_uploaded_image: 已清理失败文件")
            except Exception:
                pass
        return None

def delete_image_file(image_path):
    """删除图片文件"""
    if not image_path:
        return
    
    try:
        # 移除开头的斜杠，转换为相对路径
        if image_path.startswith('/'):
            image_path = image_path[1:]
        
        # 获取应用根目录
        from flask import current_app
        app_root = os.path.dirname(current_app.instance_path)
        file_path = os.path.join(app_root, 'app', image_path)
        
        from flask import current_app as _app
        if os.path.exists(file_path):
            os.remove(file_path)
            _app.logger.info(f"delete_image_file: 删除文件成功: {file_path}")
        else:
            _app.logger.debug(f"delete_image_file: 文件不存在: {file_path}")
    except Exception as e:
        try:
            from flask import current_app as _app2
            _app2.logger.error(f"delete_image_file: 删除图片文件失败: {e}")
        except Exception:
            pass  # 无 app 上下文时静默失败


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """用 Haversine 公式计算两点球面距离，返回千米数（纯 Python，无 API 消耗）"""
    import math
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def haversine_bbox_half_degrees(user_lat: float, radius_km: float) -> Tuple[float, float]:
    """
    以 user_lat 为中心、radius_km 为半径的球面圆，其轴对齐外包矩形在经纬度上的「半宽」。
    用于先筛掉不可能在圆内的点，再对候选点调用 haversine（性能优化方案 §5.3）。
    """
    import math
    dlat = radius_km / 111.0
    cos_lat = max(math.cos(math.radians(user_lat)), 0.01)
    dlng = radius_km / (111.0 * cos_lat)
    return dlat, dlng


def is_outside_haversine_bbox(
    user_lat: float, user_lng: float, r_lat: float, r_lng: float, radius_km: float
) -> bool:
    """若 r 有坐标且肯定落在上述圆的外接矩形之外，则返回 True（可跳过 haversine）。"""
    dlat, dlng = haversine_bbox_half_degrees(user_lat, radius_km)
    return abs(r_lat - user_lat) > dlat or abs(r_lng - user_lng) > dlng


def amap_ip_locate(ip: str) -> Optional[Tuple[float, float, str]]:
    """
    调高德 IP 定位接口，返回 (lat, lng, city) 或 None。
    仅作兜底定位（浏览器拒绝 GPS 时使用），精度约市级。
    """
    import requests
    from flask import current_app
    key = current_app.config.get('AMAP_WEB_KEY', '')
    if not key:
        return None
    try:
        resp = requests.get(
            'https://restapi.amap.com/v3/ip',
            params={'key': key, 'ip': ip},
            timeout=5
        )
        data = resp.json()
        if data.get('status') != '1' or not data.get('rectangle'):
            return None
        # rectangle 格式：'lng1,lat1;lng2,lat2'（矩形对角线两点），取中心点
        pts = data['rectangle'].split(';')
        lng1, lat1 = map(float, pts[0].split(','))
        lng2, lat2 = map(float, pts[1].split(','))
        lat = (lat1 + lat2) / 2
        lng = (lng1 + lng2) / 2
        city = data.get('city') or data.get('province') or ''
        return lat, lng, city
    except Exception as e:
        try:
            current_app.logger.warning(f'amap_ip_locate 失败: {e}')
        except Exception:
            pass
        return None


def amap_regeocode(lat: float, lng: float) -> Optional[str]:
    """
    调高德逆地理编码接口，坐标 → 可读地址文字。
    返回格式化地址字符串，失败返回 None。
    """
    import requests
    from flask import current_app
    key = current_app.config.get('AMAP_WEB_KEY', '')
    if not key:
        return None
    try:
        resp = requests.get(
            'https://restapi.amap.com/v3/geocode/regeo',
            params={
                'key': key,
                'location': f'{lng},{lat}',
                'radius': 100,
                'extensions': 'base',
                'output': 'json'
            },
            timeout=5
        )
        data = resp.json()
        if data.get('status') != '1':
            return None
        return data.get('regeocode', {}).get('formatted_address')
    except Exception as e:
        try:
            current_app.logger.warning(f'amap_regeocode 失败: {e}')
        except Exception:
            pass
        return None


def create_image_directories():
    """创建必要的图片目录"""
    try:
        from flask import current_app
        app_root = os.path.dirname(current_app.instance_path)
        
        directories = [
            os.path.join(app_root, 'app', 'static', 'images', 'dishes'),
            os.path.join(app_root, 'app', 'static', 'images', 'restaurants'),
            os.path.join(app_root, 'app', 'static', 'images', 'logos'), 
            os.path.join(app_root, 'app', 'static', 'images', 'banners')
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    except Exception as e:
        # 备用方案：使用相对路径，BUG-17 修复：移除 print
        directories = [
            'app/static/images/dishes',
            'app/static/images/restaurants',
            'app/static/images/logos',
            'app/static/images/banners'
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True) 