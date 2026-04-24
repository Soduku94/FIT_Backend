from functools import wraps
from flask import request, jsonify, current_app
from app.models.user_model import User
import jwt


# =====================================
# CHỐT CHẶN DÀNH CHO ADMIN
# =====================================
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1. Thả cửa cho CORS
        if request.method == 'OPTIONS':
            return jsonify({"message": "CORS preflight OK"}), 200

        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'message': 'Thiếu Token! Vui lòng đăng nhập.'}), 401

        token = auth_header.split(" ")[1]

        try:
            # 2. Giải mã Token bằng thư viện PyJWT gốc
            # Lưu ý: Chìa khóa ở đây phải giống hệt chìa khóa lúc tạo Token ở hàm Login
            secret_key = current_app.config.get('SECRET_KEY', 'fit_research_secret_key_123!@#')
            data = jwt.decode(token, secret_key, algorithms=["HS256"])

            # 3. Trích xuất ID (Bắt chuẩn chữ user_id từ hệ thống của bạn)
            user_id = data.get('user_id') or data.get('sub')

            current_user = User.query.get(user_id)

            if not current_user or current_user.role.value != 'admin':
                return jsonify({'message': 'Bạn không có quyền quản trị!'}), 403

        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token đã hết hạn!'}), 401
        except Exception as e:
            print(f"Lỗi giải mã: {str(e)}")
            return jsonify({'message': 'Token không hợp lệ!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated


# =====================================
# CHỐT CHẶN DÀNH CHO BẤT KỲ AI ĐÃ ĐĂNG NHẬP
# =====================================
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == 'OPTIONS':
            return jsonify({"message": "CORS preflight OK"}), 200

        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'message': 'Thiếu Token! Vui lòng đăng nhập.'}), 401

        token = auth_header.split(" ")[1]

        try:
            secret_key = current_app.config.get('SECRET_KEY', 'fit_research_secret_key_123!@#')
            data = jwt.decode(token, secret_key, algorithms=["HS256"])

            user_id = data.get('user_id') or data.get('sub')
            current_user = User.query.get(user_id)

            if not current_user:
                return jsonify({'message': 'Người dùng không tồn tại!'}), 401

        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token đã hết hạn!'}), 401
        except Exception as e:
            return jsonify({'message': 'Token không hợp lệ!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated