# 影视影评分享系统

> 基于 Flask 框架的全功能 Web 影视影评分享平台，支持用户注册/登录、影视浏览、影评互动、好友社交、实时聊天与影视分享。

---

## 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| 后端框架 | Flask | 3.0 |
| 数据库 ORM | Flask-SQLAlchemy | 3.1 |
| 表单处理 | Flask-WTF / WTForms | 1.2 / 3.1 |
| 用户认证 | Flask-Login | 0.6 |
| 前端框架 | Bootstrap | 5.3 |
| 生产服务器 | Gunicorn | 21.2 |
| 开发数据库 | SQLite | — |
| 生产数据库 | MySQL（腾讯云 CloudBase） | — |
| 容器化 | Docker | — |
| 测试框架 | unittest + coverage | 7.4 |

---

## 项目结构

```
movie_review1/
├── app/                         # 应用包
│   ├── __init__.py              # 工厂函数 create_app()（含数据库自动迁移和种子数据）
│   ├── config.py                # 配置类（Config / ProductionConfig / TestingConfig）
│   ├── extensions.py            # Flask 扩展初始化（db / csrf / login_manager）
│   ├── models.py                # 数据库模型（7 张表）
│   ├── forms.py                 # WTForms 表单定义
│   ├── utils/                   # 工具模块
│   │   └── time.py              # 北京时间工具函数
│   ├── admin/                   # 管理后台蓝图
│   │   ├── __init__.py
│   │   └── views.py             # 管理员登录 / CRUD / 分类 / 影评 / 密码修改
│   ├── main/                    # 前台蓝图
│   │   ├── __init__.py
│   │   └── views.py             # 影视列表 / 详情 / 搜索 / 影评 / 点赞
│   ├── user/                    # 用户蓝图
│   │   ├── __init__.py
│   │   └── views.py             # 注册 / 登录 / 个人资料 / 头像 / 好友 / 聊天 / 注销
│   ├── templates/               # Jinja2 模板
│   │   ├── base.html            # 基础布局（导航栏含登录状态、消息提醒）
│   │   ├── admin/               # 后台模板（登录 / 仪表盘 / 影视 / 分类 / 影评）
│   │   ├── main/                # 前台模板（首页 / 详情 / 搜索）
│   │   └── user/                # 用户模板（注册 / 登录 / 资料 / 好友 / 聊天）
│   └── static/
│       ├── css/style.css
│       ├── js/main.js
│       └── uploads/
│           └── posters/         # 30 张 AI 生成的影视海报
├── tests/                       # 单元测试（91 个用例）
│   ├── test_models.py
│   ├── test_forms.py
│   └── test_views.py
├── Dockerfile                   # 腾讯云 CloudBase 容器镜像
├── run.py                       # 启动入口（自动检测云环境切换 MySQL/SQLite）
├── wsgi.py                      # WSGI 入口（Gunicorn 使用）
├── requirements.txt             # Python 依赖
├── .env.example                 # 环境变量示例
├── CLOUDBASE_部署指南.md         # 云端部署详细文档
└── README.md
```

---

## 数据库模型

```
Category (分类)
    │ 1
    │
    ▼ N
Movie (影视) ─────────────────────────── N ── Comment (影评)
    │                                              │
    │                                              │ N
    │ N                                            │ 1
    └──── Message.related_movie             User (用户)
                                                │   │
                              Friendship ───────┘   │
                              (好友关系)        N ── Comment
                                                    N ── Message（发/收）
```

| 模型 | 说明 | 关键字段 |
|------|------|---------|
| `Admin` | 管理员 | id, username, password_hash |
| `User` | 注册用户 | id, email, nickname, avatar_data, avatar_mime, password_hash |
| `Category` | 影视分类 | id, name |
| `Movie` | 影视条目 | id, title, intro, actors, release_date, rating, poster_url, trailer_url, likes |
| `Comment` | 影评 | id, content, author, movie_id(FK), user_id(FK, 可选) |
| `Friendship` | 好友关系 | id, requester_id(FK), receiver_id(FK), status(pending/accepted/rejected) |
| `Message` | 聊天消息 | id, sender_id(FK), receiver_id(FK), content, message_type, related_movie_id, is_read |
| `VerificationCode` | 邮箱验证码 | id, target, code, purpose, expires_at, used |

---

## 功能列表

### 🎬 影视浏览（前台）

| 功能 | 说明 |
|------|------|
| 影视列表 | 游客免登录浏览，按上架时间倒序，分页展示（每页 12 条） |
| 分类筛选 | 支持电影 / 电视剧 / 综艺 / 动漫四大分类 |
| 关键词搜索 | 按片名 / 主演模糊搜索，结果支持分页 |
| 影视详情 | 海报 / 简介 / 主演 / 上映时间 / 评分 / Bilibili 预告片嵌入 |
| 影视点赞 | AJAX 无刷新点赞，实时动画反馈 |
| 30 部影视 | 系统内置 30 部精选影视，含 AI 生成海报 + B 站预告片 |

### 👤 用户系统

