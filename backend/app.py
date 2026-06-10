from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from models import db, Post, Comment
import os
from datetime import datetime, timezone, timedelta
from functools import wraps

app = Flask(__name__, static_folder='../frontend')
CORS(app)

# Database config
db_path = os.path.join(os.path.dirname(__file__), 'success_diary.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

# ---- Rate Limiter (simple in-memory) ----
from collections import defaultdict
import time
rate_limits = defaultdict(list)

def rate_limit(max_requests=30, window=60):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            ip = request.remote_addr or 'unknown'
            now = time.time()
            rate_limits[ip] = [t for t in rate_limits[ip] if now - t < window]
            if len(rate_limits[ip]) >= max_requests:
                return jsonify({'error': '请求太频繁，请稍后再试'}), 429
            rate_limits[ip].append(now)
            return f(*args, **kwargs)
        return wrapper
    return decorator

# ============ API Routes ============

@app.route('/api/posts', methods=['GET'])
def get_posts():
    """获取帖子列表，支持排序和搜索"""
    sort = request.args.get('sort', 'latest')
    search = request.args.get('search', '').strip()
    tag = request.args.get('tag', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = Post.query.filter_by(is_active=True)

    if search:
        query = query.filter(
            db.or_(
                Post.title.contains(search),
                Post.content.contains(search)
            )
        )
    if tag:
        query = query.filter(Post.tags.contains(tag))

    if sort == 'hot':
        query = query.order_by(Post.likes_count.desc(), Post.created_at.desc())
    elif sort == 'most_liked':
        query = query.order_by(Post.likes_count.desc())
    else:
        query = query.order_by(Post.created_at.desc())

    total = query.count()
    posts = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'posts': [p.to_dict() for p in posts],
        'total': total,
        'page': page,
        'pages': (total + per_page - 1) // per_page
    })

@app.route('/api/posts', methods=['POST'])
@rate_limit(max_requests=10, window=60)
def create_post():
    """发布新的成功经验"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '请提供内容'}), 400

    title = (data.get('title') or '').strip()
    content = (data.get('content') or '').strip()
    tags = (data.get('tags') or '').strip()

    if not title:
        return jsonify({'error': '标题不能为空'}), 400
    if not content:
        return jsonify({'error': '内容不能为空'}), 400
    if len(title) > 100:
        return jsonify({'error': '标题不能超过100个字'}), 400
    if len(content) > 10000:
        return jsonify({'error': '内容不能超过10000个字'}), 400

    # Generate anonymous nickname
    import random
    adjectives = ['勇敢的', '智慧的', '温暖的', '坚韧的', '乐观的', '专注的', '真诚的', '积极的',
                  '勤奋的', '从容的', '谦逊的', '热情的', '自由的', '踏实的', '明亮的', '沉静的']
    nouns = ['追梦人', '探索者', '实干家', '奋斗者', '思考者', '行动派', '梦想家', '前行者',
             '创造者', '攀登者', '远航者', '破浪者', '星辰', '曙光', '长风', '微光']
    nickname = f"{random.choice(adjectives)}{random.choice(nouns)}"

    post = Post(
        title=title,
        content=content,
        tags=tags,
        author_nickname=nickname,
        ip_address=request.remote_addr
    )
    db.session.add(post)
    db.session.commit()

    return jsonify(post.to_dict()), 201

@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    """获取单个帖子详情"""
    post = Post.query.get_or_404(post_id)
    return jsonify(post.to_dict())

@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    """点赞"""
    post = Post.query.get_or_404(post_id)
    post.likes_count += 1
    db.session.commit()
    return jsonify({'likes_count': post.likes_count})

@app.route('/api/posts/<int:post_id>/view', methods=['POST'])
def view_post(post_id):
    """增加浏览次数"""
    post = Post.query.get_or_404(post_id)
    post.views_count += 1
    db.session.commit()
    return jsonify({'views_count': post.views_count})

@app.route('/api/posts/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    """获取帖子的评论"""
    comments = Comment.query.filter_by(post_id=post_id, is_active=True)\
        .order_by(Comment.created_at.asc()).all()
    return jsonify([c.to_dict() for c in comments])

@app.route('/api/posts/<int:post_id>/comments', methods=['POST'])
@rate_limit(max_requests=10, window=60)
def create_comment(post_id):
    """发表评论"""
    post = Post.query.get_or_404(post_id)
    data = request.get_json()
    if not data or not data.get('content', '').strip():
        return jsonify({'error': '评论内容不能为空'}), 400

    content = data['content'].strip()
    if len(content) > 1000:
        return jsonify({'error': '评论不能超过1000个字'}), 400

    import random
    adjectives = ['友好的', '热心的', '细心的', '认真的', '开朗的', '温柔的', '幽默的', '坦诚的']
    nouns = ['小伙伴', '观察员', '评论家', '支持者', '同行者', '点赞手', '分享员', '路人甲']
    nickname = f"{random.choice(adjectives)}{random.choice(nouns)}"

    comment = Comment(
        post_id=post_id,
        content=content,
        author_nickname=nickname,
        ip_address=request.remote_addr
    )
    db.session.add(comment)
    post.comments_count += 1
    db.session.commit()

    return jsonify(comment.to_dict()), 201

@app.route('/api/tags/popular', methods=['GET'])
def popular_tags():
    """获取热门标签"""
    posts = Post.query.filter_by(is_active=True).order_by(Post.likes_count.desc()).all()
    tag_count = {}
    for p in posts:
        if p.tags:
            for tag in [t.strip() for t in p.tags.split(',') if t.strip()]:
                tag_count[tag] = tag_count.get(tag, 0) + 1
    sorted_tags = sorted(tag_count.items(), key=lambda x: -x[1])[:20]
    return jsonify([{'name': t, 'count': c} for t, c in sorted_tags])

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取统计数据"""
    total_posts = Post.query.filter_by(is_active=True).count()
    total_comments = Comment.query.filter_by(is_active=True).count()
    total_likes = db.session.query(db.func.sum(Post.likes_count)).scalar() or 0
    return jsonify({
        'total_posts': total_posts,
        'total_comments': total_comments,
        'total_likes': total_likes
    })

# ============ Serve Frontend ============

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    if path.startswith('api/'):
        return jsonify({'error': 'Not found'}), 404
    file_path = os.path.join(app.static_folder, path)
    if os.path.isfile(file_path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)