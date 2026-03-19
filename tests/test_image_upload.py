#!/usr/bin/env python3
"""
图片上传功能测试脚本
用于测试和调试图片上传功能
"""

import os
import sys
from PIL import Image
import uuid

def create_test_image():
    """创建一个测试图片"""
    # 创建一个简单的测试图片
    img = Image.new('RGB', (600, 400), color=(255, 100, 100))
    
    # 在图片上画一些内容
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    
    # 添加英文文字（避免中文编码问题）
    draw.text((50, 50), "Test Image", fill=(255, 255, 255))
    draw.text((50, 100), "Dish Photo", fill=(255, 255, 255))
    draw.text((50, 150), f"ID: {str(uuid.uuid4())[:8]}", fill=(255, 255, 255))
    
    # 画一些形状
    draw.rectangle([50, 200, 250, 300], outline=(255, 255, 255), width=3)
    draw.ellipse([300, 200, 500, 350], outline=(255, 255, 255), width=3)
    
    return img

def test_directories():
    """测试目录创建"""
    print("=== 测试目录创建 ===")
    
    directories = [
        'app/static/images/dishes',
        'app/static/images/restaurants',
        'app/static/images/logos',
        'app/static/images/banners'
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✓ 目录创建成功: {directory}")
            
            # 检查目录是否可写
            test_file = os.path.join(directory, 'test.txt')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            print(f"✓ 目录可写: {directory}")
            
        except Exception as e:
            print(f"✗ 目录创建失败 {directory}: {e}")

def test_image_processing():
    """测试图片处理功能"""
    print("\n=== 测试图片处理 ===")
    
    try:
        # 创建测试图片
        img = create_test_image()
        print("✓ 测试图片创建成功")
        
        # 保存到dishes目录
        test_path = 'app/static/images/dishes/test_dish.jpg'
        os.makedirs(os.path.dirname(test_path), exist_ok=True)
        
        # 保存为JPEG
        img.save(test_path, 'JPEG', quality=85, optimize=True)
        print(f"✓ 图片保存成功: {test_path}")
        
        # 检查文件大小
        file_size = os.path.getsize(test_path)
        print(f"✓ 文件大小: {file_size} bytes")
        
        # 验证图片可以重新打开
        with Image.open(test_path) as test_img:
            print(f"✓ 图片验证成功: {test_img.size}, {test_img.mode}")
        
        return test_path
        
    except Exception as e:
        print(f"✗ 图片处理失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_web_access():
    """测试Web访问路径"""
    print("\n=== 测试Web访问路径 ===")
    
    test_files = [
        'app/static/images/dishes/test_dish.jpg',
        'app/static/css/style.css' if os.path.exists('app/static/css/style.css') else None
    ]
    
    for file_path in test_files:
        if file_path and os.path.exists(file_path):
            web_path = file_path.replace('app/', '/')
            print(f"✓ 文件存在: {file_path}")
            print(f"  Web路径: {web_path}")
        elif file_path:
            print(f"✗ 文件不存在: {file_path}")

def test_flask_app():
    """测试Flask应用配置"""
    print("\n=== 测试Flask应用配置 ===")
    
    try:
        # 尝试导入并创建应用
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app import create_app
        
        app = create_app()
        print("✓ Flask应用创建成功")
        
        # 检查配置
        with app.app_context():
            print(f"✓ 最大文件大小: {app.config.get('MAX_CONTENT_LENGTH', 'undefined')}")
            print(f"✓ 允许的扩展名: {app.config.get('ALLOWED_EXTENSIONS', 'undefined')}")
            print(f"✓ Secret Key: {'已配置' if app.config.get('SECRET_KEY') else '未配置'}")
            
            # 测试工具函数
            from app.utils import create_image_directories
            create_image_directories()
            print("✓ 图片目录创建函数执行成功")
            
    except Exception as e:
        print(f"✗ Flask应用测试失败: {e}")
        import traceback
        traceback.print_exc()

def cleanup_test_files():
    """清理测试文件"""
    print("\n=== 清理测试文件 ===")
    
    test_files = [
        'app/static/images/dishes/test_dish.jpg'
    ]
    
    for file_path in test_files:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"✓ 清理文件: {file_path}")
        except Exception as e:
            print(f"✗ 清理失败 {file_path}: {e}")

def main():
    """主测试函数"""
    print("🧪 图片上传功能测试开始\n")
    
    # 检查依赖
    try:
        import PIL
        print(f"✓ PIL/Pillow 版本: {PIL.__version__}")
    except ImportError:
        print("✗ 缺少 Pillow 库，请运行: pip install Pillow")
        return
    
    # 运行测试
    test_directories()
    test_image_path = test_image_processing()
    test_web_access()
    test_flask_app()
    
    print(f"\n🏁 测试完成!")
    
    # 询问是否清理测试文件
    if test_image_path and os.path.exists(test_image_path):
        print(f"\n📸 测试图片已保存到: {test_image_path}")
        print("您可以通过以下URL访问测试图片:")
        print(f"http://localhost:5000/static/images/dishes/test_dish.jpg")
        
        choice = input("\n是否删除测试文件? (y/N): ").lower()
        if choice == 'y':
            cleanup_test_files()

if __name__ == '__main__':
    main() 