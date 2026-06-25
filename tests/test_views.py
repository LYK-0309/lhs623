"""视图层单元测试"""
import unittest
from datetime import date
from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models import Admin, Category, Movie, Comment


class TestMainViews(unittest.TestCase):
    """前台视图测试"""

    def setUp(self):
        self.app = create_app(TestingConfig)
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

        # 准备测试数据（_seed_data 已创建默认分类，直接使用）
        self.cat = Category.query.filter_by(name='电影').first()

        self.movie = Movie(
            title='测试电影A',
            intro='测试简介A',
            actors='主演A',
            release_date=date(2024, 1, 1),
            rating=8.0,
            category_id=self.cat.id
        )
        db.session.add(self.movie)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        self.app_context.pop()

    def test_index_page(self):
        """测试首页可访问"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('测试电影A', response.get_data(as_text=True))

    def test_index_pagination(self):
        """测试首页分页"""
        for i in range(10):
            m = Movie(title=f'分页测试{i}', category_id=self.cat.id)
            db.session.add(m)
        db.session.commit()

        response = self.client.get('/?page=1')
        self.assertEqual(response.status_code, 200)

    def test_category_filter(self):
        """测试分类筛选"""
        cat2 = Category.query.filter_by(name='电视剧').first()

        movie2 = Movie(title='电视剧A', category_id=cat2.id)
        db.session.add(movie2)
        db.session.commit()

        response = self.client.get(f'/?category={self.cat.id}')
        data = response.get_data(as_text=True)
        self.assertIn('测试电影A', data)
        self.assertNotIn('电视剧A', data)

    def test_keyword_search(self):
        """测试关键词搜索"""
        response = self.client.get('/?keyword=测试电影')
        data = response.get_data(as_text=True)
        self.assertIn('测试电影A', data)

    def test_search_no_results(self):
        """测试搜索无结果"""
        response = self.client.get('/?keyword=不存在的电影xyz')
        self.assertEqual(response.status_code, 200)

    def test_detail_page(self):
        """测试详情页"""
        response = self.client.get(f'/movie/{self.movie.id}')
        self.assertEqual(response.status_code, 200)
        data = response.get_data(as_text=True)
        self.assertIn('测试电影A', data)
        self.assertIn('测试简介A', data)
        self.assertIn('主演A', data)

    def test_detail_404(self):
        """测试不存在的详情页"""
        response = self.client.get('/movie/99999')
        self.assertEqual(response.status_code, 404)

    def _create_and_inject_user(self):
        """辅助：创建普通用户并直接注入 Flask-Login session（绕过邮件验证限制）"""
        from app.models import User
        from flask_login import login_user
        user = User(email='test_viewer@qq.com', nickname='影评测试者')
        user.set_password('Test1234')
        db.session.add(user)
        db.session.commit()
        # 使用 test_request_context 注入登录状态
        with self.app.test_request_context():
            login_user(user)
        # 通过 session_transaction 手动写入 user_id
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
        return user

    def test_post_comment(self):
        """测试登录后发表影评"""
        self._create_and_inject_user()
        response = self.client.post(
            f'/movie/{self.movie.id}/comment',
            data={'content': '这条影评很不错', 'author': '测试用户', 'movie_id': str(self.movie.id)},
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.query.count(), 1)
        self.assertEqual(Comment.query.first().content, '这条影评很不错')

    def test_post_comment_ajax(self):
        """测试登录后AJAX发表影评"""
        self._create_and_inject_user()
        response = self.client.post(
            f'/movie/{self.movie.id}/comment',
            data={'content': 'AJAX影评', 'author': 'AJAX用户', 'movie_id': str(self.movie.id)},
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertTrue(json_data['success'])

    def test_post_comment_requires_login(self):
        """测试未登录发表影评被重定向"""
        response = self.client.post(
            f'/movie/{self.movie.id}/comment',
            data={'content': '未登录影评', 'movie_id': str(self.movie.id)},
        )
        # 未登录应返回302重定向到登录页
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Comment.query.count(), 0)

    def test_post_empty_comment(self):
        """测试发表空影评（已登录状态下）"""
        self._create_and_inject_user()
        response = self.client.post(
            f'/movie/{self.movie.id}/comment',
            data={'content': '', 'movie_id': str(self.movie.id)},
            follow_redirects=True
        )
        self.assertEqual(Comment.query.count(), 0)

    def test_like_movie(self):
        """测试登录后点赞"""
        self._create_and_inject_user()
        response = self.client.post(f'/movie/{self.movie.id}/like')
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertTrue(json_data['success'])
        self.assertEqual(json_data['likes'], 1)

    def test_like_movie_requires_login(self):
        """测试未登录点赞被重定向"""
        response = self.client.post(f'/movie/{self.movie.id}/like')
        # 未登录应返回302或401
        self.assertIn(response.status_code, [302, 401])

    def test_search_page(self):
        """测试搜索页"""
        response = self.client.get('/search?keyword=测试电影')
        self.assertEqual(response.status_code, 200)


class TestAdminViews(unittest.TestCase):
    """管理后台视图测试"""

    def setUp(self):
        self.app = create_app(TestingConfig)
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

        # _seed_data 已创建默认管理员和分类，直接使用
        self.admin = Admin.query.filter_by(username='admin').first()
        self.cat = Category.query.filter_by(name='电影').first()

    def tearDown(self):
        db.session.remove()
        self.app_context.pop()

    def _login(self):
        """辅助方法：登录"""
        return self.client.post('/admin/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)

    def _logout(self):
        """辅助方法：注销"""
        return self.client.get('/admin/logout', follow_redirects=True)

    # ---------- 认证测试 ----------
    def test_login_page(self):
        """测试登录页可访问"""
        response = self.client.get('/admin/login')
        self.assertEqual(response.status_code, 200)

    def test_login_success(self):
        """测试成功登录"""
        response = self._login()
        self.assertEqual(response.status_code, 200)
        self.assertIn('欢迎回来', response.get_data(as_text=True))

    def test_login_wrong_password(self):
        """测试错误密码"""
        response = self.client.post('/admin/login', data={
            'username': 'admin',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertIn('密码错误', response.get_data(as_text=True))

    def test_login_nonexistent_user(self):
        """测试不存在的用户"""
        response = self.client.post('/admin/login', data={
            'username': 'nobody',
            'password': 'pass123456'
        }, follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('用户名不存在', data)

    def test_logout(self):
        """测试注销"""
        self._login()
        response = self._logout()
        self.assertIn('已安全退出', response.get_data(as_text=True))

    # ---------- 权限拦截测试 ----------
    def test_dashboard_requires_login(self):
        """测试仪表盘需要登录"""
        response = self.client.get('/admin/dashboard', follow_redirects=True)
        self.assertIn('请先登录', response.get_data(as_text=True))

    def test_movie_list_requires_login(self):
        """测试影视管理需要登录"""
        response = self.client.get('/admin/movies', follow_redirects=True)
        self.assertIn('请先登录', response.get_data(as_text=True))

    # ---------- 仪表盘测试 ----------
    def test_dashboard_authenticated(self):
        """测试登录后访问仪表盘"""
        self._login()
        response = self.client.get('/admin/dashboard')
        self.assertEqual(response.status_code, 200)

    # ---------- 影视CRUD测试 ----------
    def test_movie_list_authenticated(self):
        """测试登录后影视列表"""
        self._login()
        response = self.client.get('/admin/movies')
        self.assertEqual(response.status_code, 200)

    def test_movie_new_form(self):
        """测试新增影视表单页"""
        self._login()
        response = self.client.get('/admin/movies/new')
        self.assertEqual(response.status_code, 200)

    def test_movie_create(self):
        """测试创建影视"""
        self._login()
        response = self.client.post('/admin/movies/new', data={
            'title': '新电影',
            'intro': '新电影简介',
            'actors': '演员A',
            'rating': 7.5,
            'category_id': self.cat.id,
            'release_date': '2025-01-01'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Movie.query.filter_by(title='新电影').count(), 1)

    def test_movie_edit_form(self):
        """测试编辑影视表单页"""
        self._login()
        movie = Movie(title='待编辑', category_id=self.cat.id)
        db.session.add(movie)
        db.session.commit()

        response = self.client.get(f'/admin/movies/{movie.id}/edit')
        self.assertEqual(response.status_code, 200)

    def test_movie_update(self):
        """测试更新影视"""
        self._login()
        movie = Movie(title='原始标题', category_id=self.cat.id)
        db.session.add(movie)
        db.session.commit()

        response = self.client.post(f'/admin/movies/{movie.id}/edit', data={
            'title': '更新后的标题',
            'actors': '新演员',
            'rating': 9.0,
            'category_id': self.cat.id,
            'release_date': '2025-06-01'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        updated = Movie.query.get(movie.id)
        self.assertEqual(updated.title, '更新后的标题')
        self.assertEqual(updated.actors, '新演员')

    def test_movie_delete(self):
        """测试删除影视"""
        self._login()
        movie = Movie(title='待删除', category_id=self.cat.id)
        db.session.add(movie)
        db.session.commit()

        response = self.client.post(f'/admin/movies/{movie.id}/delete', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(Movie.query.get(movie.id))

    # ---------- 分类管理测试 ----------
    def test_category_list_authenticated(self):
        """测试登录后分类列表"""
        self._login()
        response = self.client.get('/admin/categories')
        self.assertEqual(response.status_code, 200)

    def test_category_create(self):
        """测试新增分类"""
        self._login()
        response = self.client.post('/admin/categories/new', data={
            'name': '纪录片'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(Category.query.filter_by(name='纪录片').first())

    def test_category_duplicate(self):
        """测试重复分类"""
        self._login()
        response = self.client.post('/admin/categories/new', data={
            'name': '电影'  # 已存在
        }, follow_redirects=True)
        self.assertIn('该分类已存在', response.get_data(as_text=True))

    def test_category_delete(self):
        """测试删除空分类"""
        self._login()
        cat = Category(name='空分类')
        db.session.add(cat)
        db.session.commit()

        response = self.client.post(f'/admin/categories/{cat.id}/delete', follow_redirects=True)
        self.assertIsNone(Category.query.get(cat.id))

    def test_category_delete_with_movies(self):
        """测试删除有影视的分类（应被阻止）"""
        self._login()
        cat = Category(name='有影视的分类')
        db.session.add(cat)
        db.session.commit()

        movie = Movie(title='测试', category_id=cat.id)
        db.session.add(movie)
        db.session.commit()

        response = self.client.post(f'/admin/categories/{cat.id}/delete', follow_redirects=True)
        self.assertIsNotNone(Category.query.get(cat.id))

    # ---------- 影评管理测试 ----------
    def test_comment_list_authenticated(self):
        """测试登录后影评列表"""
        self._login()
        response = self.client.get('/admin/comments')
        self.assertEqual(response.status_code, 200)

    def test_comment_delete(self):
        """测试删除影评"""
        self._login()
        movie = Movie(title='评论测试', category_id=self.cat.id)
        db.session.add(movie)
        db.session.commit()

        comment = Comment(content='违规内容', movie_id=movie.id)
        db.session.add(comment)
        db.session.commit()

        response = self.client.post(f'/admin/comments/{comment.id}/delete', follow_redirects=True)
        self.assertIsNone(Comment.query.get(comment.id))


class TestUserAuthViews(unittest.TestCase):
    """用户认证视图测试：验证码登录、忘记密码"""

    def setUp(self):
        self.app = create_app(TestingConfig)
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

        # 注册一个测试用户
        from app.models import User, VerificationCode
        from app.utils.time import beijing_now
        from datetime import timedelta
        self.User = User
        self.VerificationCode = VerificationCode
        self.timedelta = timedelta

        user = User(email='1234567890@qq.com', nickname='测试用户')
        user.set_password('Test1234')
        db.session.add(user)
        db.session.commit()
        self.user = user

    def tearDown(self):
        db.session.remove()
        self.app_context.pop()

    def _insert_code(self, purpose, code='654321'):
        """直接插入一条未过期的验证码"""
        from app.utils.time import beijing_now
        from datetime import timedelta
        vc = self.VerificationCode(
            target=self.user.email,
            code=code,
            purpose=purpose,
            expires_at=beijing_now() + timedelta(minutes=5)
        )
        db.session.add(vc)
        db.session.commit()
        return code

    # ── 登录页面 ──────────────────────────────

    def test_login_page_loads(self):
        """登录页面可正常访问"""
        resp = self.client.get('/user/login')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('密码登录', resp.get_data(as_text=True))
        self.assertIn('验证码登录', resp.get_data(as_text=True))

    def test_login_page_no_default_hint(self):
        """管理员登录页不再显示默认账号密码"""
        resp = self.client.get('/admin/login')
        body = resp.get_data(as_text=True)
        self.assertNotIn('admin123', body)

    # ── 密码登录 ──────────────────────────────

    def test_password_login_success(self):
        """正确密码可登录"""
        resp = self.client.post('/user/login', data={
            'email': '1234567890@qq.com',
            'password': 'Test1234',
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('欢迎回来', resp.get_data(as_text=True))

    def test_password_login_wrong_password(self):
        """错误密码登录被拒绝"""
        resp = self.client.post('/user/login', data={
            'email': '1234567890@qq.com',
            'password': 'WrongPwd1',
        }, follow_redirects=True)
        body = resp.get_data(as_text=True)
        self.assertIn('密码错误', body)

    # ── 验证码登录 ─────────────────────────────

    def test_code_login_success(self):
        """正确验证码可登录"""
        code = self._insert_code('login')
        resp = self.client.post('/user/code-login', data={
            'email': '1234567890@qq.com',
            'verification_code': code,
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('欢迎回来', resp.get_data(as_text=True))

    def test_code_login_wrong_code(self):
        """错误验证码被拒绝"""
        self._insert_code('login', code='111111')
        resp = self.client.post('/user/code-login', data={
            'email': '1234567890@qq.com',
            'verification_code': '999999',
        }, follow_redirects=True)
        body = resp.get_data(as_text=True)
        self.assertIn('验证码', body)

    def test_code_login_unregistered_email(self):
        """未注册邮箱验证码登录被拒绝"""
        resp = self.client.post('/user/code-login', data={
            'email': '9999999999@qq.com',
            'verification_code': '123456',
        }, follow_redirects=True)
        body = resp.get_data(as_text=True)
        self.assertIn('未注册', body)

    # ── 忘记密码 ──────────────────────────────

    def test_forgot_password_page_loads(self):
        """忘记密码页面可访问"""
        resp = self.client.get('/user/forgot-password')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('找回密码', resp.get_data(as_text=True))

    def test_forgot_password_success(self):
        """正确验证码可重置密码"""
        code = self._insert_code('reset')
        resp = self.client.post('/user/forgot-password', data={
            'email': '1234567890@qq.com',
            'verification_code': code,
            'new_password': 'NewPass88',
            'confirm_password': 'NewPass88',
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('密码重置成功', resp.get_data(as_text=True))
        # 验证新密码生效
        db.session.refresh(self.user)
        self.assertTrue(self.user.check_password('NewPass88'))

    def test_forgot_password_wrong_code(self):
        """错误验证码重置密码被拒绝"""
        self._insert_code('reset', code='111111')
        resp = self.client.post('/user/forgot-password', data={
            'email': '1234567890@qq.com',
            'verification_code': '999999',
            'new_password': 'NewPass88',
            'confirm_password': 'NewPass88',
        }, follow_redirects=True)
        body = resp.get_data(as_text=True)
        self.assertIn('验证码', body)

    def test_forgot_password_unregistered_email(self):
        """未注册邮箱重置密码被拒绝"""
        resp = self.client.post('/user/forgot-password', data={
            'email': '9999999999@qq.com',
            'verification_code': '123456',
            'new_password': 'NewPass88',
            'confirm_password': 'NewPass88',
        }, follow_redirects=True)
        body = resp.get_data(as_text=True)
        self.assertIn('未注册', body)

    def test_forgot_password_mismatch(self):
        """两次密码不一致被拒绝"""
        code = self._insert_code('reset')
        resp = self.client.post('/user/forgot-password', data={
            'email': '1234567890@qq.com',
            'verification_code': code,
            'new_password': 'NewPass88',
            'confirm_password': 'DiffPass9',
        }, follow_redirects=True)
        body = resp.get_data(as_text=True)
        self.assertIn('两次密码不一致', body)

    # ── request_code 接口 ────────────────────

    def test_request_code_reset_unregistered(self):
        """reset 用途下未注册邮箱返回 400"""
        resp = self.client.post('/user/request-code', data={
            'email': '9999999999@qq.com',
            'purpose': 'reset',
        })
        self.assertEqual(resp.status_code, 400)

    def test_request_code_invalid_purpose(self):
        """无效 purpose 返回 400"""
        resp = self.client.post('/user/request-code', data={
            'email': '1234567890@qq.com',
            'purpose': 'hack',
        })
        self.assertEqual(resp.status_code, 400)


if __name__ == '__main__':
    unittest.main()
