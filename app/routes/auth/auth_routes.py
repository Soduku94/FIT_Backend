from flask import Blueprint, request, jsonify, current_app
import jwt

from app.models.user_model import User
from app.extensions import db
from app.utils.auth_middleware import token_required

import secrets
import datetime


from . import auth_bp


# 1. API Đăng nhập (Sinh JWT)
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or not data.get('user_code') or not data.get('password'):
        return jsonify({"message": "Vui lòng cung cấp mã số và mật khẩu!"}), 400

    user = User.query.filter_by(user_code=data.get('user_code')).first()

    if user and user.check_password(data.get('password')):
        # Tạo JWT Token
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)  # Token sống 24h
        }, current_app.config['SECRET_KEY'], algorithm="HS256")

        return jsonify({
            "message": "Đăng nhập thành công!",
            "token": token,
            "is_first_login": user.is_first_login,  # Frontend sẽ dùng cờ này để bật màn hình Đổi mật khẩu
            "user": {
                "id": user.id,
                "user_code": user.user_code,
                "full_name": user.full_name,
                "role": user.role
            }
        }), 200

    return jsonify({"message": "Mã số hoặc mật khẩu không chính xác!"}), 401


# 2. API Đổi mật khẩu (Bắt buộc cho lần đăng nhập đầu tiên)
@auth_bp.route('/change-first-password', methods=['POST'])
@token_required  # Bắt buộc phải gắn JWT mới gọi được API này
def change_first_password(current_user):
    # Nếu user không phải là đăng nhập lần đầu, từ chối
    if not current_user.is_first_login:
        return jsonify({"message": "Tài khoản của bạn đã được kích hoạt từ trước!"}), 400

    data = request.get_json()
    new_password = data.get('new_password')

    if not new_password or len(new_password) < 6:
        return jsonify({"message": "Mật khẩu mới phải có ít nhất 6 ký tự!"}), 400

    # Cập nhật mật khẩu và tắt cờ first_login
    current_user.set_password(new_password)
    current_user.is_first_login = False

    db.session.commit()

    return jsonify({"message": "Đổi mật khẩu thành công! Tài khoản đã được kích hoạt."}), 200


# 3. API Quên mật khẩu (Gửi Link về Email)
@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    user_code = data.get('user_code')
    email = data.get('email')

    if not user_code or not email:
        return jsonify({"message": "Vui lòng nhập đầy đủ mã số và email!"}), 400

    # Tìm user có khớp cả Mã số và Email không
    user = User.query.filter_by(user_code=user_code, email=email).first()

    if not user:
        # Lưu ý bảo mật: Đôi khi người ta hay trả về "Email đã gửi" kể cả khi sai thông tin để tránh bị dò quét tài khoản.
        # Nhưng ở môi trường nội bộ, báo lỗi rõ ràng sẽ giúp SV/GV dễ thao tác hơn.
        return jsonify({"message": "Thông tin mã số hoặc email không chính xác!"}), 404

    # Sinh một chuỗi token ngẫu nhiên an toàn (64 ký tự)
    reset_token = secrets.token_urlsafe(32)

    # Lưu token vào DB và set hạn sử dụng là 15 phút
    user.reset_token = reset_token
    user.otp_expiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    db.session.commit()

    # TẠO LINK ĐỂ GỬI QUA EMAIL
    # Ở thực tế, localhost:3000 sẽ là domain Frontend ReactJS của bạn
    reset_link = f"http://localhost:3000/reset-password?token={reset_token}"

    # [TODO]: Tích hợp hệ thống gửi email thật (như Flask-Mail, SendGrid, Amazon SES)
    # Tạm thời chúng ta sẽ in ra Terminal để test Backend:
    print(f"\n[SYSTEM EMAIL MOCK]")
    print(f"To: {email}")
    print(f"Subject: Khôi phục mật khẩu FIT Research Hub")
    print(f"Vui lòng click vào link sau để đổi mật khẩu (có hiệu lực trong 15 phút):")
    print(f"{reset_link}\n")

    return jsonify(
        {"message": "Link khôi phục mật khẩu đã được gửi vào email của bạn. Vui lòng kiểm tra hộp thư!"}), 200


# 4. API Đặt lại mật khẩu mới (Khi user click vào Link trong Email)
@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('new_password')

    if not token or not new_password or len(new_password) < 6:
        return jsonify({"message": "Dữ liệu không hợp lệ hoặc mật khẩu quá ngắn!"}), 400

    # Tìm user sở hữu token này
    user = User.query.filter_by(reset_token=token).first()

    # Kiểm tra xem token có tồn tại và còn hạn không
    if not user or not user.otp_expiry or user.otp_expiry < datetime.datetime.utcnow():
        return jsonify({"message": "Link khôi phục không hợp lệ hoặc đã hết hạn!"}), 400

    # Cập nhật mật khẩu mới
    user.set_password(new_password)

    # Xóa token đi để link này không thể dùng lại được nữa
    user.reset_token = None
    user.otp_expiry = None

    db.session.commit()

    return jsonify({"message": "Đặt lại mật khẩu thành công! Bạn có thể đăng nhập bằng mật khẩu mới."}), 200