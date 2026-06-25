"""影视影评分享系统 - 启动入口"""
import os
import sys
from app import create_app
from app.config import Config, ProductionConfig

# 根据环境选择配置
if os.environ.get('CLOUD_ENV') or os.environ.get('MYSQL_ADDRESS'):
    # 云托管环境（检测到 MySQL 环境变量）
    config = ProductionConfig
    print('[Run] 使用生产环境配置 (MySQL)')
else:
    config = Config
    print('[Run] 使用开发环境配置 (SQLite)')

app = create_app(config)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug, host='0.0.0.0', port=port)
