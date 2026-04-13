import uuid
from datetime import datetime
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB

# Bảng trung gian Nhiều-Nhiều giữa Document và Tag (Giữ nguyên)
document_tags = db.Table('document_tags',
                         db.Column('document_id', db.String(36), db.ForeignKey('documents.id'), primary_key=True),
                         db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
                         )


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    documents = db.relationship('Document', backref='category', lazy=True)


class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)


class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(255), nullable=False)

    # Phân loại: 'paper' (Bài báo) hoặc 'dataset' (Dữ liệu/Github)
    doc_type = db.Column(db.String(20), nullable=False, default='paper')

    # Nội dung: Abstract cho bài báo HOẶC mô tả chi tiết cho Dataset
    description = db.Column(db.Text, nullable=False)

    # Danh sách tác giả: JSONB để lưu mảng tên tác giả
    authors = db.Column(JSONB, nullable=False, default=list)

    # File chính (PDF cho bài báo, hoặc file zip cho dataset)
    main_file_url = db.Column(db.String(500), nullable=True)

    # Các file đính kèm phụ (docx, xlsx, pptx...): Lưu mảng JSON các đường dẫn
    # Ví dụ: [{"file_name": "data.xlsx", "url": "/uploads/..."}]
    attachments = db.Column(JSONB, nullable=True, default=list)

    # Link ngoài: Github, Drive, OneDrive...
    external_link = db.Column(db.String(500), nullable=True)

    status = db.Column(db.String(20), nullable=False, default='pending')
    view_count = db.Column(db.Integer, default=0)
    download_count = db.Column(db.Integer, default=0)

    uploader_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)

    tags = db.relationship('Tag', secondary=document_tags, lazy='subquery',
                           backref=db.backref('documents', lazy=True))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)