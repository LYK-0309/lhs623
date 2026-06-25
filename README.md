# 影视影评分享系统

基于 Flask 框架的 Web 影视影评分享平台，支持前台浏览、分类筛选、关键词搜索和访客影评互动。

## 技术栈

- **后端框架**：Flask 3.0
- **数据库 ORM**：Flask-SQLAlchemy 3.1（SQLite）
- **表单处理**：Flask-WTF 1.2（CSRF 保护）
- **前端框架**：Bootstrap 5.3（响应式布局）
- **测试框架**：unittest + coverage 7.4

## 项目结构（包结构 + 蓝图 + 工厂函数）

```
movie_review/
├── app/                        # 应用包
│   ├── __init__.py             # 工厂函数 create_app()
│   ├── config.py               # 配置类（开发/测试）
│   ├── extensions.py           # Flask 扩展初始化
│   ├── models.py               # 数据库模型（一对多关系）
│   ├── forms.py                # WTForms 表单定义
│   ├── admin/                  # 管理后台蓝图
│   │   ├── __init__.py
│   │   └── views.py            # 登录/CRUD/分类/影评管理
│   ├── main/                   # 前台蓝图
│   │   ├── __init__.py
│   │   └── views.py            # 影视列表/详情/搜索/影评
│   ├── templates/              # Jinja2 模板
│   │   ├── base.html           # 基础布局模板
│   │   ├── admin/              # 后台模板
│   │   │   ├── login.html
│   │   │   ├── dashboard.html
│   │   │   ├── movie_list.html
│   │   │   ├── movie_form.html
│   │   │   ├── category_list.html
│   │   │   └── comment_list.html
│   │   └── main/               # 前台模板
│   │       ├── index.html
│   │       ├── detail.html
│   │       ├── search.html
│   │       └── _pagination.html
│   └── static/
│       ├── css/style.css
│       └── js/main.js
├── tests/                      # 单元测试
│   ├── __init__.py
│   ├── test_models.py          # 模型层测试（23个用例）
│   ├── test_forms.py           # 表单验证测试（21个用例）
│   └── test_views.py           # 视图层测试（31个用例）
├── run.py                      # 启动入口
├── requirements.txt            # Python 依赖
└── README.md
```

## 数据库模型（一对多关系）

```
Category (分类)  1 ──── N  Movie (影视)  1 ──── N  Comment (影评)
                                  │
                              N : 1
                                  │
                             Category (分类)
```

- **admin**：id, username, password_hash（密码哈希存储）
- **category**：id, name ← **一对多**：一个分类对应多部影视
- **movie**：id, title, intro, actors, release_date, rating, poster_url, likes, category_id(FK), created_at
- **comment**：id, content, author, created_at, movie_id(FK) ← **一对多**：一部影视对应多条影评

## 8 项核心功能

| 功能 | 说明 |
|------|------|
| 用户认证 | 管理员专属账号登录/注销，密码 Werkzeug 哈希存储 |
| 管理后台 | 路由权限拦截（login_required 装饰器），统一管理影视/分类/影评 |
| 影视 CRUD + 分页 | 管理员增删改查影视条目，后台列表分页 |
| 前台影视列表 | 游客免登录浏览，按上架时间倒序，支持分页 |
| 影视详情页 | 名称、简介、主演、上映时间、评分等完整信息 |
| 分类筛选 | 电影/电视剧/综艺/动漫分类浏览 |
| 关键词搜索 | 按影视名称/主演搜索，搜索结果分页 |
| 访客互动 | 详情页发布影评留言（AJAX 无刷新），管理员可删除违规评论 |

## 拓展加分功能

- ✅ **影视点赞**：AJAX 无刷新点赞，动画反馈
- ✅ **AJAX 无刷新发表影评**：影评即时展示，无需刷新页面
- ✅ **默认数据种子**：首次启动自动创建管理员账号和默认分类

## 快速开始

### 1. 安装依赖

```bash
cd movie_review
pip install -r requirements.txt
```

### 2. 启动应用

```bash
python run.py
```

浏览器访问：http://localhost:5000

### 3. 默认管理员账号

- 用户名：`admin`
- 密码：`admin123`

### 4. 运行测试

```bash
# 运行所有单元测试
python -m unittest discover tests -v

# 运行覆盖率测试
python -m coverage run -m unittest discover tests -v
python -m coverage report --include="app/*"
python -m coverage html --include="app/*" -d coverage_html
```

## 测试结果

- **测试用例总数**：75 个
- **通过率**：100%（全部通过）
- **代码覆盖率**：99%（远超 ≥80% 要求）

```
Name                    Stmts   Miss  Cover
-------------------------------------------
app\__init__.py            27      0   100%
app\admin\views.py        156      2    99%
app\config.py              14      0   100%
app\extensions.py           4      0   100%
app\forms.py               32      0   100%
app\main\views.py          67      3    96%
app\models.py              47      0   100%
-------------------------------------------
TOTAL                     347      5    99%
```

## 在 PyCharm 中运行

1. 用 PyCharm 打开 `movie_review/` 目录
2. 在 Terminal 中执行 `pip install -r requirements.txt`
3. 右键 `run.py` → Run 'run'
4. 浏览器访问 http://localhost:5000
