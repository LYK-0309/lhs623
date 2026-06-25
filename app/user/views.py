"""用户蓝图路由 — 注册、登录、个人资料（仅 QQ 邮箱）"""
import os
import re

from flask import (
    Blueprint, render_template, redirect, url_for, flash,
    request, session, jsonify, current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import User, VerificationCode, Friendship, Message, Movie
from app.user.forms import (
    RegisterForm, LoginForm, CodeLoginForm, ForgotPasswordForm,
    ProfileForm, ChangePasswordForm, DeleteAccountForm
)
from app.utils.email import send_verification_email, MailNotConfiguredError
from app.utils.time import beijing_now

user_bp = Blueprint('user', __name__, template_folder='../templates/user')


# ─── 辅助函数 ────────────────────────────────────────────────

def _allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def _save_avatar_base64(file):
    """将上传的头像转为 Base64 存入数据库，返回 True/False"""
    import base64
    if not file or not file.filename:
        return False
    if not _allowed_file(file.filename):
        return False
    try:
        file_data = file.read()
        if len(file_data) > 2 * 1024 * 1024:
            return False
        ext = file.filename.rsplit('.', 1)[1].lower()
        mime_map = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
                    'gif': 'image/gif', 'webp': 'image/webp'}
        mime = mime_map.get(ext, 'image/png')
        current_user.avatar_data = base64.b64encode(file_data).decode('utf-8')
        current_user.avatar_mime = mime
        current_user.avatar = None  # 清除旧文件头像
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False


def _save_avatar(file):
    """保存头像文件，返回文件名；失败返回 None（保留兼容）"""
    if not file or not file.filename:
        return None
    if not _allowed_file(file.filename):
        return None
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f'user_{current_user.id}_{int(beijing_now().timestamp())}.{ext}'
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    return filename


# ─── 请求验证码（AJAX）────────────────────────────────────────

@user_bp.route('/request-code', methods=['POST'])
def request_code():
    """
    发送验证码到 QQ 邮箱（AJAX 调用）
    purpose: register / login / reset
    """
    email = (request.form.get('email') or '').strip()
    purpose = (request.form.get('purpose') or '').strip()

    if not email or not purpose:
        return jsonify(success=False, message='参数不完整'), 400

    # 验证用途合法
    if purpose not in ('register', 'login', 'reset'):
        return jsonify(success=False, message='无效的操作类型'), 400

    # 验证 QQ 邮箱格式
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return jsonify(success=False, message='请输入有效的邮箱地址'), 400

    # 注册时检查账号是否已存在
    if purpose == 'register':
        if User.query.filter_by(email=email).first():
            return jsonify(success=False, message='该邮箱已注册'), 400

    # 登录 / 重置密码时检查账号是否存在
    if purpose in ('login', 'reset'):
        if not User.query.filter_by(email=email).first():
            return jsonify(success=False, message='该邮箱未注册'), 400

    # 生成验证码
    code = VerificationCode.generate_code(email, purpose)

    # 检查邮件服务是否已配置
    mail_enabled = current_app.config.get('MAIL_ENABLED', False)

    if mail_enabled:
        # 已配置：尝试发送邮件
        try:
            ok, msg = send_verification_email(email, code)
        except MailNotConfiguredError as e:
            return jsonify(success=False, message=str(e)), 500
        if not ok:
            return jsonify(success=False, message=msg), 500
        return jsonify(success=True, message=msg)
    else:
        # 未配置：演示模式，直接返回验证码（仅用于开发/测试环境）
        import sys
        is_debug = current_app.config.get('DEBUG', False) or \
                   current_app.config.get('TESTING', False)
        if is_debug or 'sqlite' in str(current_app.config.get('SQLALCHEMY_DATABASE_URI', '')):
            return jsonify(
                success=True,
                message=f'【演示模式】验证码已生成（未发送邮件）：{code}',
                debug_code=code,  # 前端可读取显示
                demo_mode=True
            )
        else:
            # 生产环境但未配置邮件服务：给出详细提示
            return jsonify(
                success=False,
                message='系统邮件服务尚未配置，无法发送验证码。请联系管理员在 CloudBase 控制台设置 MAIL_USERNAME 和 MAIL_PASSWORD 环境变量。'
            ), 503


# ─── 配置状态 ───────────────────────────────────────────────

@user_bp.route('/config-status')
def config_status():
    """返回邮件服务的配置状态"""
    return jsonify({
        'mail_enabled': current_app.config.get('MAIL_ENABLED', False),
    })


# ─── 注册 ───────────────────────────────────────────────────

