import uuid
from datetime import datetime
from app.extensions import db
import enum


class NewsStatus(enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class News(db.Model):
    __tablename__ = 'news'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)  # Đường dẫn bài viết
    thumbnail_url = db.Column(db.String(255), nullable=True)  # Ảnh bìa bài viết

    # Nội dung bài viết (Lưu mã HTML từ Rich Text Editor)
    content = db.Column(db.Text, nullable=False)

    category = db.Column(db.String(50), index=True)  # Ví dụ: 'Sự kiện', 'Giải thưởng', 'Đồ án xuất sắc'

    status = db.Column(db.Enum(NewsStatus, values_callable=lambda x: [e.value for e in x]), default=NewsStatus.DRAFT)

    author_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Quan hệ với người viết
    author = db.relationship('User', backref='articles')