"""影视影评分享系统 - 应用工厂"""
import os
from flask import Flask
from app.config import Config
from app.extensions import db, csrf, login_manager

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))


def create_app(config_class=Config):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 初始化扩展
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    # 处理未授权请求（AJAX 请求返回 JSON）
    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import request, jsonify, flash, redirect, url_for
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': '请先登录后再操作'}), 401
        flash('请先登录', 'warning')
        return redirect(url_for('user.login'))

    # 计算 MAIL_ENABLED / SMS_ENABLED 写入 app.config
    if hasattr(config_class, 'init_app'):
        config_class.init_app(app)

    # 注册蓝图
    from app.main.views import main_bp
    from app.admin.views import admin_bp
    from app.user.views import user_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(user_bp, url_prefix='/user')

    # 创建上传文件夹
    import os
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # 全局 before_request：加载分类数据到导航栏
    @app.before_request
    def load_nav_categories():
        from flask import g, request
        from app.models import Category
        if request.endpoint and not request.endpoint.startswith('static'):
            g.all_categories = Category.query.order_by(Category.id).all()

    # 提供头像文件的静态访问
    @app.route('/uploads/avatars/<filename>')
    def avatar_file(filename):
        from flask import send_from_directory
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # 提供海报文件的静态访问
    @app.route('/uploads/posters/<filename>')
    def poster_file(filename):
        from flask import send_from_directory
        posters_dir = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'posters')
        return send_from_directory(posters_dir, filename)

    # 创建数据库表（带重试，容器启动时 MySQL 可能还没就绪）
    import time
    max_retries = 5
    db_connected = False
    for attempt in range(1, max_retries + 1):
        try:
            with app.app_context():
                db.create_all()
                _migrate_db(app)  # 执行数据库迁移
                _seed_data(app)
            print(f'[Init] 数据库初始化成功 (尝试 {attempt}/{max_retries})')
            db_connected = True
            break
        except Exception as e:
            print(f'[Init] 数据库初始化失败 (尝试 {attempt}/{max_retries}): {e}')
            if attempt < max_retries:
                wait = attempt * 3
                print(f'[Init] 等待 {wait} 秒后重试...')
                time.sleep(wait)
            else:
                print('[Init] 数据库初始化最终失败，尝试使用 SQLite 降级模式')

    # 如果 MySQL 连接失败，自动回退到 SQLite
    if not db_connected:
        try:
            sqlite_uri = 'sqlite:///' + os.path.join(PROJECT_DIR, 'movie_review.db')
            app.config['SQLALCHEMY_DATABASE_URI'] = sqlite_uri
            # 重新初始化数据库连接
            db.init_app(app)
            with app.app_context():
                db.create_all()
                _seed_data(app)
            print(f'[Init] SQLite 降级模式启动成功: {sqlite_uri}')
        except Exception as e2:
            print(f'[Init] SQLite 也失败了: {e2}')

    return app


