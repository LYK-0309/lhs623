"""模型层单元测试"""
import unittest
from datetime import date, datetime
from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models import Admin, Category, Movie, Comment


class TestAdminModel(unittest.TestCase):
    """管理员模型测试"""

    def setUp(self):
        self.app = create_app(TestingConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        db.session.remove()
        self.app_context.pop()

    def test_create_admin(self):
        """测试创建管理员"""
        admin = Admin(username='testadmin')
        admin.set_password('password123')
        db.session.add(admin)
        db.session.commit()

        found = Admin.query.filter_by(username='testadmin').first()
        self.assertIsNotNone(found)
        self.assertEqual(found.username, 'testadmin')

    def test_password_hashing(self):
        """测试密码哈希存储与验证"""
        admin = Admin(username='admin1')
        admin.set_password('secret123')
        self.assertNotEqual(admin.password_hash, 'secret123')
        self.assertTrue(admin.check_password('secret123'))
        self.assertFalse(admin.check_password('wrongpassword'))

    def test_unique_username(self):
        """测试用户名唯一约束"""
        admin1 = Admin(username='uniqueuser')
        admin1.set_password('pass1')
        db.session.add(admin1)
        db.session.commit()

        admin2 = Admin(username='uniqueuser')
        admin2.set_password('pass2')
        db.session.add(admin2)
        with self.assertRaises(Exception):
            db.session.commit()
        db.session.rollback()

    def test_repr(self):
        """测试字符串表示"""
        admin = Admin(username='reprtest')
        self.assertIn('reprtest', repr(admin))


class TestCategoryModel(unittest.TestCase):
    """分类模型测试"""

    def setUp(self):
        self.app = create_app(TestingConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        db.session.remove()
        self.app_context.pop()

    def test_create_category(self):
        """测试创建分类"""
        cat = Category(name='科幻片')
        db.session.add(cat)
        db.session.commit()

        found = Category.query.filter_by(name='科幻片').first()
        self.assertIsNotNone(found)
        self.assertEqual(found.name, '科幻片')

    def test_unique_name(self):
        """测试分类名称唯一约束"""
        cat1 = Category(name='动作片')
        db.session.add(cat1)
        db.session.commit()

        cat2 = Category(name='动作片')
        db.session.add(cat2)
        with self.assertRaises(Exception):
            db.session.commit()
        db.session.rollback()

    def test_one_to_many_movies(self):
        """测试一对多关系：分类 → 多部影视"""
        cat = Category(name='剧情片')
        db.session.add(cat)
        db.session.commit()

        movie1 = Movie(title='电影A', category_id=cat.id)
        movie2 = Movie(title='电影B', category_id=cat.id)
        db.session.add_all([movie1, movie2])
        db.session.commit()

        self.assertEqual(cat.movies.count(), 2)
        self.assertEqual(cat.movies.first().title, '电影A')

    def test_cascade_delete(self):
        """测试级联删除：删除分类时关联影视也被删除"""
        movie_count_before = Movie.query.count()

        cat = Category(name='恐怖片')
        db.session.add(cat)
        db.session.commit()

        movie = Movie(title='恐怖片A', category_id=cat.id)
        db.session.add(movie)
        db.session.commit()
        self.assertEqual(Movie.query.count(), movie_count_before + 1)

        db.session.delete(cat)
        db.session.commit()

        # 被删分类下的影视应被级联删除，其余影视不受影响
        self.assertEqual(Movie.query.count(), movie_count_before)
        self.assertIsNone(Movie.query.filter_by(title='恐怖片A').first())

    def test_repr(self):
        """测试字符串表示"""
        cat = Category(name='测试')
        self.assertIn('测试', repr(cat))


class TestMovieModel(unittest.TestCase):
    """影视模型测试"""

    def setUp(self):
        self.app = create_app(TestingConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        # _seed_data 已创建默认分类，直接使用
        self.cat = Category.query.filter_by(name='电影').first()

    def tearDown(self):
        db.session.remove()
        self.app_context.pop()

    def test_create_movie(self):
        """测试创建影视条目"""
        movie = Movie(
            title='测试电影',
            intro='这是一部测试电影',
            actors='张三, 李四',
            release_date=date(2024, 6, 15),
            rating=8.5,
            category_id=self.cat.id
        )
        db.session.add(movie)
        db.session.commit()

        found = Movie.query.filter_by(title='测试电影').first()
        self.assertIsNotNone(found)
        self.assertEqual(found.intro, '这是一部测试电影')
        self.assertEqual(found.actors, '张三, 李四')
        self.assertEqual(found.rating, 8.5)
        self.assertEqual(found.category.name, '电影')
        self.assertEqual(found.likes, 0)

    def test_movie_relationship_category(self):
        """测试影视与分类的关系"""
        movie = Movie(title='关系测试', category_id=self.cat.id)
        db.session.add(movie)
        db.session.commit()

        self.assertEqual(movie.category.name, '电影')
        self.assertIn(movie, self.cat.movies.all())

    def test_one_to_many_comments(self):
        """测试一对多关系：影视 → 多条影评"""
        movie = Movie(title='影评测试电影', category_id=self.cat.id)
        db.session.add(movie)
        db.session.commit()

        c1 = Comment(content='影评1', movie_id=movie.id)
        c2 = Comment(content='影评2', movie_id=movie.id)
        c3 = Comment(content='影评3', movie_id=movie.id)
        db.session.add_all([c1, c2, c3])
        db.session.commit()

        self.assertEqual(movie.comments.count(), 3)

    def test_cascade_delete_comments(self):
        """测试级联删除：删除影视时关联影评也被删除"""
        movie = Movie(title='级联删除测试', category_id=self.cat.id)
        db.session.add(movie)
        db.session.commit()

        comment = Comment(content='测试影评', movie_id=movie.id)
        db.session.add(comment)
        db.session.commit()

        db.session.delete(movie)
        db.session.commit()

        self.assertEqual(Comment.query.count(), 0)

    def test_default_values(self):
        """测试默认值"""
        movie = Movie(title='默认值测试')
        db.session.add(movie)
        db.session.commit()

        self.assertEqual(movie.rating, 0.0)
        self.assertEqual(movie.likes, 0)
        self.assertIsNone(movie.category)

    def test_likes_increment(self):
        """测试点赞计数"""
        movie = Movie(title='点赞测试', category_id=self.cat.id)
        db.session.add(movie)
        db.session.commit()

        movie.likes = (movie.likes or 0) + 1
        db.session.commit()
        self.assertEqual(movie.likes, 1)

        movie.likes = (movie.likes or 0) + 1
        db.session.commit()
        self.assertEqual(movie.likes, 2)

    def test_repr(self):
        """测试字符串表示"""
        movie = Movie(title='repr测试')
        self.assertIn('repr测试', repr(movie))


class TestCommentModel(unittest.TestCase):
    """影评模型测试"""

    def setUp(self):
        self.app = create_app(TestingConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        # _seed_data 已创建默认分类，直接使用
        cat = Category.query.filter_by(name='电影').first()
        self.movie = Movie(title='影评测试', category_id=cat.id)
        db.session.add(self.movie)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        self.app_context.pop()

    def test_create_comment(self):
        """测试创建影评"""
        comment = Comment(
            content='这部电影非常好看！',
            author='影迷小王',
            movie_id=self.movie.id
        )
        db.session.add(comment)
        db.session.commit()

        found = Comment.query.first()
        self.assertEqual(found.content, '这部电影非常好看！')
        self.assertEqual(found.author, '影迷小王')
        self.assertEqual(found.movie.title, '影评测试')

    def test_default_author(self):
        """测试默认作者名"""
        comment = Comment(content='测试', movie_id=self.movie.id)
        db.session.add(comment)
        db.session.commit()

        self.assertEqual(comment.author, '匿名用户')

    def test_created_at_auto(self):
        """测试自动生成创建时间"""
        comment = Comment(content='时间测试', movie_id=self.movie.id)
        db.session.add(comment)
        db.session.commit()

        self.assertIsInstance(comment.created_at, datetime)

    def test_repr(self):
        """测试字符串表示"""
        comment = Comment(content='repr', movie_id=self.movie.id)
        self.assertIn('Comment', repr(comment))


if __name__ == '__main__':
    unittest.main()
