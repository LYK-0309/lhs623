"""应用配置 — 支持 .env 加载，QQ 邮箱 SMTP 验证码发送"""
import os
from pathlib import Path

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))

# 加载 .env 文件
_dotenv_path = os.path.join(PROJECT_DIR, '.env')
if os.path.exists(_dotenv_path):
    from dotenv import load_dotenv
    load_dotenv(_dotenv_path)
    print(f'[Config] 已加载环境变量: {_dotenv_path}')
else:
    print('[Config] 未找到 .env 文件，使用默认值（验证码将无法真实发送）')
    print(f'[Config] 请复制 .env.example 为 .env 并填入真实配置')


def _env_bool(name, default=False):
    val = os.environ.get(name, '').strip().lower()
    if val in ('1', 'true', 'yes', 'on'):
        return True
    if val in ('0', 'false', 'no', 'off'):
        return False
    return default


class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(PROJECT_DIR, 'movie_review.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 分页配置
    MOVIES_PER_PAGE = 12
    COMMENTS_PER_PAGE = 10
    ADMIN_MOVIES_PER_PAGE = 10

    # 头像上传配置
    UPLOAD_FOLDER = os.path.join(PROJECT_DIR, 'uploads', 'avatars')
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024   # 最大 2MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # ─── QQ 邮箱 SMTP 配置（发验证码用）─────────────────
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.qq.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 465)
    MAIL_USE_SSL = _env_bool('MAIL_USE_SSL', True)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or ''
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or ''
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or MAIL_USERNAME

    @classmethod
    def init_app(cls, app):
        """将 MAIL_ENABLED 写入 app.config"""
        app.config['MAIL_ENABLED'] = bool(
            app.config.get('MAIL_USERNAME') and app.config.get('MAIL_PASSWORD')
        )


class ProductionConfig(Config):
    """生产环境配置 — 腾讯云 CloudBase 云托管 MySQL"""
    from urllib.parse import quote_plus

    MYSQL_HOST = os.environ.get('MYSQL_ADDRESS', '127.0.0.1')
    MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
    MYSQL_USER = os.environ.get('MYSQL_USERNAME', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DB = os.environ.get('MYSQL_DATABASE', 'movie_review')

    # URL 编码密码，防止特殊字符（如 @、#、% 等）破坏连接字符串
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{quote_plus(MYSQL_USER)}:{quote_plus(MYSQL_PASSWORD)}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
    )

    # 上传路径：容器内工作目录
    UPLOAD_FOLDER = os.path.join(PROJECT_DIR, 'uploads', 'avatars')

    # 生产环境关闭 DEBUG
    DEBUG = False


class TestingConfig(Config):
    """测试配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    MOVIES_PER_PAGE = 5
    UPLOAD_FOLDER = os.path.join(PROJECT_DIR, 'tests', 'temp_uploads')
    MAIL_USERNAME = 'test@example.com'
    MAIL_PASSWORD = 'test-password-no-real-send'
