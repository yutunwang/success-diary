from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

class Post(db.Model):
    __tablename__ = 'success_posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(500), default='')
    author_nickname = db.Column(db.String(50), nullable=False)
    likes_count = db.Column(db.Integer, default=0)
    views_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    ip_address = db.Column(db.String(45), default='')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    comments = db.relationship('Comment', backref='post', lazy='dynamic',
                               cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content[:300] + ('...' if len(self.content) > 300 else ''),
            'content_full': self.content,
            'tags': self.tags,
            'tags_list': [t.strip() for t in self.tags.split(',') if t.strip()] if self.tags else [],
            'author_nickname': self.author_nickname,
            'likes_count': self.likes_count,
            'views_count': self.views_count,
            'comments_count': self.comments_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('success_posts.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_nickname = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    ip_address = db.Column(db.String(45), default='')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'post_id': self.post_id,
            'content': self.content,
            'author_nickname': self.author_nickname,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }