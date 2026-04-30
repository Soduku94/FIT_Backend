from flask import Flask, request
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
        """Tạo dữ liệu mẫu toàn diện."""
        from app.seeds import seed_all
        seed_all()

    @app.route('/storage/uploads/<path:filename>')
    def serve_storage_file(filename):
        # Kiểm tra nếu có tham số ?download=true thì ép tải về
        as_attachment = request.args.get('download', 'false').lower() == 'true'
        storage_dir = os.path.join(app.root_path, 'storage', 'uploads')
        return send_from_directory(storage_dir, filename, as_attachment=as_attachment)

    @app.route('/uploads/<path:filename>')
    def serve_upload_file(filename):
        # Kiểm tra nếu có tham số ?download=true thì ép tải về
        as_attachment = request.args.get('download', 'false').lower() == 'true'
        upload_dir = os.path.join(os.path.dirname(app.root_path), 'uploads')
        return send_from_directory(upload_dir, filename, as_attachment=as_attachment)

    return app

# chạy lệnh để tạo dự liệu mẫu
#
#
#
# flask seed-db