def _migrate_db(app):
    """数据库迁移：添加缺失的列和表（幂等）"""
    from sqlalchemy import text, inspect as sa_inspect

    try:
        inspector = sa_inspect(db.engine)
        existing_tables = inspector.get_table_names()

        # 1. 为 user 表添加新列（SQLite 兼容）
        if 'user' in existing_tables:
            columns = [col['name'] for col in inspector.get_columns('user')]
            with db.engine.connect() as conn:
                if 'avatar_data' not in columns:
                    conn.execute(text('ALTER TABLE user ADD COLUMN avatar_data TEXT'))
                    conn.commit()
                    print('[Migrate] 已添加 user.avatar_data 列')
                if 'avatar_mime' not in columns:
                    conn.execute(text('ALTER TABLE user ADD COLUMN avatar_mime VARCHAR(64)'))
                    conn.commit()
                    print('[Migrate] 已添加 user.avatar_mime 列')

        # 2. 为 movie 表添加新列（actors / release_date / trailer_url）
        if 'movie' in existing_tables:
            movie_cols = [col['name'] for col in inspector.get_columns('movie')]
            with db.engine.connect() as conn:
                if 'actors' not in movie_cols:
                    conn.execute(text('ALTER TABLE movie ADD COLUMN actors VARCHAR(256)'))
                    conn.commit()
                    print('[Migrate] 已添加 movie.actors 列')
                if 'release_date' not in movie_cols:
                    conn.execute(text('ALTER TABLE movie ADD COLUMN release_date DATE'))
                    conn.commit()
                    print('[Migrate] 已添加 movie.release_date 列')
                if 'trailer_url' not in movie_cols:
                    conn.execute(text('ALTER TABLE movie ADD COLUMN trailer_url VARCHAR(512)'))
                    conn.commit()
                    print('[Migrate] 已添加 movie.trailer_url 列')
                if 'likes' not in movie_cols:
                    conn.execute(text('ALTER TABLE movie ADD COLUMN likes INTEGER DEFAULT 0'))
                    conn.commit()
                    print('[Migrate] 已添加 movie.likes 列')

        # 4. 创建 friendship 表（如果不存在）
        if 'friendship' not in existing_tables:
            with db.engine.connect() as conn:
                conn.execute(text('''
                    CREATE TABLE IF NOT EXISTS friendship (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        requester_id INTEGER NOT NULL,
                        receiver_id INTEGER NOT NULL,
                        status VARCHAR(16) NOT NULL DEFAULT 'pending',
                        created_at DATETIME,
                        updated_at DATETIME
                    )
                '''))
                conn.commit()
                print('[Migrate] 已创建 friendship 表')

        # 5. 创建 message 表（如果不存在）
        if 'message' not in existing_tables:
            with db.engine.connect() as conn:
                conn.execute(text('''
                    CREATE TABLE IF NOT EXISTS message (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sender_id INTEGER NOT NULL,
                        receiver_id INTEGER NOT NULL,
                        content TEXT NOT NULL,
                        message_type VARCHAR(32) DEFAULT 'text',
                        related_movie_id INTEGER,
                        created_at DATETIME,
                        is_read BOOLEAN DEFAULT 0
                    )
                '''))
                conn.commit()
                print('[Migrate] 已创建 message 表')

        print('[Migrate] 数据库迁移完成')
    except Exception as e:
        print(f'[Migrate] 迁移失败（可忽略）: {e}')


