"""WSGI 入口文件 - 用于生产环境部署"""
from app import create_app

# 创建应用实例
app = create_app()

if __name__ == "__main__":
    app.run()
