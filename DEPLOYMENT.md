# 影视影评分享系统 - 部署指南

本文档提供多种部署方案，你可以根据自己的需求选择合适的方案。

## 目录
- [方案对比](#方案对比)
- [方案一：本地生产环境部署](#方案一本地生产环境部署)
- [方案二：部署到 Render（免费推荐）](#方案二部署到-render免费推荐)
- [方案三：部署到 Railway](#方案三部署到-railway)
- [方案四：部署到云服务器](#方案四部署到云服务器)
- [常见问题](#常见问题)

---

## 方案对比

| 方案 | 难度 | 费用 | 适合场景 |
|------|------|------|----------|
| 本地生产环境 | ⭐ | 免费 | 本地测试、演示 |
| Render | ⭐⭐ | 免费（有休眠） | 个人项目、演示 |
| Railway | ⭐⭐ | $5/月免费额度 | 小型生产环境 |
| 云服务器 | ⭐⭐⭐ | ¥100+/月 | 正式生产环境 |

---

## 方案一：本地生产环境部署

### 1. 安装依赖

```bash
cd movie_review1
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，修改以下配置：
- `SECRET_KEY`: 设置为随机字符串
- `FLASK_ENV`: 设置为 `production`
- `FLASK_DEBUG`: 设置为 `False`

### 3. 使用 Gunicorn 启动（推荐）

```bash
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

参数说明：
- `-w 4`: 使用 4 个 worker 进程
- `-b 0.0.0.0:5000`: 监听所有网络接口的 5000 端口

### 4. 访问应用

浏览器访问：http://localhost:5000

---

## 方案二：部署到 Render（免费推荐）

Render 提供免费的 Web 服务托管，适合个人项目和演示。

### 1. 准备工作

1. 注册 [Render](https://render.com/) 账号
2. 将代码推送到 GitHub 仓库

### 2. 创建 Web Service

1. 登录 Render，点击 **New +** → **Web Service**
2. 连接你的 GitHub 仓库
3. 填写配置信息：
   - **Name**: `movie-review-system`（可自定义）
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:app`

### 3. 配置环境变量

在 Render 的 **Environment** 选项卡中添加以下环境变量：

```
SECRET_KEY = [随机字符串]
FLASK_ENV = production
FLASK_DEBUG = False
DATABASE_URL = [Render 会自动提供 PostgreSQL 数据库]
```

### 4. 部署

点击 **Create Web Service**，Render 会自动构建和部署你的应用。

部署完成后，Render 会提供一个 `.onrender.com` 的域名供你访问。

### 注意事项

- Render 免费套餐有休眠机制：15 分钟无访问会自动休眠，下次访问需要等待 30-50 秒唤醒
- 免费套餐每月有 750 小时的运行时间限制
- 需要使用 PostgreSQL 数据库（Render 提供免费 PostgreSQL 数据库）

---

## 方案三：部署到 Railway

Railway 提供简单的部署体验，有 $5/月的免费额度。

### 1. 准备工作

1. 注册 [Railway](https://railway.app/) 账号
2. 将代码推送到 GitHub 仓库

### 2. 创建项目

1. 登录 Railway，点击 **New Project**
2. 选择 **Deploy from GitHub repo**
3. 选择你的仓库

### 3. 配置环境变量

在 Railway 的 **Variables** 选项卡中添加环境变量：
```
SECRET_KEY = [随机字符串]
FLASK_ENV = production
FLASK_DEBUG = False
```

### 4. 部署

Railway 会自动检测 Python 项目并部署。

部署完成后，Railway 会提供一个 `.up.railway.app` 的域名供你访问。

---

## 方案四：部署到云服务器

以腾讯云/阿里云为例，介绍如何在云服务器上部署。

### 1. 购买并配置服务器

1. 购买云服务器（推荐 2核4G 配置）
2. 配置安全组，开放 80、443、5000 等端口
3. 使用 SSH 连接到服务器

### 2. 安装依赖

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Python 3.12
sudo apt install python3.12 python3-pip python3-venv -y

# 安装 Nginx
sudo apt install nginx -y

# 安装 PostgreSQL（可选，推荐使用 PostgreSQL）
sudo apt install postgresql postgresql-contrib -y
```

### 3. 部署应用

```bash
# 创建项目目录
sudo mkdir -p /var/www/movie_review
sudo chown $USER:$USER /var/www/movie_review
cd /var/www/movie_review

# 克隆代码（或上传代码）
git clone <your-repo-url> .

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
nano .env  # 编辑配置文件

# 使用 Gunicorn 测试运行
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

### 4. 使用 Systemd 管理进程

创建 Systemd 服务文件：

```bash
sudo nano /etc/systemd/system/movie-review.service
```

写入以下内容：

```ini
[Unit]
Description=Movie Review System
After=network.target

[Service]
User=your-username
Group=www-data
WorkingDirectory=/var/www/movie_review
Environment="PATH=/var/www/movie_review/venv/bin"
ExecStart=/var/www/movie_review/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl start movie-review
sudo systemctl enable movie-review
```

### 5. 配置 Nginx 反向代理

创建 Nginx 配置文件：

```bash
sudo nano /etc/nginx/sites-available/movie-review
```

写入以下内容：

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名或 IP 地址

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /var/www/movie_review/app/static;
    }

    location /uploads {
        alias /var/www/movie_review/uploads;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/movie-review /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. 配置域名（可选）

如果你有域名，可以在域名服务商处配置 A 记录，将域名指向服务器 IP 地址。

### 7. 配置 HTTPS（可选但推荐）

使用 Let's Encrypt 免费证书：

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

---

## 常见问题

### 1. 数据库迁移问题

如果从 SQLite 迁移到 PostgreSQL，需要使用 `pgloader` 或其他工具迁移数据。

### 2. 静态文件无法访问

确保 Nginx 配置中正确设置了静态文件路径。

### 3. 邮件发送失败

确保在 `.env` 文件中正确配置了 QQ 邮箱的 SMTP 设置，并获取了授权码。

### 4. 上传文件失败

确保上传目录有正确的权限：

```bash
sudo chown -R $USER:www-data uploads/
sudo chmod -R 755 uploads/
```

### 5. 应用无法启动

检查日志：

```bash
# Systemd 日志
sudo journalctl -u movie-review

# Nginx 日志
sudo tail -f /var/log/nginx/error.log
```

---

## 部署检查清单

- [ ] 已安装所有依赖
- [ ] 已配置环境变量（`.env` 文件）
- [ ] 已生成随机 `SECRET_KEY`
- [ ] 已设置 `FLASK_ENV=production`
- [ ] 已设置 `FLASK_DEBUG=False`
- [ ] 数据库已初始化
- [ ] 静态文件可访问
- [ ] 上传目录权限正确
- [ ] 邮件配置正确（如需使用邮件功能）

---

## 联系方式

如遇部署问题，请检查：
1. 日志文件
2. 环境变量配置
3. 数据库连接
4. 端口占用情况

祝部署顺利！
