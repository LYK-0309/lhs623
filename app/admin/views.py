"""管理后台蓝图 — 路由权限拦截，仅登录可进入"""
from functools import wraps
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from app.extensions import db
from app.models import Admin, Movie, Category, Comment
from app.forms import LoginForm, MovieForm, CategoryForm, ChangePasswordForm

admin_bp = Blueprint('admin', __name__, template_folder='../templates/admin')


# ---------- 登录验证装饰器 ----------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('请先登录管理后台', 'warning')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function


# 在所有管理路由前注入当前管理员
@admin_bp.before_request
def load_admin():
    if request.endpoint and request.endpoint.startswith('admin.'):
        if 'admin_id' in session:
            admin_user = Admin.query.get(session['admin_id'])
            # 通过 g 传递，模板中通过 g.admin_user 获取
            from flask import g
            g.admin_user = admin_user


# ---------- 认证 ----------
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """管理员登录"""
    if 'admin_id' in session:
        return redirect(url_for('admin.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        admin_user = Admin.query.filter_by(username=form.username.data).first()
        if admin_user and admin_user.check_password(form.password.data):
            session['admin_id'] = admin_user.id
            session.permanent = True
            flash(f'欢迎回来，{admin_user.username}！', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.dashboard'))
        flash('密码错误', 'danger')
    return render_template('admin/login.html', form=form)


@admin_bp.route('/logout')
@login_required
def logout():
    """管理员注销"""
    session.pop('admin_id', None)
    flash('已安全退出', 'info')
    return redirect(url_for('admin.login'))


# ---------- 仪表盘 ----------
@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """管理后台首页 - 统计概览"""
    from flask import current_app
    movie_count = Movie.query.count()
    category_count = Category.query.count()
    comment_count = Comment.query.count()
    recent_movies = Movie.query.order_by(Movie.created_at.desc()).limit(5).all()
    recent_comments = Comment.query.order_by(Comment.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html',
                           movie_count=movie_count,
                           category_count=category_count,
                           comment_count=comment_count,
                           recent_movies=recent_movies,
                           recent_comments=recent_comments)


# ---------- 影视 CRUD ----------
@admin_bp.route('/movies')
@login_required
def movie_list():
    """影视列表（分页）"""
    from flask import current_app
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ADMIN_MOVIES_PER_PAGE']
    pagination = Movie.query.order_by(Movie.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    movies = pagination.items
    return render_template('admin/movie_list.html', movies=movies, pagination=pagination)


@admin_bp.route('/movies/new', methods=['GET', 'POST'])
@login_required
def movie_new():
    """新增影视"""
    form = MovieForm()
    form.category_id.choices = _category_choices()
    if form.validate_on_submit():
        movie = Movie(
            title=form.title.data,
            intro=form.intro.data,
            actors=form.actors.data,
            release_date=form.release_date.data,
            rating=form.rating.data or 0.0,
            poster_url=form.poster_url.data,
            trailer_url=form.trailer_url.data,
            category_id=form.category_id.data if form.category_id.data else None
        )
        db.session.add(movie)
        db.session.commit()
        flash('影视添加成功！', 'success')
        return redirect(url_for('admin.movie_list'))
    return render_template('admin/movie_form.html', form=form, title='新增影视', is_edit=False)


@admin_bp.route('/movies/<int:movie_id>/edit', methods=['GET', 'POST'])
@login_required
def movie_edit(movie_id):
    """编辑影视"""
    movie = Movie.query.get_or_404(movie_id)
    form = MovieForm(obj=movie)
    form.category_id.choices = _category_choices()
    if form.validate_on_submit():
        movie.title = form.title.data
        movie.intro = form.intro.data
        movie.actors = form.actors.data
        movie.release_date = form.release_date.data
        movie.rating = form.rating.data or 0.0
        movie.poster_url = form.poster_url.data
        movie.trailer_url = form.trailer_url.data
        movie.category_id = form.category_id.data if form.category_id.data else None
        db.session.commit()
        flash('影视信息已更新！', 'success')
        return redirect(url_for('admin.movie_list'))
    return render_template('admin/movie_form.html', form=form, title='编辑影视',
                           is_edit=True, movie=movie)


@admin_bp.route('/movies/<int:movie_id>/delete', methods=['POST'])
@login_required
def movie_delete(movie_id):
    """删除影视"""
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    flash('影视已删除', 'info')
    return redirect(url_for('admin.movie_list'))


# ---------- 分类管理 ----------
@admin_bp.route('/categories')
@login_required
def category_list():
    """分类列表"""
    categories = Category.query.all()
    form = CategoryForm()
    return render_template('admin/category_list.html', categories=categories, form=form)


@admin_bp.route('/categories/new', methods=['POST'])
@login_required
def category_new():
    """新增分类"""
    form = CategoryForm()
    if form.validate_on_submit():
        existing = Category.query.filter_by(name=form.name.data).first()
        if existing:
            flash('该分类已存在', 'warning')
        else:
            cat = Category(name=form.name.data)
            db.session.add(cat)
            db.session.commit()
            flash('分类添加成功！', 'success')
    return redirect(url_for('admin.category_list'))


@admin_bp.route('/categories/<int:cat_id>/delete', methods=['POST'])
@login_required
def category_delete(cat_id):
    """删除分类"""
    cat = Category.query.get_or_404(cat_id)
    if cat.movies.count() > 0:
        flash(f'分类"{cat.name}"下还有影视，无法删除', 'danger')
    else:
        db.session.delete(cat)
        db.session.commit()
        flash('分类已删除', 'info')
    return redirect(url_for('admin.category_list'))


# ---------- 影评管理 ----------
@admin_bp.route('/comments')
@login_required
def comment_list():
    """影评列表（分页）"""
    from flask import current_app
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['COMMENTS_PER_PAGE']
    pagination = Comment.query.order_by(Comment.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    comments = pagination.items
    return render_template('admin/comment_list.html', comments=comments, pagination=pagination)


@admin_bp.route('/comments/<int:comment_id>/delete', methods=['POST'])
@login_required
def comment_delete(comment_id):
    """删除影评"""
    comment = Comment.query.get_or_404(comment_id)
    movie_id = comment.movie_id
    db.session.delete(comment)
    db.session.commit()
    flash('影评已删除', 'info')
    # 如果是从影评列表页面来的，返回列表；否则返回影视详情页
    referrer = request.referrer or ''
    if 'admin/comments' in referrer:
        return redirect(url_for('admin.comment_list'))
    return redirect(url_for('admin.comment_list'))


# ---------- 辅助函数 ----------
def _category_choices():
    """返回分类下拉选项"""
    categories = Category.query.all()
    choices = [(0, '-- 请选择分类 --')]
    choices.extend([(c.id, c.name) for c in categories])
    return choices


# ---------- 修改密码 ----------
@admin_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改管理员密码"""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        admin_user = Admin.query.get(session['admin_id'])
        admin_user.set_password(form.new_password.data)
        db.session.commit()
        flash('密码修改成功！', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/change_password.html', form=form)
