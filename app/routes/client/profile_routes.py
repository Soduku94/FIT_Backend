from flask import jsonify, request
from app.models.user_model import User
from app.models.resource_model import Paper, Dataset
from app.utils.auth_middleware import token_required
from app.extensions import db

# Quan trọng: Import auth_bp từ routes/auth/__init__.py hoặc file auth gốc của bạn
from app.routes.auth import auth_bp


@auth_bp.route('/profile', methods=['GET', 'OPTIONS'])  # Thêm OPTIONS để tránh lỗi CORS
@token_required
def get_my_profile(current_user):
    # Xử lý Preflight request của trình duyệt
    if request.method == 'OPTIONS':
        return jsonify({"message": "OK"}), 200

    try:
        user_info = {
            "id": current_user.id,
            "user_code": current_user.user_code,
            "full_name": current_user.full_name,
            "email": current_user.email,
            "role": current_user.role.value,
            "department": current_user.department,
            "class_name": current_user.class_name
        }

        my_documents = []
        docs = Paper.query.filter_by(uploader_id=current_user.id).all()
        datasets = Dataset.query.filter_by(uploader_id=current_user.id).all()
        for d in docs + datasets:
            my_documents.append({
                "id": d.id,
                "title": d.title,
                "status": d.status,
                "created_at": d.created_at.strftime("%d/%m/%Y"),
                "view_count": d.view_count or 0
            })

        return jsonify({
            "user": user_info,
            "documents": my_documents
        }), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500