| 功能 | 说明 |
|------|------|
| 邮箱注册 | QQ 邮箱 + 6 位验证码注册（5 分钟有效期） |
| 邮箱登录 | 邮箱 + 密码登录 |
| 修改资料 | 修改昵称、修改密码 |
| 头像上传 | 上传头像自动转 Base64 存入数据库（云端重新部署不丢失） |
| 账号注销 | 密码 + 输入"确认注销"文字双重确认，数据全部删除 |

### 💬 社交功能

| 功能 | 说明 |
|------|------|
| 发布影评 | 登录用户可在详情页发布影评（AJAX 无刷新），匿名用户也可留言 |
| 加好友 | 搜索用户 → 发送好友请求 → 对方接受/拒绝 |
| 好友管理 | 查看好友列表、撤回请求、删除好友 |
| 好友聊天 | 实时文字聊天（每 3 秒自动轮询刷新），消息已读标记 |
| 分享影视 | 从影视详情页一键分享给好友（发送带链接的分享消息） |
| 消息提醒 | 导航栏显示未读消息数量角标 |

### 🔧 管理后台

| 功能 | 说明 |
|------|------|
| 管理员登录 | 专属账号，密码 Werkzeug 哈希存储 |
| 影视 CRUD | 新增 / 编辑 / 删除影视条目，含海报上传 |
| 分类管理 | 新增 / 编辑 / 删除分类 |
| 影评管理 | 查看全站影评，删除违规评论 |
| 修改密码 | 管理员可在后台修改自己的登录密码 |

---

## 快速开始

### 1. 克隆代码

```bash
git clone https://github.com/LYK-0309/lhs623.git
cd lhs623
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量（可选）

```bash
# 复制示例配置
cp .env.example .env

# 编辑 .env 填入你的 QQ 邮箱授权码（不配置则验证码直接显示在页面上）
MAIL_USERNAME=你的QQ邮箱@qq.com
MAIL_PASSWORD=你的SMTP授权码
SECRET_KEY=your-secret-key
```

### 4. 启动应用

```bash
python run.py
```

浏览器访问：**http://localhost:5000**

### 5. 默认账号

| 账号类型 | 用户名/邮箱 | 密码 |
|----------|-------------|------|
| 管理员 | `admin` | `admin123` |

> 首次启动自动创建管理员账号、4 个分类、30 部影视种子数据。

---

## 运行测试

```bash
# 运行所有单元测试
python -m unittest discover tests -v

# 运行覆盖率测试
python -m coverage run -m unittest discover tests -v
python -m coverage report --include="app/*"

# 生成 HTML 覆盖率报告
python -m coverage html --include="app/*" -d coverage_html
```

### 测试结果

- **测试用例总数**：91 个
- **通过率**：100%
- **代码覆盖率**：99%

---

## 腾讯云 CloudBase 部署

### 快速部署步骤

1. 将代码推送到 GitHub 仓库
2. 登录 [腾讯云 CloudBase 控制台](https://console.cloud.tencent.com/tcb)
3. 云托管 → 新建服务 → 关联 GitHub 仓库
4. 配置以下**环境变量**：

| 变量名 | 说明 |
|--------|------|
| `SECRET_KEY` | Flask 密钥（随机字符串） |
| `MAIL_USERNAME` | QQ 邮箱（发验证码用） |
| `MAIL_PASSWORD` | QQ 邮箱 SMTP 授权码 |
| `MYSQL_ADDRESS` | MySQL 主机地址（绑定数据库后自动注入） |
| `MYSQL_PASSWORD` | MySQL 密码（绑定数据库后自动注入） |

5. 服务端口：**80**（与 Dockerfile 一致）
6. 点击部署，等待 3-5 分钟

### 数据持久化

**⚠️ 重要：** 必须绑定 MySQL 数据库，否则重新部署后用户数据会丢失。

- 在 CloudBase 控制台创建 MySQL 实例（数据库名：`movie_review`）
- 将 MySQL 绑定到云托管服务
- 应用启动时自动创建表结构，无需手动建表

### 自动部署

关联 GitHub 仓库后，每次执行以下操作即可自动部署：

```bash
git add .
git commit -m "更新：修复了某个功能"
git push origin main
```

详细部署文档参见 [CLOUDBASE_部署指南.md](./CLOUDBASE_部署指南.md)。

---

## 特色设计

- **云端兼容**：头像使用 Base64 存入数据库，重新部署不丢失
- **优雅降级**：MySQL 连接失败时自动回退到 SQLite（5 次重试后降级）
- **演示模式**：未配置邮件时，验证码直接显示在页面，方便本地测试
- **自动迁移**：`app/__init__.py` 启动时自动检测并添加缺失的数据库列（幂等）
- **北京时间**：所有时间字段统一使用 Asia/Shanghai 时区
- **CSRF 保护**：所有表单自动启用 CSRF Token 防护

---

## 截图预览

> 系统内置 30 部精选影视，涵盖电影、电视剧、综艺、动漫四大分类，均配有 AI 生成海报和 B 站预告片。

| 页面 | 路由 |
|------|------|
| 首页 | `/` |
| 影视详情 | `/movie/<id>` |
| 搜索结果 | `/search?q=关键词` |
| 用户注册 | `/user/register` |
| 我的好友 | `/user/friends` |
| 好友聊天 | `/user/chat/<friend_id>` |
| 管理后台 | `/admin/dashboard` |
