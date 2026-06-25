"""表单验证单元测试"""
import unittest
from werkzeug.datastructures import MultiDict
from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models import Admin
from app.forms import LoginForm, MovieForm, CommentForm, SearchForm, CategoryForm


class TestLoginForm(unittest.TestCase):
    """登录表单测试"""

    def setUp(self):
        self.app = create_app(TestingConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        # 创建测试管理员
        admin = Admin(username='testadmin')
        admin.set_password('password123')
        db.session.add(admin)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        self.app_context.pop()

    def _make_form(self, **data):
        with self.app.test_request_context():
            return LoginForm(formdata=MultiDict(data))

    def test_valid_login(self):
        """测试有效的登录数据"""
        form = self._make_form(username='testadmin', password='password123')
        self.assertTrue(form.validate())

    def test_empty_username(self):
        """测试空用户名"""
        form = self._make_form(username='', password='password123')
        self.assertFalse(form.validate())
        self.assertIn('username', form.errors)

    def test_empty_password(self):
        """测试空密码"""
        form = self._make_form(username='testadmin', password='')
        self.assertFalse(form.validate())
        self.assertIn('password', form.errors)

    def test_short_password(self):
        """测试过短密码"""
        form = self._make_form(username='testadmin', password='123')
        self.assertFalse(form.validate())
        self.assertIn('password', form.errors)

    def test_nonexistent_username(self):
        """测试不存在的用户名（自定义验证器）"""
        form = self._make_form(username='nonexistent', password='password123')
        self.assertFalse(form.validate())
        self.assertIn('username', form.errors)


class TestMovieForm(unittest.TestCase):
    """影视表单测试"""

    def setUp(self):
        self.app = create_app(TestingConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def _make_form(self, **data):
        with self.app.test_request_context():
            form = MovieForm(formdata=MultiDict(data))
            # 设置分类选项
            form.category_id.choices = [(0, '-- 请选择分类 --'), (1, '电影')]
            return form

    def test_valid_movie(self):
        """测试有效的影视数据"""
        form = self._make_form(
            title='测试电影',
            intro='简介内容',
            actors='张三, 李四',
            rating='8.5',
            category_id='1'
        )
        self.assertTrue(form.validate())

    def test_empty_title(self):
        """测试空影视名称"""
        form = self._make_form(title='')
        self.assertFalse(form.validate())
        self.assertIn('title', form.errors)

    def test_title_too_long(self):
        """测试影视名称超长"""
        form = self._make_form(title='A' * 200)
        self.assertFalse(form.validate())
        self.assertIn('title', form.errors)

    def test_rating_out_of_range(self):
        """测试评分超出范围"""
        form = self._make_form(title='测试', rating='11')
        self.assertFalse(form.validate())
        self.assertIn('rating', form.errors)

    def test_rating_negative(self):
        """测试评分为负数"""
        form = self._make_form(title='测试', rating='-1')
        self.assertFalse(form.validate())
        self.assertIn('rating', form.errors)

    def test_optional_fields(self):
        """测试可选字段"""
        form = self._make_form(title='最小数据')
        self.assertTrue(form.validate())

    def test_actors_too_long(self):
        """测试主演超长"""
        form = self._make_form(title='测试', actors='A' * 300)
        self.assertFalse(form.validate())
        self.assertIn('actors', form.errors)


class TestCommentForm(unittest.TestCase):
    """影评表单测试"""

    def setUp(self):
        self.app = create_app(TestingConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def _make_form(self, **data):
        with self.app.test_request_context():
            defaults = {'movie_id': '1'}
            defaults.update(data)
            return CommentForm(formdata=MultiDict(defaults))

    def test_valid_comment(self):
        """测试有效影评"""
        form = self._make_form(
            author='影迷',
            content='这部电影真的太好了！强烈推荐！'
        )
        self.assertTrue(form.validate())

    def test_empty_content(self):
        """测试空影评内容"""
        form = self._make_form(content='')
        self.assertFalse(form.validate())
        self.assertIn('content', form.errors)

    def test_content_too_long(self):
        """测试影评内容超长"""
        form = self._make_form(content='A' * 3000)
        self.assertFalse(form.validate())
        self.assertIn('content', form.errors)

    def test_default_author(self):
        """测试默认作者名（不传 author 时使用默认值）"""
        form = self._make_form(content='测试内容')
        self.assertTrue(form.validate())
        self.assertEqual(form.author.data, '匿名用户')

    def test_missing_movie_id(self):
        """测试缺少影视ID"""
        with self.app.test_request_context():
            form = CommentForm(formdata=MultiDict({'content': '测试'}))
            self.assertFalse(form.validate())


class TestSearchForm(unittest.TestCase):
    """搜索表单测试"""

    def setUp(self):
        self.app = create_app(TestingConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_valid_keyword(self):
        """测试有效搜索关键词"""
        with self.app.test_request_context():
            form = SearchForm(formdata=MultiDict({'keyword': '流浪地球'}))
            self.assertTrue(form.validate())

    def test_empty_keyword(self):
        """测试空关键词"""
        with self.app.test_request_context():
            form = SearchForm(formdata=MultiDict({'keyword': ''}))
            self.assertFalse(form.validate())


class TestCategoryForm(unittest.TestCase):
    """分类表单测试"""

    def setUp(self):
        self.app = create_app(TestingConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_valid_category(self):
        """测试有效分类"""
        with self.app.test_request_context():
            form = CategoryForm(formdata=MultiDict({'name': '纪录片'}))
            self.assertTrue(form.validate())

    def test_empty_name(self):
        """测试空分类名"""
        with self.app.test_request_context():
            form = CategoryForm(formdata=MultiDict({'name': ''}))
            self.assertFalse(form.validate())

    def test_name_too_long(self):
        """测试分类名超长"""
        with self.app.test_request_context():
            form = CategoryForm(formdata=MultiDict({'name': 'A' * 50}))
            self.assertFalse(form.validate())


if __name__ == '__main__':
    unittest.main()
