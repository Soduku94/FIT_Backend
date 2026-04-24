from flask import Flask
from config import Config
from app.extensions import db, migrate,mail
from flask_cors import CORS
from flask import Flask, send_from_directory
import os

def create_app(config_class=Config):
    app = Flask(__name__)
    CORS(app)
    # Chỉ cần gọi from_object 1 lần là đủ
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    # ==========================================
    # IMPORT MODEL
    # ==========================================
    from app.models import user_model
    from app.models import resource_model
    from app.routes.client import profile_routes

    # ==========================================
    # IMPORT VÀ ĐĂNG KÝ CÁC BLUEPRINT (API ROUTES)
    # ==========================================
    from app.routes.auth import auth_bp
    from app.routes.client import upload_routes
    app.register_blueprint(auth_bp)

    from app.routes.admin import admin_bp
    app.register_blueprint(admin_bp)

    # ĐÃ SỬA: Lấy chuẩn từ thư mục public của bạn
    from app.routes.public import public_bp
    app.register_blueprint(public_bp)

    from app.routes.teacher.document_routes import teacher_bp
    app.register_blueprint(teacher_bp)

    # ĐÃ SỬA: Gom gọn lại chỉ 1 lần import cho student
    from app.routes.student import student_bp
    app.register_blueprint(student_bp)

    from app.routes.client import profile_routes

    from app.routes.editor.news_routes import editor_bp
    app.register_blueprint(editor_bp)


    # ==========================================
    # LỆNH TẠO DỮ LIỆU MẪU (CLI)
    # ==========================================
    @app.cli.command("seed-db")
    def seed_db():
        """Tạo dữ liệu mẫu."""
        print("Đang khởi tạo dữ liệu mẫu...")

        # 1. Tạo tài khoản Admin
        admin = user_model.User.query.filter_by(user_code='admin_fit').first()
        if not admin:
            admin = user_model.User(
                user_code='admin_fit',
                email='admin@fit.edu.vn',
                full_name='Quản trị viên FIT',
                role=user_model.UserRole.ADMIN,
                department='Văn phòng Khoa'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print("- Đã tạo Admin: admin_fit / admin123")

        # 2. Tạo tài khoản Giảng viên (Lecturer)
        teacher = user_model.User.query.filter_by(user_code='GV001').first()
        if not teacher:
            teacher = user_model.User(
                user_code='GV001',
                email='gv001@fit.edu.vn',
                full_name='TS. Nguyễn Văn A',
                role=user_model.UserRole.LECTURER,
                department='Bộ môn Hệ thống thông tin'
            )
            teacher.set_password('teacher123')
            db.session.add(teacher)
            print("- Đã tạo Teacher (Lecturer): GV001 / teacher123")

        # 3. Tạo tài khoản Sinh viên (Student)
        student = user_model.User.query.filter_by(user_code='20240001').first()
        if not student:
            student = user_model.User(
                user_code='20240001',
                email='sv20240001@student.edu.vn',
                full_name='Trần Thị Sinh Viên',
                role=user_model.UserRole.STUDENT,
                department='Khoa CNTT',
                class_name='K65-CNTT'
            )
            student.set_password('student123')
            db.session.add(student)
            print("- Đã tạo Student: 20240001 / student123")

        # 4. Tạo tài khoản Biên tập viên (Editor)
        editor = user_model.User.query.filter_by(user_code='ED001').first()
        if not editor:
            editor = user_model.User(
                user_code='ED001',
                email='editor001@fit.edu.vn',
                full_name='Biên tập viên Nội dung',
                role=user_model.UserRole.EDITOR,
                department='Ban Truyền thông'
            )
            editor.set_password('editor123')
            db.session.add(editor)
            print("- Đã tạo Editor: ED001 / editor123")

        db.session.commit()
        print("Hoàn thành khởi tạo dữ liệu!")

    @app.route('/uploads/<path:filename>')
    def serve_upload_file(filename):
        # Trỏ chính xác ra thư mục 'uploads' nằm ngoài cùng project (ngang hàng với app và run.py)
        upload_dir = os.path.join(os.path.dirname(app.root_path), 'uploads')
        return send_from_directory(upload_dir, filename)

    return app

# chạy lệnh để tạo dự liệu mẫu
#
#
#
# flask seed-db
