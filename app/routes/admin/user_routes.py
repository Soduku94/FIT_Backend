from flask import Blueprint, request, jsonify
from sqlalchemy import or_

from app.models.user_model import User
from app.extensions import db
from app.utils.auth_middleware import admin_required

from . import admin_bp
import openpyxl
from io import BytesIO

# ========================
#   USER MANAGEMENT API
# ========================

# ==================== 1. LẤY DANH SÁCH NGƯỜI DÙNG ====================
@admin_bp.route('/users', methods=['GET', 'OPTIONS'])
@admin_required
def get_all_users(current_user):
    """API lấy danh sách tất cả người dùng (có hỗ trợ lọc và tìm kiếm)"""

    if request.method == 'OPTIONS':
        return jsonify({"message": "OK"}), 200

    print(f"[LOG] Admin {current_user.full_name} đang lấy danh sách người dùng...")

    # Lấy tham số từ query string
    role_filter = request.args.get('role')
    search_keyword = request.args.get('search')

    # Xây dựng query
    query = User.query

    # 1. Lọc theo role (nếu có)
    if role_filter:
        query = query.filter_by(role=role_filter)

    # 2. Tìm kiếm theo từ khóa (full_name, email, user_code)
    if search_keyword:
        search_term = f"%{search_keyword}%"
        query = query.filter(
            or_(
                User.full_name.ilike(search_term),
                User.email.ilike(search_term),
                User.user_code.ilike(search_term)
            )
        )

    # 3. Sắp xếp theo thời gian tạo mới nhất lên đầu
    users = query.order_by(User.created_at.desc()).all()

    # 4. Chuẩn bị dữ liệu trả về
    result = []
    for user in users:
        result.append({
            "id": user.id,
            "user_code": user.user_code,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "department": user.department,
            "class_name": user.class_name,
            "academic_title": getattr(user, 'academic_title', None),  # tránh lỗi nếu chưa có cột
            "is_active": user.is_active,
            "is_first_login": user.is_first_login,
            "last_login_at": user.last_login_at.strftime("%d/%m/%Y %H:%M")
            if user.last_login_at else "Chưa đăng nhập",
            "created_at": user.created_at.strftime("%d/%m/%Y")
            if user.created_at else ""
        })

    return jsonify({
        "total": len(result),
        "users": result
    }), 200