@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data.strip(),
            nickname=form.nickname.data.strip(),
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('注册成功！已自动登录', 'success')
        login_user(user, remember=True)
        return redirect(url_for('user.profile'))

    mail_enabled = current_app.config.get('MAIL_ENABLED', False)
    return render_template('user/register.html', form=form, mail_enabled=mail_enabled)


# ─── 密码登录 ───────────────────────────────────────────────

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    code_form = CodeLoginForm()

    if form.validate_on_submit():
        remember = request.form.get('remember') == '1'
        login_user(form.user, remember=remember)
        flash(f'欢迎回来，{form.user.nickname}！', 'success')
        next_page = request.args.get('next')
        return redirect(next_page or url_for('main.index'))

    mail_enabled = current_app.config.get('MAIL_ENABLED', False)
    return render_template('user/login.html', form=form, code_form=code_form,
                           active_tab='password', mail_enabled=mail_enabled)


# ─── 验证码登录 ─────────────────────────────────────────────

@user_bp.route('/code-login', methods=['POST'])
def code_login():
    """QQ 邮箱验证码登录"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()       # 空实例，仅用于渲染密码登录标签
    code_form = CodeLoginForm()

    if code_form.validate_on_submit():
        remember = request.form.get('remember') == '1'
        login_user(code_form.user, remember=remember)
        flash(f'欢迎回来，{code_form.user.nickname}！', 'success')
        next_page = request.args.get('next')
        return redirect(next_page or url_for('main.index'))

    mail_enabled = current_app.config.get('MAIL_ENABLED', False)
    return render_template('user/login.html', form=form, code_form=code_form,
                           active_tab='code', mail_enabled=mail_enabled)


# ─── 忘记密码 ───────────────────────────────────────────────

@user_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """忘记密码：邮箱验证码 → 重置密码（一步完成）"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = form.user
        user.set_password(form.new_password.data)
        db.session.commit()
        flash('密码重置成功，请用新密码登录', 'success')
        return redirect(url_for('user.login'))

    return render_template('user/forgot_password.html', form=form)


# ─── 注销 ───────────────────────────────────────────────────

@user_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已安全退出', 'info')
    return redirect(url_for('main.index'))


# ─── 个人资料 ───────────────────────────────────────────────

@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    change_pwd_form = ChangePasswordForm()

    if form.validate_on_submit():
        current_user.nickname = form.nickname.data.strip()

        if form.avatar.data:
            if _save_avatar_base64(form.avatar.data):
                flash('头像已更新', 'success')
            else:
                flash('头像格式不支持或文件过大（最大 2MB），仅支持 png/jpg/jpeg/gif/webp', 'warning')

        db.session.commit()
        flash('个人资料已更新', 'success')
        return redirect(url_for('user.profile'))

    if request.method == 'GET':
        form.nickname.data = current_user.nickname

    return render_template(
        'user/profile.html',
        form=form,
        change_pwd_form=change_pwd_form,
        user=current_user
    )


# ─── 修改密码 ───────────────────────────────────────────────

@user_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.old_password.data):
            flash('当前密码错误', 'danger')
            return redirect(url_for('user.profile'))
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash('密码修改成功，请重新登录', 'success')
        logout_user()
        return redirect(url_for('user.login'))

    for field, errors in form.errors.items():
        for err in errors:
            flash(f'{getattr(form, field).label.text}：{err}', 'danger')
    return redirect(url_for('user.profile'))


# ─── 账号注销 ───────────────────────────────────────────────

@user_bp.route('/delete-account', methods=['GET', 'POST'])
@login_required
def delete_account():
    """永久注销账号 — 需密码确认 + 输入确认文字"""
    form = DeleteAccountForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.password.data):
            flash('密码错误，注销失败', 'danger')
            return redirect(url_for('user.delete_account'))

        user_id = current_user.id
        nickname = current_user.nickname

        # 删除该用户相关的好友关系
        Friendship.query.filter(
            (Friendship.requester_id == user_id) |
            (Friendship.receiver_id == user_id)
        ).delete(synchronize_session=False)

        # 删除用户（Comments 会通过 cascade 自动删除）
        db.session.delete(current_user)
        db.session.commit()

        logout_user()
        flash(f'账号「{nickname}」已永久注销，感谢您的使用', 'info')
        return redirect(url_for('main.index'))

    return render_template('user/delete_account.html', form=form)


# ─── 好友功能 ───────────────────────────────────────────────

