from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db
from app.utils.time import beijing_now


class Admin(db.Model):
    """管理员表"""
    __tablename__ = 'admin'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        """设置密码哈希"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Admin {self.username}>'


class User(UserMixin, db.Model):
    """注册用户表 — 仅 QQ 邮箱注册"""
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(128), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    nickname = db.Column(db.String(64), nullable=False)
    avatar = db.Column(db.String(256), nullable=True)       # 头像文件名（旧，保留兼容）
    avatar_data = db.Column(db.Text, nullable=True)           # 头像 Base64 数据（新，CloudBase 兼容）
    avatar_mime = db.Column(db.String(64), nullable=True)     # 头像 MIME 类型
    created_at = db.Column(db.DateTime, default=beijing_now)

    # 关系：一个用户多条影评
    comments = db.relationship('Comment', back_populates='user', lazy='dynamic',
                               cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def avatar_url(self):
        """返回头像访问 URL — 优先使用 Base64 数据（CloudBase 兼容）"""
        if self.avatar_data and self.avatar_mime:
            return f'data:{self.avatar_mime};base64,{self.avatar_data}'
        if self.avatar:
            return f'/uploads/avatars/{self.avatar}'
        return None

    def __repr__(self):
        return f'<User {self.nickname}>'


class VerificationCode(db.Model):
    """验证码表 — 存储手机/邮箱验证码，5分钟有效期"""
    __tablename__ = 'verification_code'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    target = db.Column(db.String(128), nullable=False, index=True)  # 手机号或邮箱
    code = db.Column(db.String(10), nullable=False)
    purpose = db.Column(db.String(32), nullable=False)   # 'register' 或 'login'
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=beijing_now)

    @property
    def is_expired(self):
        return beijing_now() > self.expires_at

    @classmethod
    def generate_code(cls, target, purpose):
        """生成6位验证码，同一 target+purpose 先作废旧码，有效期5分钟"""
        # 作废该 target 下同一用途的未使用旧码
        cls.query.filter(
            cls.target == target,
            cls.purpose == purpose,
            cls.used == False
        ).update({'used': True})
        import random
        code = str(random.randint(100000, 999999))
        vc = cls(
            target=target,
            code=code,
            purpose=purpose,
            expires_at=beijing_now() + timedelta(minutes=5)
        )
        db.session.add(vc)
        db.session.commit()
        return code

    @classmethod
    def verify_code(cls, target, code, purpose):
        """验证验证码是否正确且未过期"""
        vc = cls.query.filter(
            cls.target == target,
            cls.code == code,
            cls.purpose == purpose,
            cls.used == False
        ).order_by(cls.created_at.desc()).first()
        if not vc:
            return False, '验证码错误或已使用'
        if vc.is_expired:
            return False, '验证码已过期，请重新获取'
        vc.used = True
        db.session.commit()
        return True, '验证成功'

    def __repr__(self):
        return f'<VerificationCode {self.target}:{self.code}>'


class Category(db.Model):
    """影视分类表 — 一对多：一个分类对应多部影视"""
    __tablename__ = 'category'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(32), unique=True, nullable=False)

    # 一对多关系
    movies = db.relationship('Movie', back_populates='category', lazy='dynamic',
                             cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Category {self.name}>'


class Movie(db.Model):
    """影视表 — 关联分类外键"""
    __tablename__ = 'movie'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(128), nullable=False, index=True)
    intro = db.Column(db.Text, nullable=True)
    actors = db.Column(db.String(256), nullable=True)
    release_date = db.Column(db.Date, nullable=True)
    rating = db.Column(db.Float, default=0.0)
    poster_url = db.Column(db.String(512), nullable=True)
    trailer_url = db.Column(db.String(512), nullable=True)   # 预告片嵌入 URL
    created_at = db.Column(db.DateTime, default=beijing_now)
    likes = db.Column(db.Integer, default=0)

    # 外键关联分类
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)

    # 关系
    category = db.relationship('Category', back_populates='movies')
    # 一对多：一部影视对应多条影评
    comments = db.relationship('Comment', back_populates='movie', lazy='dynamic',
                               cascade='all, delete-orphan',
                               order_by='Comment.created_at.desc()')

    def __repr__(self):
        return f'<Movie {self.title}>'


class Friendship(db.Model):
    """好友关系表 — 记录用户之间的好友请求与状态"""
    __tablename__ = 'friendship'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    status = db.Column(db.String(16), nullable=False, default='pending')  # pending / accepted / rejected
    created_at = db.Column(db.DateTime, default=beijing_now)
    updated_at = db.Column(db.DateTime, default=beijing_now, onupdate=beijing_now)

    # 关系
    requester = db.relationship('User', foreign_keys=[requester_id],
                                backref=db.backref('sent_requests', lazy='dynamic',
                                                   cascade='all, delete-orphan'))
    receiver = db.relationship('User', foreign_keys=[receiver_id],
                               backref=db.backref('received_requests', lazy='dynamic',
                                                  cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<Friendship {self.requester_id}->{self.receiver} ({self.status})>'


class Message(db.Model):
    """好友聊天消息表"""
    __tablename__ = 'message'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(32), default='text')  # 'text' 或 'share_movie'
    related_movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=beijing_now, index=True)
    is_read = db.Column(db.Boolean, default=False)  # 是否已读（避免 SQLite 保留字 read）

    # 关系
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')
    related_movie = db.relationship('Movie', backref='shared_in_messages')

    def __repr__(self):
        return f'<Message {self.id}: {self.content[:20]}>'


class Comment(db.Model):
    """影评表 — 关联影视外键（一对多），关联用户外键（可选）"""
    __tablename__ = 'comment'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(64), default='匿名用户')
    created_at = db.Column(db.DateTime, default=beijing_now, index=True)

    # 外键关联影视
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    # 外键关联用户（可选，允许匿名影评）
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # 关系
    movie = db.relationship('Movie', back_populates='comments')
    user = db.relationship('User', back_populates='comments')

    def __repr__(self):
        return f'<Comment {self.id} on Movie {self.movie_id}>'
