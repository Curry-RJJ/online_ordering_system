import os

class Config:
    """MySQL数据库配置 - 适配PHPStudy环境"""
    
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'meituan-waimai-secret-key-2024'
    
    # MySQL数据库配置（PHPStudy默认配置）
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_PORT = os.environ.get('MYSQL_PORT') or 3306
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or 'root'  # PHPStudy默认密码
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE') or 'meituan_waimai'
    
    # SQLAlchemy配置
    SQLALCHEMY_DATABASE_URI = (
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@'
        f'{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4'
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'echo': False  # 设置为True可以看到SQL语句
    }

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'echo': True  # 开发环境显示SQL语句
    }

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    
    # 生产环境建议使用环境变量
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-production-secret-key'
    
    # 生产环境数据库配置
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_PORT = os.environ.get('MYSQL_PORT') or 3306
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'meituan_user'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or 'your-secure-password'
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE') or 'meituan_waimai'
    
    SQLALCHEMY_DATABASE_URI = (
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@'
        f'{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4'
    )

# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 