@user_bp.route('/friends')
@login_required
def friends():
    """好友列表页 — 显示好友、待处理请求"""
    # 已接受的好友
    accepted = Friendship.query.filter_by(
        status='accepted'
    ).filter(
        (Friendship.requester_id == current_user.id) |
        (Friendship.receiver_id == current_user.id)
    ).order_by(Friendship.updated_at.desc()).all()

    friend_list = []
    for f in accepted:
        friend_obj = f.receiver if f.requester_id == current_user.id else f.requester
        friend_list.append({
            'friendship_id': f.id,
            'user': friend_obj,
        })

    # 收到的好友请求（待处理）
    pending_requests = Friendship.query.filter_by(
        receiver_id=current_user.id, status='pending'
    ).order_by(Friendship.created_at.desc()).all()

    # 发出的好友请求（等待对方确认）
    sent_requests = Friendship.query.filter_by(
        requester_id=current_user.id, status='pending'
    ).order_by(Friendship.created_at.desc()).all()

    return render_template(
        'user/friends.html',
        friend_list=friend_list,
        pending_requests=pending_requests,
        sent_requests=sent_requests,
    )


@user_bp.route('/friends/search')
@login_required
def friends_search():
    """搜索用户（AJAX）— 按昵称或 QQ 邮箱搜索"""
    keyword = (request.args.get('q') or '').strip()
    if not keyword or len(keyword) < 1:
        return jsonify(success=True, users=[])

    # 搜索非自己的用户
    users = User.query.filter(
        User.id != current_user.id,
        db.or_(
            User.nickname.ilike(f'%{keyword}%'),
            User.email.ilike(f'%{keyword}%')
        )
    ).limit(10).all()

    result = []
    for u in users:
        # 检查好友关系状态
        friendship = Friendship.query.filter(
            db.or_(
                db.and_(Friendship.requester_id == current_user.id,
                        Friendship.receiver_id == u.id),
                db.and_(Friendship.requester_id == u.id,
                        Friendship.receiver_id == current_user.id)
            )
        ).first()

        if friendship:
            if friendship.status == 'accepted':
                status = 'friends'
            elif friendship.status == 'pending':
                if friendship.requester_id == current_user.id:
                    status = 'sent'
                else:
                    status = 'received'
            else:
                status = 'rejected'
        else:
            status = 'none'

        result.append({
            'id': u.id,
            'nickname': u.nickname,
            'email': u.email,
            'avatar_url': u.avatar_url,
            'status': status,
        })

    return jsonify(success=True, users=result)


@user_bp.route('/friends/request/<int:user_id>', methods=['POST'])
@login_required
def friends_send_request(user_id):
    """发送好友请求"""
    target = User.query.get_or_404(user_id)

    if target.id == current_user.id:
        return jsonify(success=False, message='不能添加自己为好友'), 400

    # 检查是否已有关系记录
    existing = Friendship.query.filter(
        db.or_(
            db.and_(Friendship.requester_id == current_user.id,
                    Friendship.receiver_id == target.id),
            db.and_(Friendship.requester_id == target.id,
                    Friendship.receiver_id == current_user.id)
        )
    ).first()

    if existing:
        if existing.status == 'accepted':
            return jsonify(success=False, message='你们已经是好友了'), 400
        elif existing.status == 'pending':
            if existing.requester_id == current_user.id:
                return jsonify(success=False, message='好友请求已发送，等待对方确认'), 400
            else:
                # 对方先发了请求给我，直接接受
                existing.status = 'accepted'
                db.session.commit()
                return jsonify(success=True, message=f'已与 {target.nickname} 成为好友')
        elif existing.status == 'rejected':
            # 重新发送请求
            existing.requester_id = current_user.id
            existing.receiver_id = target.id
            existing.status = 'pending'
            db.session.commit()
            return jsonify(success=True, message=f'好友请求已发送给 {target.nickname}')

    # 创建新的好友请求
    friendship = Friendship(
        requester_id=current_user.id,
        receiver_id=target.id,
        status='pending'
    )
    db.session.add(friendship)
    db.session.commit()
    return jsonify(success=True, message=f'好友请求已发送给 {target.nickname}')


@user_bp.route('/friends/accept/<int:friendship_id>', methods=['POST'])
@login_required
def friends_accept(friendship_id):
    """接受好友请求"""
    friendship = Friendship.query.get_or_404(friendship_id)

    if friendship.receiver_id != current_user.id:
        return jsonify(success=False, message='无权操作'), 403

    if friendship.status != 'pending':
        return jsonify(success=False, message='该请求已处理'), 400

    friendship.status = 'accepted'
    db.session.commit()
    requester = friendship.requester
    return jsonify(success=True, message=f'已接受 {requester.nickname} 的好友请求')


