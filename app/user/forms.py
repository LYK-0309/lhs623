from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FileField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError, EqualTo
from app.extensions import db
from app.models import User, VerificationCode
import re


class QQEmailValidator:
    """QQ 邮箱格式验证"""
    def __call__(self, form, field):
        value = field.data.strip()
        if not re.match(r'^\d+@qq\.com$', value):
            raise ValidationError('请输入有效的 QQ 邮箱（格式：数字@qq.com）')


def _validate_password(form, field):
    """密码：8-15 位，不能包含空格"""
    pwd = field.data
    if len(pwd) < 8 or len(pwd) > 15:
        raise ValidationError('密码长度需为 8-15 位')
    if ' ' in pwd:
        raise ValidationError('密码不能包含空格')


class RequestCodeForm(FlaskForm):
    """请求验证码表单（AJAX 提交，无 CSRF）"""
    target = StringField('QQ 邮箱', validators=[DataRequired(message='请输入 QQ 邮箱')])
    purpose = 'register'

    def validate_target(self, field):
        value = field.data.strip()
        if not re.match(r'^\d+@qq\.com$', value):
            raise ValidationError('请输入有效的 QQ 邮箱（格式：数字@qq.com）')


class RegisterForm(FlaskForm):
    """用户注册表单（仅 QQ 邮箱）"""
    email = StringField('QQ 邮箱', validators=[
        DataRequired(message='请输入 QQ 邮箱'),
        Length(max=128),
        QQEmailValidator()
    ])
    verification_code = StringField('验证码', validators=[
        DataRequired(message='请输入验证码'),
        Length(min=6, max=6, message='验证码为 6 位数字')
    ])
    nickname = StringField('昵称', validators=[
        DataRequired(message='请输入昵称'), Length(min=1, max=64, message='昵称 1-64 个字符')
    ])
    password = PasswordField('密码', validators=[
        DataRequired(message='请输入密码'), _validate_password
    ])
    confirm_password = PasswordField('确认密码', validators=[
        DataRequired(message='请再次输入密码'), EqualTo('password', message='两次密码不一致')
    ])
    submit = SubmitField('注册')

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        email = self.email.data.strip()
        # 检查邮箱是否已注册
        existing = User.query.filter_by(email=email).first()
        if existing:
            self.email.errors.append('该 QQ 邮箱已注册，请直接登录')
            return False
        # 验证验证码
        ok, msg = VerificationCode.verify_code(email, self.verification_code.data.strip(), 'register')
        if not ok:
            self.verification_code.errors.append(msg)
            return False
        return True


class LoginForm(FlaskForm):
    """用户密码登录表单（仅 QQ 邮箱）"""
    email = StringField('QQ 邮箱', validators=[
        DataRequired(message='请输入 QQ 邮箱'),
        QQEmailValidator()
    ])
    password = PasswordField('密码', validators=[DataRequired(message='请输入密码')])
    remember = SubmitField('记住我', render_kw={'type': 'checkbox'})
    submit = SubmitField('登录')

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        email = self.email.data.strip()
        user = User.query.filter_by(email=email).first()
        if not user:
            self.email.errors.append('该邮箱未注册')
            return False
        if not user.check_password(self.password.data):
            self.password.errors.append('密码错误')
            return False
        self.user = user
        return True


class CodeLoginForm(FlaskForm):
    """QQ 邮箱验证码登录表单"""
    email = StringField('QQ 邮箱', validators=[
        DataRequired(message='请输入 QQ 邮箱'),
        Length(max=128),
        QQEmailValidator()
    ])
    verification_code = StringField('验证码', validators=[
        DataRequired(message='请输入验证码'),
        Length(min=6, max=6, message='验证码为 6 位数字')
    ])
    remember = SubmitField('记住我', render_kw={'type': 'checkbox'})
    submit = SubmitField('验证码登录')

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        email = self.email.data.strip()
        user = User.query.filter_by(email=email).first()
        if not user:
            self.email.errors.append('该邮箱未注册，请先注册')
            return False
        ok, msg = VerificationCode.verify_code(email, self.verification_code.data.strip(), 'login')
        if not ok:
            self.verification_code.errors.append(msg)
            return False
        self.user = user
        return True


class ForgotPasswordForm(FlaskForm):
    """忘记密码 — 第一步：填写邮箱，获取验证码"""
    email = StringField('QQ 邮箱', validators=[
        DataRequired(message='请输入注册时使用的 QQ 邮箱'),
        Length(max=128),
        QQEmailValidator()
    ])
    verification_code = StringField('验证码', validators=[
        DataRequired(message='请输入验证码'),
        Length(min=6, max=6, message='验证码为 6 位数字')
    ])
    new_password = PasswordField('新密码', validators=[
        DataRequired(message='请输入新密码'), _validate_password
    ])
    confirm_password = PasswordField('确认新密码', validators=[
        DataRequired(message='请再次输入新密码'),
        EqualTo('new_password', message='两次密码不一致')
    ])
    submit = SubmitField('重置密码')

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        email = self.email.data.strip()
        user = User.query.filter_by(email=email).first()
        if not user:
            self.email.errors.append('该邮箱未注册')
            return False
        ok, msg = VerificationCode.verify_code(email, self.verification_code.data.strip(), 'reset')
        if not ok:
            self.verification_code.errors.append(msg)
            return False
        self.user = user
        return True


class ProfileForm(FlaskForm):
    """个人资料表单（修改昵称 / 头像）"""
    nickname = StringField('昵称', validators=[
        DataRequired(message='昵称不能为空'), Length(min=1, max=64, message='昵称 1-64 个字符')
    ])
    avatar = FileField('头像（可选，最大 2MB）', validators=[])
    submit = SubmitField('保存修改')


class ChangePasswordForm(FlaskForm):
    """修改密码表单"""
    old_password = PasswordField('当前密码', validators=[DataRequired(message='请输入当前密码')])
    new_password = PasswordField('新密码', validators=[
        DataRequired(message='请输入新密码'), _validate_password
    ])
    confirm_password = PasswordField('确认新密码', validators=[
        DataRequired(message='请再次输入新密码'), EqualTo('new_password', message='两次密码不一致')
    ])
    submit = SubmitField('修改密码')


class DeleteAccountForm(FlaskForm):
    """注销账号表单 — 需确认密码"""
    password = PasswordField('当前密码', validators=[DataRequired(message='请输入当前密码以确认注销')])
    confirm_text = StringField('确认输入', validators=[
        DataRequired(message='请输入确认文字'),
    ])
    submit = SubmitField('永久注销账号')

    def validate_confirm_text(self, field):
        if field.data.strip() != '确认注销':
            raise ValidationError('请输入"确认注销"以确认操作')
