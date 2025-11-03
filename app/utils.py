import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
from PIL import Image
import hashlib

def setup_logging(app):
    """配置日志系统"""
    if not app.debug:
        # 确保日志目录存在
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # 设置文件日志处理器
        file_handler = RotatingFileHandler(
            'logs/meituan.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
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

# 允许的图片格式
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    if not file or not file.filename:
        print("没有文件或文件名为空")
        return None
    
    if not allowed_file(file.filename):
        print(f"不支持的文件格式: {file.filename}")
        return None
    
    try:
        # 生成唯一文件名
        filename = generate_unique_filename(file.filename)
        print(f"生成文件名: {filename}")
        
        # 获取应用根目录下的static目录
        from flask import current_app
        app_root = os.path.dirname(current_app.instance_path)
        upload_dir = os.path.join(app_root, 'app', 'static', 'images', upload_type)
        
        # 确保目录存在
        os.makedirs(upload_dir, exist_ok=True)
        print(f"保存目录: {upload_dir}")
        
        # 完整文件路径
        file_path = os.path.join(upload_dir, filename)
        print(f"完整文件路径: {file_path}")
        
        # 保存原始文件
        file.save(file_path)
        print("文件保存成功")
        
        # 使用PIL压缩和调整图片大小
        try:
            with Image.open(file_path) as img:
                print(f"原始图片信息: {img.size}, {img.mode}")
                
                # 转换为RGB模式（处理RGBA等格式）
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                    print("图片模式转换完成")
                
                # 调整图片大小（保持比例）
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                print(f"图片尺寸调整后: {img.size}")
                
                # 保存压缩后的图片
                img.save(file_path, 'JPEG', quality=85, optimize=True)
                print("图片压缩保存完成")
        except Exception as img_error:
            print(f"图片处理失败: {img_error}")
            # 如果图片处理失败，但文件已保存，仍然返回路径
        
        # 返回相对路径（用于数据库存储和Web访问）
        web_path = f"/static/images/{upload_type}/{filename}"
        print(f"返回的Web路径: {web_path}")
        return web_path
        
    except Exception as e:
        print(f"图片保存失败: {e}")
        import traceback
        traceback.print_exc()
        # 如果保存失败，删除可能创建的文件
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print("清理失败文件")
            except:
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
        
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"删除文件成功: {file_path}")
        else:
            print(f"文件不存在: {file_path}")
    except Exception as e:
        print(f"删除图片文件失败: {e}")

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
            print(f"创建目录: {directory}")
            
    except Exception as e:
        print(f"创建图片目录失败: {e}")
        # 备用方案：使用相对路径
        directories = [
            'app/static/images/dishes',
            'app/static/images/restaurants',
            'app/static/images/logos', 
            'app/static/images/banners'
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            print(f"使用相对路径创建目录: {directory}") 