@user_bp.route('/friends/reject/<int:friendship_id>', methods=['POST'])
@login_required
def friends_reject(friendship_id):
    """拒绝好友请求"""
    friendship = Friendship.query.get_or_404(friendship_id)

    if friendship.receiver_id != current_user.id:
        return jsonify(success=False, message='无权操作'), 403

    friendship.status = 'rejected'
    db.session.commit()
    return jsonify(success=True, message='已拒绝好友请求')


@user_bp.route('/friends/remove/<int:friendship_id>', methods=['POST'])
@login_required
def friends_remove(friendship_id):
    """删除好友"""
    friendship = Friendship.query.get_or_404(friendship_id)

    if friendship.requester_id != current_user.id and friendship.receiver_id != current_user.id:
        return jsonify(success=False, message='无权操作'), 403

    if friendship.status != 'accepted':
        return jsonify(success=False, message='你们还不是好友'), 400

    friend_obj = friendship.receiver if friendship.requester_id == current_user.id else friendship.requester
    db.session.delete(friendship)
    db.session.commit()
    return jsonify(success=True, message=f'已删除好友 {friend_obj.nickname}')


@user_bp.route('/friends/cancel/<int:friendship_id>', methods=['POST'])
@login_required
def friends_cancel(friendship_id):
    """撤回好友请求"""
    friendship = Friendship.query.get_or_404(friendship_id)

    if friendship.requester_id != current_user.id:
        return jsonify(success=False, message='无权操作'), 403

    if friendship.status != 'pending':
        return jsonify(success=False, message='该请求已处理'), 400

    db.session.delete(friendship)
    db.session.commit()
    return jsonify(success=True, message='已撤回好友请求')


# ── 好友聊天 ─────────────────────────────────────────

@user_bp.route('/friends/chat/<int:friend_id>')
@login_required
def chat(friend_id):
    """与好友的聊天页面"""
    friend = User.query.get_or_404(friend_id)
    friendship = Friendship.query.filter(
        Friendship.status == 'accepted',
        db.or_(
            db.and_(Friendship.requester_id == current_user.id, Friendship.receiver_id == friend_id),
            db.and_(Friendship.requester_id == friend_id, Friendship.receiver_id == current_user.id)
        )
    ).first()
    if not friendship:
        flash('你们还不是好友', 'warning')
        return redirect(url_for('user.friends'))
    Message.query.filter_by(sender_id=friend_id, receiver_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return render_template('user/chat.html', friend=friend)


@user_bp.route('/friends/send-message/<int:friend_id>', methods=['POST'])
@login_required
def send_message(friend_id):
    """发送聊天消息（AJAX）"""
    friend = User.query.get_or_404(friend_id)
    friendship = Friendship.query.filter(
        Friendship.status == 'accepted',
        db.or_(
            db.and_(Friendship.requester_id == current_user.id, Friendship.receiver_id == friend_id),
            db.and_(Friendship.requester_id == friend_id, Friendship.receiver_id == current_user.id)
        )
    ).first()
    if not friendship:
        return jsonify(success=False, message='你们还不是好友'), 403
    data = request.get_json() or {}
    content = (data.get('content') or '').strip()
    if not content:
        return jsonify(success=False, message='消息内容不能为空'), 400
    msg = Message(sender_id=current_user.id, receiver_id=friend_id, content=content, message_type='text')
    db.session.add(msg)
    db.session.commit()
    return jsonify(success=True, message='发送成功')


@user_bp.route('/friends/share-movie/<int:friend_id>', methods=['POST'])
@login_required
def share_movie_to_friend(friend_id):
    """在聊天中直接分享影视给好友（AJAX）"""
    friend = User.query.get_or_404(friend_id)
    friendship = Friendship.query.filter(
        Friendship.status == 'accepted',
        db.or_(
            db.and_(Friendship.requester_id == current_user.id, Friendship.receiver_id == friend_id),
            db.and_(Friendship.requester_id == friend_id, Friendship.receiver_id == current_user.id)
        )
    ).first()
    if not friendship:
        return jsonify(success=False, message='你们还不是好友'), 403

    data = request.get_json() or {}
    movie_id = data.get('movie_id')
    if not movie_id:
        return jsonify(success=False, message='请选择要分享的影视'), 400

    movie = Movie.query.get(int(movie_id))
    if not movie:
        return jsonify(success=False, message='影视不存在'), 404

    msg = Message(
        sender_id=current_user.id,
        receiver_id=friend_id,
        content=f'分享了影视《{movie.title}》给你，快来看看吧！',
        message_type='share_movie',
        related_movie_id=movie.id
    )
    db.session.add(msg)
    db.session.commit()
    return jsonify(success=True, message=f'已分享《{movie.title}》给 {friend.nickname}')


@user_bp.route('/friends/messages/<int:friend_id>')
@login_required
def get_messages(friend_id):
    """获取与好友的聊天记录（AJAX）"""
    friend = User.query.get_or_404(friend_id)
    friendship = Friendship.query.filter(
        Friendship.status == 'accepted',
        db.or_(
            db.and_(Friendship.requester_id == current_user.id, Friendship.receiver_id == friend_id),
            db.and_(Friendship.requester_id == friend_id, Friendship.receiver_id == current_user.id)
        )
    ).first()
    if not friendship:
        return jsonify(success=False, message='你们还不是好友'), 403
    messages = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == current_user.id, Message.receiver_id == friend_id),
            db.and_(Message.sender_id == friend_id, Message.receiver_id == current_user.id)
        )
    ).order_by(Message.created_at.asc()).limit(100).all()
    result = []
    for m in messages:
        result.append({
            'id': m.id,
            'sender_id': m.sender_id,
            'content': m.content,
            'message_type': m.message_type,
            'related_movie_id': m.related_movie_id,
            'created_at': m.created_at.strftime('%Y-%m-%d %H:%M'),
            'is_me': m.sender_id == current_user.id,
        })
    return jsonify(success=True, messages=result)


