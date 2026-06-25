from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, FloatField, DateField, \
    SelectField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, ValidationError, EqualTo
from app.models import Admin


class LoginForm(FlaskForm):
    """管理员登录表单"""
    username = StringField('用户名', validators=[
        DataRequired(message='请输入用户名'),
        Length(min=2, max=64, message='用户名长度2-64位')
    ])
    password = PasswordField('密码', validators=[
        DataRequired(message='请输入密码'),
        Length(min=6, max=128, message='密码长度至少6位')
    ])
    submit = SubmitField('登录')

    def validate_username(self, field):
        """验证用户名是否存在"""
        admin = Admin.query.filter_by(username=field.data).first()
        if admin is None:
            raise ValidationError('用户名不存在')


class MovieForm(FlaskForm):
    """影视信息表单（新增/编辑共用）"""
    title = StringField('影视名称', validators=[
        DataRequired(message='请输入影视名称'),
        Length(max=128, message='名称不能超过128个字符')
    ])
    intro = TextAreaField('简介', validators=[Optional()])
    actors = StringField('主演', validators=[
        Optional(), Length(max=256, message='主演不能超过256个字符')
    ])
    release_date = DateField('上映时间', validators=[Optional()], format='%Y-%m-%d')
    rating = FloatField('评分', validators=[
        Optional(),
        NumberRange(min=0, max=10, message='评分需在0-10之间')
    ], default=0.0)
    poster_url = StringField('海报URL', validators=[Optional(), Length(max=512)])
    trailer_url = StringField('预告片嵌入URL', validators=[Optional(), Length(max=512)])
    category_id = SelectField('影视分类', coerce=int, validators=[Optional()])
    submit = SubmitField('保存')


class CommentForm(FlaskForm):
    """访客影评表单"""
    author = StringField('昵称', validators=[
        Optional(), Length(max=64, message='昵称不能超过64个字符')
    ], default='匿名用户')
    content = TextAreaField('影评内容', validators=[
        DataRequired(message='请输入影评内容'),
        Length(min=1, max=2000, message='影评内容1-2000字')
    ])
    movie_id = HiddenField('影视ID', validators=[DataRequired()])
    submit = SubmitField('发表影评')


class SearchForm(FlaskForm):
    """搜索表单"""
    keyword = StringField('搜索', validators=[
        DataRequired(message='请输入搜索关键词'),
        Length(max=128)
    ])
    submit = SubmitField('搜索')


class CategoryForm(FlaskForm):
    """分类表单"""
    name = StringField('分类名称', validators=[
        DataRequired(message='请输入分类名称'),
        Length(max=32, message='分类名称不能超过32个字符')
    ])
    submit = SubmitField('保存')


class ChangePasswordForm(FlaskForm):
    """管理员修改密码表单"""
    old_password = PasswordField('当前密码', validators=[
        DataRequired(message='请输入当前密码')
    ])
    new_password = PasswordField('新密码', validators=[
        DataRequired(message='请输入新密码'),
        Length(min=6, max=128, message='密码长度至少6位')
    ])
    confirm_password = PasswordField('确认新密码', validators=[
        DataRequired(message='请再次输入新密码'),
        EqualTo('new_password', message='两次密码不一致')
    ])
    submit = SubmitField('确认修改')

    def validate_old_password(self, field):
        """验证当前密码是否正确"""
        from flask import session
        from app.models import Admin
        admin_id = session.get('admin_id')
        if admin_id:
            admin = Admin.query.get(admin_id)
            if admin and not admin.check_password(field.data):
                raise ValidationError('当前密码错误')
