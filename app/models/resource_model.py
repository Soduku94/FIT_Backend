from datetime import datetime
import uuid
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
# ==========================================
# 1. BẢNG BÀI BÁO KHOA HỌC (PAPERS)
# ==========================================
class Paper(db.Model):
    __tablename__ = 'papers'

    # --- Thông tin chung ---
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)  # Tóm tắt (Abstract)
    authors = db.Column(JSONB, nullable=False)  # Mảng tác giả: ["Nguyễn Văn A", "Trần B"]
    tags = db.Column(JSONB, nullable=True)  # MỚI: Từ khóa ["AI", "NLP"]
    thumbnail_url = db.Column(db.String(255), nullable=True)  # MỚI: Ảnh bìa (nếu có)

    # --- Đặc thù Bài Báo ---
    publication_year = db.Column(db.Integer, nullable=True)  # Năm xuất bản
    journal_name = db.Column(db.String(255), nullable=True)  # Tên tạp chí / Hội nghị
    doi = db.Column(db.String(100), nullable=True)  # Mã định danh tài liệu số (DOI)

    # --- File & Trạng thái ---
    file_url = db.Column(db.String(255), nullable=False)  # Link tải PDF
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    reject_reason = db.Column(db.Text, nullable=True)  # MỚI: Lý do từ chối (dành cho Admin)

    # --- Thống kê ---
    view_count = db.Column(db.Integer, default=0)
    download_count = db.Column(db.Integer, default=0)

    # --- Khóa ngoại ---
    uploader_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ==========================================
# 2. BẢNG BỘ DỮ LIỆU (DATASETS)
# ==========================================
class Dataset(db.Model):
    __tablename__ = 'datasets'

    # --- Thông tin chung ---
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)  # Mô tả bộ dữ liệu
    authors = db.Column(JSONB, nullable=False)  # Mảng người đóng tạo/sưu tầm
    tags = db.Column(JSONB, nullable=True)  # MỚI: Từ khóa ["Images", "Medical"]
    thumbnail_url = db.Column(db.String(255), nullable=True)

    # --- Đặc thù Dataset ---
    file_size = db.Column(db.String(50), nullable=True)  # VD: "1.5 GB", "500 MB"
    data_format = db.Column(db.String(100), nullable=True)  # VD: "CSV, JSON, JPG"
    license_type = db.Column(db.String(100), nullable=True)  # VD: "MIT", "Open Source", "Nội bộ"
    github_url = db.Column(db.String(255), nullable=True)  # MỚI: Rất cần cho Dataset có code đi kèm

    # --- File & Trạng thái ---
    file_url = db.Column(db.String(255), nullable=True)  # Link tải file ZIP (Có thể Null nếu dùng Github)
    status = db.Column(db.String(20), default='pending')
    reject_reason = db.Column(db.Text, nullable=True)

    # --- Thống kê ---
    view_count = db.Column(db.Integer, default=0)
    download_count = db.Column(db.Integer, default=0)

    # --- Khóa ngoại ---
    uploader_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)