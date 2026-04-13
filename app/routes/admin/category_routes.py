from flask import request, jsonify
from app.models.document_model import Category
from app.extensions import db
from app.utils.auth_middleware import admin_required, token_required


from app.utils.auth_middleware import admin_required

# Import Blueprint của admin
from . import admin_bp


# 1. Lấy danh sách Danh mục (Ai đăng nhập cũng xem được để chọn lúc upload/tìm kiếm)
@admin_bp.route('/categories', methods=['GET'])
@token_required  # Sinh viên, Giảng viên, Admin đều cần xem danh sách này
def get_categories(current_user):
    categories = Category.query.all()
    result = []
    for c in categories:
        result.append({
            "id": c.id,
            "name": c.name,
            "description": c.description
        })
    return jsonify({"categories": result}), 200


# 2. Tạo mới Danh mục (Chỉ Admin)
@admin_bp.route('/categories', methods=['POST'])
@admin_required
def create_category(current_user):
    data = request.get_json()

    if not data or not data.get('name'):
        return jsonify({"message": "Tên danh mục là bắt buộc!"}), 400

    # Kiểm tra xem danh mục đã tồn tại chưa
    if Category.query.filter_by(name=data.get('name')).first():
        return jsonify({"message": "Tên danh mục này đã tồn tại!"}), 400

    new_category = Category(
        name=data.get('name'),
        description=data.get('description', '')
    )

    db.session.add(new_category)
    db.session.commit()

    return jsonify({
        "message": "Tạo danh mục thành công!",
        "category": {
            "id": new_category.id,
            "name": new_category.name
        }
    }), 201


# 3. Sửa Danh mục (Chỉ Admin)
@admin_bp.route('/categories/<int:category_id>', methods=['PUT'])
@admin_required
def update_category(current_user, category_id):
    category = Category.query.get(category_id)
    if not category:
        return jsonify({"message": "Không tìm thấy danh mục!"}), 404

    data = request.get_json()

    if 'name' in data:
        # Kiểm tra xem tên mới có bị trùng với danh mục khác không
        existing = Category.query.filter_by(name=data['name']).first()
        if existing and existing.id != category_id:
            return jsonify({"message": "Tên danh mục này đã được sử dụng!"}), 400
        category.name = data['name']

    if 'description' in data:
        category.description = data['description']

    db.session.commit()
    return jsonify({"message": "Cập nhật danh mục thành công!"}), 200


# 4. Xóa Danh mục (Chỉ Admin)
@admin_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@admin_required
def delete_category(current_user, category_id):
    category = Category.query.get(category_id)
    if not category:
        return jsonify({"message": "Không tìm thấy danh mục!"}), 404

    # Tính năng an toàn: Không cho xóa nếu đang có bài báo nằm trong danh mục này
    if category.documents:
        return jsonify({"message": "Không thể xóa! Đang có tài liệu thuộc danh mục này."}), 400

    db.session.delete(category)
    db.session.commit()
    return jsonify({"message": "Đã xóa danh mục thành công!"}), 200



# ==========================================
# API: LẤY DANH SÁCH DANH MỤC (DÀNH CHO ADMIN)
# ==========================================
@admin_bp.route('/categories', methods=['GET'])
@admin_required
def get_all_categories(current_user):
    # Lấy toàn bộ danh mục từ Database
    categories = Category.query.order_by(Category.name.asc()).all()

    result = []
    for cat in categories:
        result.append({
            "id": cat.id,
            "name": cat.name,
            "description": cat.description
        })

    return jsonify({
        "message": "Lấy danh sách thành công",
        "categories": result
    }), 200