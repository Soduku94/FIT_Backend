from flask import request, jsonify
from app.models.document_model import Document, Category
from app.extensions import db
from app.utils.auth_middleware import admin_required

# Import Blueprint của admin
from . import admin_bp
from ...models.user_model import User


# ==========================================
# API 1: LẤY DANH SÁCH TÀI LIỆU (CÓ LỌC)
# ==========================================
@admin_bp.route('/documents', methods=['GET'])
@admin_required
def get_all_documents(current_user):
    # Lấy tham số trạng thái từ URL (VD: ?status=pending)
    status_filter = request.args.get('status')

    query = Document.query
    if status_filter:
        query = query.filter_by(status=status_filter)

    # Xếp bài mới nhất lên đầu để Admin duyệt trước
    documents = query.order_by(Document.created_at.desc()).all()

    result = []
    for doc in documents:
        result.append({
            "id": doc.id,
            "title": doc.title,
            "doc_type": "Bài báo khoa học" if doc.doc_type == 'paper' else "Dataset",
            "category_name": doc.category.name if doc.category else "Không có",
            "uploader_id": doc.uploader_id,
            "status": doc.status,
            "created_at": doc.created_at.strftime('%Y-%m-%d %H:%M')
        })

    return jsonify({
        "message": "Lấy danh sách tài liệu thành công",
        "total": len(result),
        "documents": result
    }), 200


# ==========================================
# API 2: PHÊ DUYỆT / TỪ CHỐI TÀI LIỆU
# # ==========================================
# @admin_bp.route('/documents/<string:document_id>/review', methods=['PUT'])
# @admin_required
# def review_document(current_user, document_id):
#     # Tìm tài liệu theo ID
#     doc = Document.query.get(document_id)
#     if not doc:
#         return jsonify({"message": "Không tìm thấy tài liệu!"}), 404
#
#     # Lấy quyết định của Admin từ Body JSON
#     data = request.get_json()
#     new_status = data.get('status')
#
#     if new_status not in ['approved', 'rejected']:
#         return jsonify({"message": "Trạng thái không hợp lệ! Chỉ chấp nhận 'approved' hoặc 'rejected'."}), 400
#
#     # Cập nhật trạng thái
#     doc.status = new_status
#     db.session.commit()
#
#     action = "phê duyệt" if new_status == 'approved' else "từ chối"
#     return jsonify({
#         "message": f"Đã {action} tài liệu thành công!",
#         "document_id": doc.id,
#         "new_status": doc.status
#     }), 200


# ==========================================
# 1. API: LẤY DANH SÁCH BÀI BÁO CHỜ DUYỆT
# ==========================================
@admin_bp.route('/documents/pending', methods=['GET', 'OPTIONS'])
@admin_required
def get_pending_documents(current_user):
    if request.method == 'OPTIONS':
        return jsonify({"message": "CORS preflight OK"}), 200

    # Lấy các bài có status là 'pending' (chờ duyệt)
    docs = Document.query.filter_by(status='pending').order_by(Document.created_at.desc()).all()

    result = []
    for d in docs:
        # Cách 1: Tìm tên tác giả cực kỳ an toàn
        author_name = "Ẩn danh"
        if hasattr(d, 'uploader_id') and d.uploader_id:
            user = User.query.get(d.uploader_id)
            if user:
                author_name = user.full_name

        # Cách 2: Tìm tên chuyên ngành cực kỳ an toàn
        category_name = "Chưa phân loại"
        if hasattr(d, 'category_id') and d.category_id:
            cat = Category.query.get(d.category_id)
            if cat:
                category_name = cat.name

        result.append({
            "id": d.id,
            "title": d.title,
            "author": author_name,
            "category": category_name,
            "created_at": d.created_at.strftime("%d/%m/%Y") if hasattr(d, 'created_at') and d.created_at else "",
        })

    return jsonify({
        "message": "Thành công",
        "documents": result
    }), 200
# ==========================================
# 2. API: CẬP NHẬT TRẠNG THÁI (DUYỆT / TỪ CHỐI)
# ==========================================
@admin_bp.route('/documents/<string:doc_id>/review', methods=['PUT', 'OPTIONS'])
@admin_required
def review_document(current_user, doc_id):
    if request.method == 'OPTIONS':
        return jsonify({"message": "CORS preflight OK"}), 200
    data = request.get_json()
    new_status = data.get('status')  # Sẽ nhận 'approved' hoặc 'rejected' từ React

    if new_status not in ['approved', 'rejected']:
        return jsonify({"message": "Trạng thái không hợp lệ!"}), 400

    doc = Document.query.get(doc_id)
    if not doc:
        return jsonify({"message": "Không tìm thấy tài liệu!"}), 404

    # Cập nhật trạng thái và lưu vào Database
    doc.status = new_status
    db.session.commit()

    return jsonify({"message": f"Đã {'duyệt' if new_status == 'approved' else 'từ chối'} tài liệu thành công!"}), 200