# ==================== 2. TẠO NGƯỜI DÙNG MỚI ====================
@admin_bp.route('/users', methods=['POST', 'OPTIONS'])
@admin_required
def create_user(current_user):
    """API tạo người dùng mới bởi Admin"""
    print(f"[LOG] Admin {current_user.full_name} tạo người dùng mới...")
    if request.method == 'OPTIONS':
        return jsonify({"message": "OK"}), 200

    data = request.get_json() or {}

    # Kiểm tra các trường bắt buộc
    required_fields = ['user_code', 'email', 'full_name', 'role']
    for field in required_fields:
        if not data.get(field):
            return jsonify({"message": f"Thiếu thông tin bắt buộc: {field}"}), 400

    # Kiểm tra trùng lặp
    if User.query.filter_by(user_code=data['user_code']).first():
        return jsonify({"message": "Mã số người dùng này đã tồn tại!"}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({"message": "Email này đã được sử dụng!"}), 400

    # Xử lý dữ liệu theo role
    role = data.get('role')
    class_name = data.get('class_name') if role == 'student' else None
    academic_title = data.get('academic_title') if role in ['lecturer', 'teacher'] else None

    # Tạo user mới
    new_user = User(
        user_code=data['user_code'],
        email=data['email'],
        full_name=data['full_name'],
        role=role,
        department=data.get('department'),
        class_name=class_name,
        academic_title=academic_title,
        bio=data.get('bio'),
        is_active=data.get('is_active', True),
        is_first_login=True
    )

    # Đặt mật khẩu mặc định
    default_password = "fit@123456"
    new_user.set_password(default_password)

    try:
        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            "message": "Tạo người dùng thành công!",
            "default_password": default_password,
            "user_code": new_user.user_code,
            "role": new_user.role
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Lỗi tạo user: {str(e)}")
        return jsonify({"message": "Lỗi máy chủ khi tạo người dùng!"}), 500


# ==================== 3. KHÓA / MỞ KHÓA TÀI KHOẢN (Soft Delete) ====================
@admin_bp.route('/users/<string:user_id>/toggle-status', methods=['PUT', 'OPTIONS'])
@admin_required
def toggle_user_status(current_user, user_id):
    """API khóa hoặc mở khóa tài khoản người dùng"""

    if request.method == 'OPTIONS':
        return jsonify({"message": "OK"}), 200

    try:
        # Ngăn admin tự khóa chính mình
        if current_user.id == user_id:
            return jsonify({
                "message": "Bạn không thể tự khóa tài khoản của chính mình!"
            }), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({"message": "Không tìm thấy người dùng!"}), 404

        # Đảo trạng thái
        user.is_active = not user.is_active
        db.session.commit()

        status_text = "Mở khóa" if user.is_active else "Khóa"

        return jsonify({
            "message": f"Đã {status_text} tài khoản {user.full_name} thành công!",
            "is_active": user.is_active
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Lỗi toggle status: {str(e)}")
        return jsonify({"message": "Lỗi máy chủ khi cập nhật trạng thái!"}), 500


# ==================== 4. CẬP NHẬT THÔNG TIN NGƯỜI DÙNG ====================
@admin_bp.route('/users/<string:user_id>', methods=['PUT', 'OPTIONS'])
@admin_required
def update_user(current_user, user_id):
    """API cập nhật thông tin người dùng"""

    if request.method == 'OPTIONS':
        return jsonify({"message": "OK"}), 200

    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "Không tìm thấy người dùng!"}), 404

    data = request.get_json() or {}

    # Kiểm tra trùng email/user_code (trừ chính user này)
    new_email = data.get('email')
    if new_email and new_email != user.email:
        if User.query.filter_by(email=new_email).first():
            return jsonify({"message": "Email này đã được người khác sử dụng!"}), 400
        user.email = new_email

    new_code = data.get('user_code')
    if new_code and new_code != user.user_code:
        if User.query.filter_by(user_code=new_code).first():
            return jsonify({"message": "Mã số này đã tồn tại!"}), 400
        user.user_code = new_code

    # Cập nhật các trường cơ bản
    user.full_name = data.get('full_name', user.full_name)
    user.department = data.get('department', user.department)
    user.role = data.get('role', user.role)
    user.bio = data.get('bio', user.bio)

    # Cho phép thay đổi trạng thái active
    if 'is_active' in data:
        # Vẫn ngăn không cho tự khóa chính mình
        if data['is_active'] is False and current_user.id == user_id:
            return jsonify({"message": "Bạn không thể tự khóa tài khoản của chính mình!"}), 400
        user.is_active = data['is_active']

    # Xử lý logic theo role
    if user.role == 'student':
        user.class_name = data.get('class_name', user.class_name)
        user.academic_title = None
    elif user.role in ['lecturer', 'teacher']:
        user.academic_title = data.get('academic_title', user.academic_title)
        user.class_name = None

    # Đặt lại mật khẩu (nếu admin truyền password)
    if data.get('password'):
        user.set_password(data.get('password'))

    try:
        db.session.commit()
        return jsonify({
            "message": f"Cập nhật tài khoản {user.full_name} thành công!",
            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Lỗi cập nhật user: {str(e)}")
        return jsonify({"message": "Lỗi máy chủ khi cập nhật dữ liệu!"}), 500


# ==========================================
# API Import người dùng từ file Excel
# ==========================================
@admin_bp.route('/users/import', methods=['POST', 'OPTIONS'])
@admin_required
def import_users_from_excel(current_user):
    if request.method == 'OPTIONS':
        return jsonify({"message": "OK"}), 200

    if 'file' not in request.files:
        return jsonify({"message": "Không tìm thấy file tải lên!"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "Chưa chọn file!"}), 400

    try:
        # 1. Đọc file Excel từ bộ nhớ (không cần lưu file ra ổ cứng)
        wb = openpyxl.load_workbook(BytesIO(file.read()), data_only=True)
        sheet = wb.active

        success_count = 0
        errors = []
        default_password = "fit@123456"

        # 2. Duyệt qua từng dòng (Bắt đầu từ dòng 2 để bỏ qua Tiêu đề)
        # Giả sử cấu trúc cột: A=Mã số, B=Họ Tên, C=Email, D=Vai trò (student/lecturer), E=Khoa, F=Lớp, G=Học hàm
        for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            # Nếu dòng trống (Mã số hoặc Email bị None), bỏ qua
            if not row[0] or not row[2]:
                continue

            user_code = str(row[0]).strip()
            full_name = str(row[1]).strip() if row[1] else "Chưa cập nhật"
            email = str(row[2]).strip()
            role = str(row[3]).strip().lower() if row[3] else "student"
            department = str(row[4]).strip() if row[4] else None
            class_name = str(row[5]).strip() if row[5] and role == 'student' else None
            academic_title = str(row[6]).strip() if row[6] and role == 'lecturer' else None

            # Kiểm tra trùng lặp
            if User.query.filter_by(user_code=user_code).first():
                errors.append(f"Dòng {row_idx}: Mã {user_code} đã tồn tại.")
                continue
            if User.query.filter_by(email=email).first():
                errors.append(f"Dòng {row_idx}: Email {email} đã được sử dụng.")
                continue

            # Tạo user
            new_user = User(
                user_code=user_code,
                email=email,
                full_name=full_name,
                role=role,
                department=department,
                class_name=class_name,
                academic_title=academic_title,
                is_first_login=True
            )
            new_user.set_password(default_password)
            db.session.add(new_user)
            success_count += 1

        # Lưu tất cả vào Database
        db.session.commit()

        return jsonify({
            "message": f"Nhập thành công {success_count} người dùng!",
            "errors": errors # Trả về danh sách lỗi để Admin biết dòng nào bị bỏ qua
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"LỖI ĐỌC EXCEL: {str(e)}")
        return jsonify({"message": "File không đúng định dạng hoặc có lỗi xảy ra!"}), 500
