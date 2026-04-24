from flask import Blueprint, request, jsonify, current_app
import jwt

from app.models.user_model import User
from app.extensions import db
from app.utils.auth_middleware import token_required

import secrets
import datetime

from flask_mail import Mail, Message
from . import auth_bp

from flask_mail import Message
from app.extensions import mail
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
                "role": user.role.value
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


# 3. API Quên mật khẩu (Gửi Link về Email thực tế)
@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    user_code = data.get('user_code')
    email = data.get('email')

    if not user_code or not email:
        return jsonify({"message": "Vui lòng nhập đầy đủ mã số và email!"}), 400

    user = User.query.filter_by(user_code=user_code, email=email).first()

    if not user:
        return jsonify({"message": "Thông tin mã số hoặc email không chính xác!"}), 404

    reset_token = secrets.token_urlsafe(32)

    user.reset_token = reset_token
    # ĐÃ SỬA: Dùng reset_token_expiry thay vì otp_expiry
    user.reset_token_expiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    db.session.commit()

    reset_link = f"http://localhost:5173/reset-password?token={reset_token}"

    try:
        msg = Message(
            subject="[FIT Research] Khôi phục mật khẩu tài khoản",
            recipients=[email],
            html=f"""
                <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: auto; border: 1px solid #e0e0e0; border-radius: 10px; padding: 20px;">
                    <h2 style="color: #2c3e50; text-align: center;">Khôi phục mật khẩu</h2>
                    <hr style="border: 0; border-top: 1px solid #eee;">
                    <p>Xin chào <strong>{user.full_name}</strong>,</p>
                    <p>Chúng tôi đã nhận được yêu cầu khôi phục mật khẩu cho tài khoản có mã nhân viên: <span style="background: #f4f4f4; padding: 2px 5px; border-radius: 3px; font-family: monospace;">{user.user_code}</span>.</p>
                    <p>Để thiết lập mật khẩu mới, vui lòng nhấn vào nút xác nhận bên dưới:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_link}" style="background-color: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">Đổi mật khẩu ngay</a>
                    </div>
                    <p style="color: #e74c3c; font-size: 0.9em;"><strong>Lưu ý:</strong> Liên kết này sẽ hết hạn sau 15 phút vì lý do bảo mật.</p>
                    <hr style="border: 0; border-top: 1px solid #eee;">
                    <p style="font-size: 0.8em; color: #7f8c8d;">Nếu bạn không thực hiện yêu cầu này, hãy yên tâm bỏ qua email này. Tài khoản của bạn vẫn được bảo mật.</p>
                    <p style="margin-top: 20px;">Trân trọng,<br>
                    <strong>Đội ngũ FIT Research Hub</strong></p>
                </div>
                """
        )
        mail.send(msg)
        return jsonify({"message": "Link khôi phục mật khẩu đã được gửi. Vui lòng kiểm tra hộp thư của bạn!"}), 200

    except Exception as e:
        print(f"LỖI GỬI MAIL: {str(e)}")
        user.reset_token = None
        # ĐÃ SỬA: Dùng reset_token_expiry
        user.reset_token_expiry = None
        db.session.commit()
        return jsonify({"message": "Có lỗi từ máy chủ Email. Vui lòng thử lại sau!"}), 500

# 4. API Đặt lại mật khẩu mới (Khi user click vào Link trong Email)
@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('new_password')

    if not token or not new_password or len(new_password) < 6:
        return jsonify({"message": "Dữ liệu không hợp lệ hoặc mật khẩu quá ngắn!"}), 400

    user = User.query.filter_by(reset_token=token).first()

    # ĐÃ SỬA: Dùng reset_token_expiry thay vì otp_expiry
    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.datetime.utcnow():
        return jsonify({"message": "Link khôi phục không hợp lệ hoặc đã hết hạn!"}), 400

    user.set_password(new_password)

    user.reset_token = None
    # ĐÃ SỬA: Dùng reset_token_expiry
    user.reset_token_expiry = None

    db.session.commit()

    return jsonify({"message": "Đặt lại mật khẩu thành công! Bạn có thể đăng nhập bằng mật khẩu mới."}), 200

# 5. API Đổi mật khẩu (Dành cho user đang đăng nhập trong trang Profile)
@auth_bp.route('/change-password', methods=['PUT', 'OPTIONS'])
@token_required
def change_password(current_user):
    if request.method == 'OPTIONS':
        return jsonify({"message": "OK"}), 200

    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    if not old_password or not new_password:
        return jsonify({"message": "Vui lòng nhập đầy đủ mật khẩu cũ và mật khẩu mới!"}), 400

    # 1. Kiểm tra mật khẩu cũ có đúng không
    if not current_user.check_password(old_password):
        return jsonify({"message": "Mật khẩu cũ không chính xác!"}), 400

    # 2. Kiểm tra độ dài mật khẩu mới
    if len(new_password) < 6:
        return jsonify({"message": "Mật khẩu mới phải có ít nhất 6 ký tự!"}), 400

    # 3. Chống đổi mật khẩu mới trùng mật khẩu cũ (UX tốt)
    if old_password == new_password:
        return jsonify({"message": "Mật khẩu mới không được trùng với mật khẩu cũ!"}), 400

    # 4. Cập nhật và lưu DB
    current_user.set_password(new_password)
    db.session.commit()

    return jsonify({"message": "Đổi mật khẩu thành công!"}), 200