from flask import Blueprint, request, jsonify
from app.models.user_model import User
from app.extensions import db
from app.utils.auth_middleware import admin_required
# ĐÚNG: Import từ file __init__.py


from . import admin_bp
# Tạo Blueprint cho Admin


# 1. API Xem danh sách người dùng (Read)
@admin_bp.route('/users', methods=['GET'])
@admin_required  # Bắt buộc là Admin mới gọi được
def get_all_users(current_user):
    # Lấy thêm tham số lọc theo role nếu có (ví dụ: /api/admin/users?role=student)
    role_filter = request.args.get('role')

    if role_filter:
        users = User.query.filter_by(role=role_filter).all()
    else:
        users = User.query.all()

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
            "is_first_login": user.is_first_login
        })

    return jsonify({"total": len(result), "users": result}), 200


# 2. API Tạo mới người dùng (Create)
@admin_bp.route('/users', methods=['POST'])
@admin_required
def create_user(current_user):
    data = request.get_json()

    # Kiểm tra dữ liệu bắt buộc
    required_fields = ['user_code', 'email', 'full_name', 'role']
    for field in required_fields:
        if not data.get(field):
            return jsonify({"message": f"Thiếu thông tin bắt buộc: {field}"}), 400

    # Kiểm tra xem user_code hoặc email đã tồn tại chưa
    if User.query.filter_by(user_code=data.get('user_code')).first():
        return jsonify({"message": "Mã số này đã tồn tại trong hệ thống!"}), 400
    if User.query.filter_by(email=data.get('email')).first():
        return jsonify({"message": "Email này đã được sử dụng!"}), 400

    # Tạo user mới
    new_user = User(
        user_code=data.get('user_code'),
        email=data.get('email'),
        full_name=data.get('full_name'),
        role=data.get('role'),
        department=data.get('department'),
        class_name=data.get('class_name'),
        is_first_login=True  # Mặc định bắt đổi mật khẩu lần đầu
    )

    # Set mật khẩu mặc định (ví dụ: fit@123456)
    default_password = "fit@123456"
    new_user.set_password(default_password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": "Tạo người dùng thành công!",
        "default_password": default_password,
        "user_code": new_user.user_code
    }), 201


# 3. API Xóa người dùng (Delete)
@admin_bp.route('/users/<string:user_id>', methods=['DELETE'])
@admin_required
def delete_user(current_user, user_id):
    user = User.query.get(user_id)

    if not user:
        return jsonify({"message": "Không tìm thấy người dùng!"}), 404

    # Không cho phép admin tự xóa chính mình
    if user.id == current_user.id:
        return jsonify({"message": "Không thể tự xóa tài khoản của chính mình!"}), 400

    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": f"Đã xóa thành công người dùng {user.user_code}!"}), 200