@user_bp.route('/friends/unread-count')
@login_required
def unread_count():
    """获取未读消息数（AJAX）"""
    count = Message.query.filter_by(receiver_id=current_user.id, is_read=False).count()
    return jsonify(success=True, count=count)


@user_bp.route('/notifications')
@login_required
def notifications():
    """
    综合通知数量（AJAX）
    返回：unread_messages（未读聊天消息数）、
          pending_requests（待处理好友请求数）、
          total（总和）
    """
    unread_messages = Message.query.filter_by(
        receiver_id=current_user.id, is_read=False
    ).count()
    pending_requests = Friendship.query.filter_by(
        receiver_id=current_user.id, status='pending'
    ).count()
    return jsonify(
        success=True,
        unread_messages=unread_messages,
        pending_requests=pending_requests,
        total=unread_messages + pending_requests
    )


# ── 好友列表 API ─────────────────────────────────

@user_bp.route('/friends/accepted')
@login_required
def friends_accepted():
    """获取已接受的好友列表（AJAX）"""
    friendships = Friendship.query.filter_by(status='accepted').filter(
        db.or_(Friendship.requester_id == current_user.id, Friendship.receiver_id == current_user.id)
    ).all()
    result = []
    for f in friendships:
        f_user = f.receiver if f.requester_id == current_user.id else f.requester
        result.append({
            'id': f_user.id,
            'nickname': f_user.nickname,
            'avatar_url': f_user.avatar_url or '',
            'email': f_user.email or '',
        })
    return jsonify(success=True, friends=result)


# ── 分享影视给好友 ─────────────────────────────────

@user_bp.route('/movie/<int:movie_id>/share', methods=['GET', 'POST'])
@login_required
def share_movie(movie_id):
    """分享影视给好友"""
    movie = Movie.query.get_or_404(movie_id)
    if request.method == 'POST':
        data = request.get_json() or {}
        friend_id = data.get('friend_id')
        if not friend_id:
            return jsonify(success=False, message='请选择好友'), 400
        friend = User.query.get_or_404(int(friend_id))
        friendship = Friendship.query.filter(
            Friendship.status == 'accepted',
            db.or_(
                db.and_(Friendship.requester_id == current_user.id, Friendship.receiver_id == friend.id),
                db.and_(Friendship.requester_id == friend.id, Friendship.receiver_id == current_user.id)
            )
        ).first()
        if not friendship:
            return jsonify(success=False, message='你们还不是好友'), 403
        msg = Message(
            sender_id=current_user.id,
            receiver_id=friend.id,
            content=f'分享了影视《{movie.title}》给你',
            message_type='share_movie',
            related_movie_id=movie.id
        )
        db.session.add(msg)
        db.session.commit()
        return jsonify(success=True, message=f'已分享给 {friend.nickname}')
    accepted = Friendship.query.filter_by(status='accepted').filter(
        db.or_(Friendship.requester_id == current_user.id, Friendship.receiver_id == current_user.id)
    ).all()
    friend_list = []
    for f in accepted:
        f_user = f.receiver if f.requester_id == current_user.id else f.requester
        friend_list.append(f_user)
    return render_template('user/share_movie.html', movie=movie, friend_list=friend_list)

