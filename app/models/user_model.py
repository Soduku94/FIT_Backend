import uuid
from datetime import datetime
import enum
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db

class UserRole(enum.Enum):
    STUDENT = "student"
    LECTURER = "lecturer"
    ADMIN = "admin"
    EDITOR = "editor"  # Role mới cho Quản trị nội dung

class User(db.Model):
    """Model đại diện cho người dùng trong hệ thống (User)"""

    __tablename__ = 'users'

    # ========================================
    # 1. THÔNG TIN ĐỊNH DANH CƠ BẢN
    # ========================================
    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )

    user_code = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        index=True,                    # Tăng tốc độ tìm kiếm theo mã SV/GV
        comment="Mã số sinh viên hoặc mã giảng viên"
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False,
        index=True,
        comment="Email dùng để đăng nhập"
    )

    password_hash = db.Column(
        db.String(256),
        nullable=False,
        comment="Mật khẩu đã được băm (không lưu plaintext)"
    )

    # ========================================
    # 2. THÔNG TIN HỒ SƠ CÁ NHÂN
    # ========================================
    full_name = db.Column(
        db.String(100),
        nullable=False,
        index=True,
        comment="Họ và tên đầy đủ"
    )

    avatar_url = db.Column(
        db.String(255),
        nullable=True,
        comment="Đường dẫn ảnh đại diện"
    )

    academic_title = db.Column(
        db.String(50),
        nullable=True,
        comment="Học hàm / Học vị (TS, ThS, PGS, GS...)"
    )

    bio = db.Column(
        db.Text,
        nullable=True,
        comment="Giới thiệu ngắn hoặc hướng nghiên cứu"
    )

    # ========================================
    # 3. PHÂN LOẠI & ĐƠN VỊ
    # ========================================
    role = db.Column(
        db.Enum(UserRole, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=UserRole.STUDENT,
        index=True,
        comment="Vai trò: student, lecturer, admin, editor"
    )

    department = db.Column(
        db.String(100),
        nullable=True,
        index=True,
        comment="Khoa / Bộ môn"
    )

    class_name = db.Column(
        db.String(50),
        nullable=True,
        comment="Lớp sinh hoạt (chỉ áp dụng cho sinh viên)"
    )

    # ========================================
    # 4. BẢO MẬT & QUẢN TRỊ
    # ========================================
    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False,
        comment="Trạng thái tài khoản: True = đang hoạt động"
    )

    is_first_login = db.Column(
        db.Boolean,
        default=True,
        nullable=False,
        comment="Yêu cầu đổi mật khẩu lần đầu tiên đăng nhập"
    )

    last_login_at = db.Column(
        db.DateTime,
        nullable=True,
        comment="Thời điểm đăng nhập lần cuối"
    )

    # ========================================
    # 5. KHÔI PHỤC MẬT KHẨU
    # ========================================
    reset_token = db.Column(
        db.String(100),
        nullable=True,
        comment="Token dùng để reset mật khẩu"
    )

    reset_token_expiry = db.Column(
        db.DateTime,
        nullable=True,
        comment="Thời hạn hết hạn của reset_token"
    )

    # ========================================
    # 6. DẤU VẾT THỜI GIAN
    # ========================================
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Ngày tạo tài khoản"
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Ngày cập nhật thông tin lần cuối"
    )

    # ========================================
    # PHƯƠNG THỨC HỖ TRỢ
    # ========================================
    def set_password(self, password: str) -> None:
        """Băm mật khẩu và lưu vào password_hash"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Kiểm tra mật khẩu người dùng nhập vào"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.user_code} - {self.full_name}>"