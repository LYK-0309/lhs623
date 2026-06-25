"""前台蓝图 — 游客可访问的影视浏览和影评功能"""
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, current_app, url_for, redirect, flash
from flask_login import current_user, login_required
from app.extensions import db
from app.models import Movie, Category, Comment, User
from app.forms import CommentForm, SearchForm
from sqlalchemy import or_

main_bp = Blueprint('main', __name__, template_folder='../templates/main')


@main_bp.route('/')
def index():
    """前台首页 — 影视列表，按上架时间倒序，支持分页、分类筛选、搜索"""
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    keyword = request.args.get('keyword', '').strip()
    per_page = current_app.config['MOVIES_PER_PAGE']

    query = Movie.query

    # 分类筛选
    if category_id:
        query = query.filter_by(category_id=category_id)

    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                Movie.title.ilike(f'%{keyword}%'),
                Movie.actors.ilike(f'%{keyword}%')
            )
        )

    # 按创建时间倒序
    query = query.order_by(Movie.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    movies = pagination.items

    # 获取所有分类供筛选
    categories = Category.query.all()

    search_form = SearchForm()

    return render_template('main/index.html',
                           movies=movies,
                           pagination=pagination,
                           categories=categories,
                           current_category=category_id,
                           keyword=keyword,
                           search_form=search_form)


@main_bp.route('/search')
def search():
    """独立搜索页"""
    keyword = request.args.get('keyword', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['MOVIES_PER_PAGE']

    if not keyword:
        return render_template('main/search.html', movies=[], keyword='',
                               pagination=None, total=0)

    query = Movie.query.filter(
        or_(
            Movie.title.ilike(f'%{keyword}%'),
            Movie.actors.ilike(f'%{keyword}%')
        )
    ).order_by(Movie.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    movies = pagination.items

    return render_template('main/search.html',
                           movies=movies,
                           keyword=keyword,
                           pagination=pagination,
                           total=pagination.total)


@main_bp.route('/movie/<int:movie_id>')
def detail(movie_id):
    """影视详情页 — 完整信息 + 影评列表 + 影评表单"""
    movie = Movie.query.get_or_404(movie_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['COMMENTS_PER_PAGE']

    pagination = movie.comments.paginate(page=page, per_page=per_page, error_out=False)
    comments = pagination.items

    comment_form = CommentForm(movie_id=movie_id)

    return render_template('main/detail.html',
                           movie=movie,
                           comments=comments,
                           pagination=pagination,
                           comment_form=comment_form)


@main_bp.route('/movie/<int:movie_id>/comment', methods=['POST'])
@login_required
def post_comment(movie_id):
    """发表影评（支持 AJAX + 普通表单提交）"""
    movie = Movie.query.get_or_404(movie_id)
    form = CommentForm()

    if form.validate_on_submit():
        # 已登录用户自动关联 user_id 和使用昵称
        author = current_user.nickname
        user_id = current_user.id

        comment = Comment(
            content=form.content.data,
            author=author,
            movie_id=movie_id,
            user_id=user_id
        )
        db.session.add(comment)
        db.session.commit()

        # 判断是否为 AJAX 请求
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': '影评发表成功！',
                'comment': {
                    'id': comment.id,
                    'author': comment.author,
                    'content': comment.content,
                    'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
                    'user': {
                        'nickname': comment.user.nickname if comment.user else None,
                        'avatar_url': comment.user.avatar_url if comment.user else None
                    } if comment.user else None
                }
            })

        from flask import flash
        flash('影评发表成功！', 'success')
        return redirect(url_for('main.detail', movie_id=movie_id))

    # 表单验证失败
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        errors = {field: errs for field, errs in form.errors.items()}
        return jsonify({'success': False, 'errors': errors}), 400

    return redirect(url_for('main.detail', movie_id=movie_id))


@main_bp.route('/movie/<int:movie_id>/like', methods=['POST'])
@login_required
def like_movie(movie_id):
    """影视点赞（AJAX）"""
    movie = Movie.query.get_or_404(movie_id)
    movie.likes = (movie.likes or 0) + 1
    db.session.commit()
    return jsonify({'success': True, 'likes': movie.likes})


@main_bp.route('/api/movies/search')
@login_required
def api_movies_search():
    """影视搜索 API（AJAX）— 用于聊天页分享影视选择"""
    keyword = (request.args.get('q') or '').strip()
    if keyword:
        movies = Movie.query.filter(
            or_(
                Movie.title.ilike(f'%{keyword}%'),
                Movie.actors.ilike(f'%{keyword}%')
            )
        ).order_by(Movie.created_at.desc()).limit(20).all()
    else:
        movies = Movie.query.order_by(Movie.created_at.desc()).limit(20).all()

    result = []
    for m in movies:
        result.append({
            'id': m.id,
            'title': m.title,
            'intro': (m.intro[:80] + '...') if m.intro and len(m.intro) > 80 else (m.intro or ''),
            'rating': m.rating,
            'poster_url': m.poster_url,
            'category_name': m.category.name if m.category else '',
        })
    return jsonify(success=True, movies=result)
