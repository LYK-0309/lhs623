# ============================================================
# 影视影评分享系统 - Docker 镜像
# 部署到腾讯云 CloudBase 云托管 (CloudRun)
# ============================================================

FROM python:3.11-slim

# 设置时区为上海
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    # SQLite support (lightweight backup)
    libsqlite3-0 \
    # MySQL client for pymysql/psycopg2
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# 设定工作目录
WORKDIR /app

# 先复制依赖文件，利用 Docker 缓存层
COPY requirements.txt .

# 使用腾讯云镜像源加速 pip
RUN pip config set global.index-url https://mirrors.cloud.tencent.com/pypi/simple \
    && pip config set global.trusted-host mirrors.cloud.tencent.com \
    && pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 暴露端口（CloudBase 云托管默认使用 80 端口）
EXPOSE 80

# 使用 gunicorn 启动（生产级 WSGI 服务器）
# bind 0.0.0.0:80 必须与 CloudBase 云托管配置的端口一致
CMD ["gunicorn", "run:app", "--bind", "0.0.0.0:80", "--workers", "2", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]
