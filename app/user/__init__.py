"""用户蓝图 — 注册登录、个人资料"""
from flask import Blueprint

user_bp = Blueprint('user', __name__, template_folder='../templates/user')

from app.user import views