def _seed_data(app):
    """初始化种子数据（幂等：重复调用不会报错）"""
    from app.models import Admin, Category, Movie
    from sqlalchemy.exc import IntegrityError

    try:
        # 创建默认管理员账号
        if Admin.query.count() == 0:
            admin = Admin(username='admin')
            admin.set_password('admin123')
            db.session.add(admin)

        # 创建默认分类
        default_categories = ['电影', '电视剧', '综艺', '动漫']
        cat_map = {}
        for cat_name in default_categories:
            cat = Category.query.filter_by(name=cat_name).first()
            if cat is None:
                cat = Category(name=cat_name)
                db.session.add(cat)
                db.session.flush()
            cat_map[cat_name] = cat.id

        # 创建30部影视数据（仅当数据库为空时）
        if Movie.query.count() == 0:
            movies_data = [
                {'title': '流浪地球2', 'category_id': cat_map['电影'], 'poster_url': '/uploads/posters/poster_01.png', 'trailer_url': '//player.bilibili.com/player.html?bvid=BV1K8411T7ev&page=1&autoplay=0&danmaku=0&high_quality=1', 'rating': 8.3, 'actors': '吴京, 刘德华, 李雪健, 沙溢', 'release_date': '2023-01-22', 'intro': '太阳即将毁灭，人类在地球表面建造了大量推进器，将地球推离太阳系。吴京、刘德华联袂出演，中国科幻的里程碑之作。'},
                {'title': '满江红', 'category_id': cat_map['电影'], 'poster_url': '/uploads/posters/poster_02.png', 'trailer_url': '//player.bilibili.com/player.html?bvid=BV1AR4y1a7kf&page=1&autoplay=0&danmaku=0&high_quality=1', 'rating': 8.0, 'actors': '沈腾, 易烊千玺, 张译, 雷佳音', 'release_date': '2023-01-22', 'intro': '南宋绍兴年间，岳飞死后四年，一场惊天谜局悄然展开。张艺谋导演，悬疑与喜剧完美融合。'},
                {'title': '你好，李焕英', 'category_id': cat_map['电影'], 'poster_url': '/uploads/posters/poster_03.png', 'trailer_url': '//player.bilibili.com/player.html?bvid=BV1F5411E7o9&page=1&autoplay=0&danmaku=0&high_quality=1', 'rating': 8.2, 'actors': '贾玲, 张小斐, 沈腾, 陈赫', 'release_date': '2021-02-12', 'intro': '贾晓玲意外穿越到1981年，与年轻时的母亲成为好友。贾玲首部导演作品，票房破54亿。'},
                {'title': '长津湖', 'category_id': cat_map['电影'], 'poster_url': '/uploads/posters/poster_04.png', 'trailer_url': '//player.bilibili.com/player.html?epid=350065&autoplay=0&danmaku=0&high_quality=1', 'rating': 7.9, 'actors': '吴京, 易烊千玺, 段奕宏, 朱亚文', 'release_date': '2021-09-30', 'intro': '1950年志愿军入朝参战，在长津湖战役中以钢铁意志与美军殊死搏斗。史诗战争巨制。'},
                {'title': '封神第一部：朝歌风云', 'category_id': cat_map['电影'], 'poster_url': '/uploads/posters/poster_05.png', 'trailer_url': '//player.bilibili.com/player.html?bvid=BV1bp4y1A7Ww&page=1&autoplay=0&danmaku=0&high_quality=1', 'rating': 7.8, 'actors': '费翔, 黄渤, 李雪健, 夏雨', 'release_date': '2023-07-20', 'intro': '商王殷寿勾连狐妖妲己，西伯侯之子姬发踏上斩神封神之路。乌尔善导演奇幻史诗。'},
                {'title': '消失的她', 'category_id': cat_map['电影'], 'poster_url': '/uploads/posters/poster_06.png', 'trailer_url': '//player.bilibili.com/player.html?bvid=BV1zc411u7aS&page=1&autoplay=0&danmaku=0&high_quality=1', 'rating': 7.0, 'actors': '朱一龙, 倪妮, 文咏珊', 'release_date': '2023-06-22', 'intro': '何非在海岛旅游途中声称妻子失踪，一个婚姻谎局逐渐浮出水面。朱一龙、倪妮主演悬疑片。'},
                {'title': '奥本海默', 'category_id': cat_map['电影'], 'poster_url': '/uploads/posters/poster_07.png', 'trailer_url': '//player.bilibili.com/player.html?bvid=BV1oh4y1J7MH&page=1&autoplay=0&danmaku=0&high_quality=1', 'rating': 8.9, 'actors': '基里安·墨菲, 艾米莉·布朗特, 小罗伯特·唐尼', 'release_date': '2023-08-30', 'intro': '原子弹之父奥本海默主导曼哈顿计划，研发核武器后却遭受政治迫害。诺兰执导奥斯卡最佳影片。'},
                {'title': '狂飙', 'category_id': cat_map['电视剧'], 'poster_url': '/uploads/posters/poster_08.png', 'trailer_url': '//player.bilibili.com/player.html?bvid=BV1xM4y1E7eH&page=1&autoplay=0&danmaku=0&high_quality=1', 'rating': 9.0, 'actors': '张译, 张颂文, 李一桐, 高启强', 'release_date': '2023-01-14', 'intro': '刑警安欣与鱼贩高启强跨越20年的正邪较量，扫黑除恶题材现象级大剧。张颂文、张译主演。'},
                {'title': '三体', 'category_id': cat_map['电视剧'], 'poster_url': '/uploads/posters/poster_09.png', 'trailer_url': '//player.bilibili.com/player.html?bvid=BV1kR4y1u77C&page=1&autoplay=0&danmaku=0&high_quality=1', 'rating': 8.6, 'actors': '张鲁一, 于和伟, 王子文, 林永健', 'release_date': '2023-01-15', 'intro': '地球文明首次接触外星文明三体世界，人类面临前所未有的生存危机。刘慈欣科幻巨著改编。'},
                {'title': '漫长的季节', 'category_id': cat_map['电视剧'], 'poster_url': '/uploads/posters/poster_10.png', 'trailer_url': '//player.bilibili.com/player.html?bvid=BV1oP411L7Gh&page=1&autoplay=0&danmaku=0&high_quality=1', 'rating': 9.3, 'actors': '范伟, 秦昊, 陈明昊, 李庚希', 'release_date': '2023-04-22', 'intro': '东北小城碎尸悬案跨越18年，三个老友在命运的漩涡中寻找真相。范伟、秦昊主演年度神剧。'},
                {'title': '人世间', 'category_id': cat_map['电视剧'], 'poster_url': '/uploads/posters/poster_11.png', 'trailer_url': '//player.bilibili.com/player.html?bvid=BV1iY411z7Qp&page=1&autoplay=0&danmaku=0&high_quality=1', 'rating': 8.6, 'actors': '雷佳音, 宋佳, 辛柏青, 殷桃', 'release_date': '2022-01-28', 'intro': '北方某城市周家三代人的命运沉浮，50年中国社会变迁的缩影。雷佳音、宋佳主演茅盾文学奖改编剧。'},
                {'title': '梦华录', 'category_id': cat_map['电视剧'], 'poster_url': '/uploads/posters/poster_12.png', 'trailer_url': '//player.bilibili.com/player.html?bvid=BV1wT411N7tF&page=1&autoplay=0&danmaku=0&high_quality=1', 'rating': 7.9, 'actors': '刘亦菲, 陈晓, 柳岩, 林允', 'release_date': '2022-06-02', 'intro': '赵盼儿等三位女子从钱塘来到京城，凭借茶坊闯出一片天地。刘亦菲、陈晓主演古装励志剧。'},
                {'title': '开端', 'category_id': cat_map['电视剧'], 'poster_url': '/uploads/posters/poster_13.png', 'trailer_url': '//player.bilibili.com/player.html?bvid=BV1r34y1s78A&page=1&autoplay=0&danmaku=0&high_quality=1', 'rating': 8.2, 'actors': '赵今麦, 白敬亭, 刘奕君', 'release_date': '2022-01-11', 'intro': '公交车爆炸案陷入时间循环，男女主角一次次尝试拯救全车乘客。国产无限流题材开山之作。'},
                {'title': '繁花', 'category_id': cat_map['电视剧'], 'poster_url': '/uploads/posters/poster_14.png', 'trailer_url': '//player.bilibili.com/player.html?bvid=BV1p142177cJ&page=1&autoplay=0&danmaku=0&high_quality=1', 'rating': 8.5, 'actors': '胡歌, 唐嫣, 马伊琍, 辛芷蕾', 'release_date': '2023-12-27', 'intro': '90年代上海滩，阿宝从普通青年蜕变为商界传奇宝总。王家卫导演首部电视剧，胡歌主演。'},
                {'title': '繁城之下', 'category_id': cat_map['电视剧'], 'poster_url': '/uploads/posters/poster_15.png', 'trailer_url': '//player.bilibili.com/player.html?bvid=BV1j84y1s79B&page=1&autoplay=0&danmaku=0&high_quality=1', 'rating': 8.6, 'actors': '白宇帆, 宁理, 向涵之, 刘怡潼', 'release_date': '2023-09-27', 'intro': '万历三十七年江南蠹县连环命案，小捕快追查真相揭开官场黑幕。高分古装悬疑剧。'},
                {'title': '庆余年2', 'category_id': cat_map['电视剧'], 'poster_url': '/uploads/posters/poster_16.png', 'trailer_url': '//player.bilibili.com/player.html?bvid=BV1dD421L7qf&page=1&autoplay=0&danmaku=0&high_quality=1', 'rating': 8.8, 'actors': '张若昀, 李沁, 陈道明, 吴刚', 'release_date': '2024-05-16', 'intro': '范闲身世之谜揭开，京都风云再起，权谋斗争升级。张若昀主演现象级古装剧续作。'},
                {'title': '我的阿勒泰', 'category_id': cat_map['电视剧'], 'poster_url': '/uploads/posters/poster_17.png', 'trailer_url': '//player.bilibili.com/player.html?bvid=BV1Kw4m1m7Eh&page=1&autoplay=0&danmaku=0&high_quality=1', 'rating': 8.8, 'actors': '于适, 周依然, 马伊琍', 'release_date': '2024-05-07', 'intro': '汉族少女李文秀随母亲回到新疆阿勒泰牧区，在广袤草原上感受自然之美与人文之暖。于适、周依然主演治愈系佳作。'},
                {'title': '玫瑰的故事', 'category_id': cat_map['电视剧'], 'poster_url': '/uploads/posters/poster_18.png', 'trailer_url': '//player.bilibili.com/player.html?bvid=BV1Zv421n7XU&page=1&autoplay=0&danmaku=0&high_quality=1', 'rating': 7.5, 'actors': '刘亦菲, 彭冠午, 林更新, 霍建华', 'release_date': '2024-06-08', 'intro': '黄亦玫经历四段感情，在不同的人生阶段追寻自我价值。刘亦菲主演都市情感大女主剧。'},
                {'title': '边水往事', 'category_id': cat_map['电视剧'], 'poster_url': '/uploads/posters/poster_19.png', 'trailer_url': '//player.bilibili.com/player.html?bvid=BV1XH4y1E7gB&page=1&autoplay=0&danmaku=0&high_quality=1', 'rating': 8.4, 'actors': '郭麒麟, 吴镇宇, 蒋奇明', 'release_date': '2024-08-16', 'intro': '沈星意外卷入三边坡的混乱局势，在生死边缘挣扎求生。郭麒麟、吴镇宇主演异域冒险悬疑剧。'},
                {'title': '唐朝诡事录之西行', 'category_id': cat_map['电视剧'], 'poster_url': '/uploads/posters/poster_20.png', 'trailer_url': '//player.bilibili.com/player.html?bvid=BV1c94y1z7Qp&page=1&autoplay=0&danmaku=0&high_quality=1', 'rating': 8.4, 'actors': '杨旭文, 杨志刚, 郜思雯', 'release_date': '2024-07-18', 'intro': '苏无名与卢凌风踏上西行之路，破解大唐边疆诡异奇案。杨旭文、杨志刚主演探案剧续作。'},
                {'title': '歌手2024', 'category_id': cat_map['综艺'], 'poster_url': '/uploads/posters/poster_21.png', 'trailer_url': '//player.bilibili.com/player.html?bvid=BV1xx421c7V8&page=1&autoplay=0&danmaku=0&high_quality=1', 'rating': 7.8, 'actors': '那英, 汪苏泷, 香缇莫, 凡希亚', 'release_date': '2024-05-10', 'intro': '湖南卫视王牌音乐竞技节目，国内外顶级歌手同台竞演，那英、汪苏泷、香缇莫等实力唱将带来精彩对决。'},
                {'title': '奔跑吧', 'category_id': cat_map['综艺'], 'poster_url': '/uploads/posters/poster_22.png', 'trailer_url': '//player.bilibili.com/player.html?bvid=BV1sW421R7hR&page=1&autoplay=0&danmaku=0&high_quality=1', 'rating': 7.5, 'actors': '李晨, Angelababy, 郑恺, 沙溢', 'release_date': '2024-04-19', 'intro': '李晨、Angelababy、郑恺、沙溢等固定成员，每期进行各种趣味游戏和挑战。国民级户外竞技综艺，欢笑不断。'},
                {'title': '乘风2024', 'category_id': cat_map['综艺'], 'poster_url': '/uploads/posters/poster_23.png', 'trailer_url': '//player.bilibili.com/player.html?bvid=BV1wW42187Qh&page=1&autoplay=0&danmaku=0&high_quality=1', 'rating': 7.6, 'actors': '陈嘉桦Ella, 戚薇, 柳岩, 尚雯婕', 'release_date': '2024-05-18', 'intro': '30+位不同年龄段的女性艺人通过舞台竞演展现女性力量，陈嘉桦Ella、戚薇、柳岩等姐姐们燃炸舞台。'},
                {'title': '王牌对王牌', 'category_id': cat_map['综艺'], 'poster_url': '/uploads/posters/poster_24.png', 'trailer_url': '//player.bilibili.com/player.html?bvid=BV177411e7MJ&page=1&autoplay=0&danmaku=0&high_quality=1', 'rating': 8.2, 'actors': '沈腾, 贾玲, 华晨宇, 关晓彤', 'release_date': '2024-01-26', 'intro': '沈腾、贾玲、华晨宇、关晓彤四位固定嘉宾，每期邀请不同主题的嘉宾团进行各种趣味竞技。'},
                {'title': '哪吒之魔童降世', 'category_id': cat_map['动漫'], 'poster_url': '/uploads/posters/poster_25.png', 'trailer_url': '//player.bilibili.com/player.html?bvid=BV1ot411c7LV&page=1&autoplay=0&danmaku=0&high_quality=1', 'rating': 9.0, 'actors': '吕艳婷, 囧森瑟夫, 瀚墨', 'release_date': '2019-07-26', 'intro': '天地灵气孕育混元珠，本该是灵珠转世的哪吒却成了魔丸降生。"我命由我不由天"——国漫里程碑，票房破50亿。'},
                {'title': '进击的巨人', 'category_id': cat_map['动漫'], 'poster_url': '/uploads/posters/poster_26.png', 'trailer_url': '//player.bilibili.com/player.html?bvid=BV1Va4y1v7yf&page=1&autoplay=0&danmaku=0&high_quality=1', 'rating': 9.6, 'actors': '梶裕贵, 石川由依, 井上麻里奈', 'release_date': '2013-04-07', 'intro': '人类被迫居住在高墙之内抵御巨人侵食，少年艾伦发誓消灭所有巨人。被誉为神作的史诗级动漫。'},
                {'title': '鬼灭之刃', 'category_id': cat_map['动漫'], 'poster_url': '/uploads/posters/poster_27.png', 'trailer_url': '//player.bilibili.com/player.html?epid=430726&autoplay=0&danmaku=0&high_quality=1', 'rating': 8.9, 'actors': '花江夏树, 鬼头明里, 下野纮', 'release_date': '2019-04-06', 'intro': '炭治郎家人惨遭鬼灭，妹妹变成鬼，他加入鬼杀队踏上了斩鬼之路。"无限列车篇"打破日本票房纪录。'},
                {'title': '灌篮高手（剧场版）', 'category_id': cat_map['动漫'], 'poster_url': '/uploads/posters/poster_28.png', 'trailer_url': '//player.bilibili.com/player.html?bvid=BV1pN4y1u7Ao&page=1&autoplay=0&danmaku=0&high_quality=1', 'rating': 9.0, 'actors': '仲村宗悟, 木村昴, 武田航平', 'release_date': '2023-04-25', 'intro': '以流川枫、樱木花道为主角的青春热血篮球故事，井上雄彦亲自执导，令一代人再度燃烧。'},
                {'title': '火影忍者', 'category_id': cat_map['动漫'], 'poster_url': '/uploads/posters/poster_29.png', 'trailer_url': '//player.bilibili.com/player.html?bvid=BV1pFkCBhEEN&page=1&autoplay=0&danmaku=0&high_quality=1', 'rating': 9.0, 'actors': '竹内顺子, 中村千绘, 石田彰', 'release_date': '2002-10-03', 'intro': '体内封印九尾妖狐的少年鸣人，从被嫌弃的孤儿成长为守护忍界的英雄。影响一代动漫迷的经典之作。'},
                {'title': '名侦探柯南', 'category_id': cat_map['动漫'], 'poster_url': '/uploads/posters/poster_30.png', 'trailer_url': '//player.bilibili.com/player.html?bvid=BV1Cx411Z7Ys&page=1&autoplay=0&danmaku=0&high_quality=1', 'rating': 9.1, 'actors': '山口胜平, 山崎和佳奈, 堀内贤雄', 'release_date': '1996-01-08', 'intro': '高中生侦探工藤新一身体缩小成小学生柯南，隐藏身份继续追查组织。日本国民级推理动漫。'},
            ]
            for data in movies_data:
                movie = Movie(
                    title=data['title'],
                    category_id=data['category_id'],
                    poster_url=data['poster_url'],
                    trailer_url=data.get('trailer_url', ''),
                    rating=data.get('rating', 0),
                    intro=data.get('intro', ''),
                    actors=data.get('actors', ''),
                    likes=0,
                )
                # 处理日期字符串转换为 date 对象
                if data.get('release_date'):
                    from datetime import datetime as dt
                    try:
                        movie.release_date = dt.strptime(data['release_date'], '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        pass
                db.session.add(movie)

            print(f'[Seed] 已添加 {len(movies_data)} 部影视数据')

        db.session.commit()

    except IntegrityError:
        db.session.rollback()
    except Exception as e:
        db.session.rollback()
        raise
