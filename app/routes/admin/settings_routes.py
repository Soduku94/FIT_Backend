from flask import request, jsonify
from app.models.setting_model import SystemSetting
from app.extensions import db
from app.utils.auth_middleware import admin_required
from . import admin_bp

@admin_bp.route('/settings', methods=['GET'])
@admin_required
def get_settings(current_user):
    try:
        settings = SystemSetting.query.all()
        # Biến đổi danh sách thành key-value pair dễ dùng ở frontend
        result = {s.key: s.value for s in settings}
        return jsonify({
            "message": "Lấy cấu hình hệ thống thành công!",
            "settings": result
        }), 200
    except Exception as e:
        return jsonify({"message": f"Lỗi lấy cấu hình: {str(e)}"}), 500

@admin_bp.route('/settings', methods=['PUT'])
@admin_required
def update_settings(current_user):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "Thiếu dữ liệu cấu hình!"}), 400

        # Kỳ vọng dữ liệu gửi lên dạng: {"STORAGE_PROVIDER": "cloud"}
        updated_keys = []
        for key, value in data.items():
            setting = SystemSetting.query.filter_by(key=key).first()
            if setting:
                # Validate giá trị cho STORAGE_PROVIDER
                if key == 'STORAGE_PROVIDER' and value not in ['local', 'cloud']:
                    return jsonify({"message": "Giá trị của STORAGE_PROVIDER chỉ có thể là 'local' hoặc 'cloud'!"}), 400
                
                setting.value = str(value)
                updated_keys.append(key)
            else:
                # Nếu chưa tồn tại thì tạo mới tự động
                new_setting = SystemSetting(key=key, value=str(value))
                db.session.add(new_setting)
                updated_keys.append(key)

        db.session.commit()
        return jsonify({
            "message": f"Cập nhật cấu hình thành công: {', '.join(updated_keys)}!",
            "settings": data
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Lỗi cập nhật cấu hình: {str(e)}"}), 500
