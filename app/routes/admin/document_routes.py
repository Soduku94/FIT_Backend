from flask import request, jsonify
from app.models.resource_model import Paper, Dataset, Category
from app.models.user_model import User
from app.extensions import db
from app.utils.auth_middleware import admin_required
from . import admin_bp


# ==========================================
# API 1: LẤY DANH SÁCH TÀI LIỆU (Bao gồm cả Bài báo & Dataset)
# Hỗ trợ lọc theo trạng thái: /api/admin/documents?status=pending
# ==========================================
@admin_bp.route('/documents', methods=['GET', 'OPTIONS'])
@admin_required
def get_all_documents(current_user):
    if request.method == 'OPTIONS':
        return jsonify({"message": "OK"}), 200

    status_filter = request.args.get('status')
    type_filter = request.args.get('type')  # 'paper' hoặc 'dataset'

    documents = []

    # 1. Lấy dữ liệu từ bảng BÀI BÁO
    if not type_filter or type_filter == 'paper':
        q_paper = Paper.query
        if status_filter:
            q_paper = q_paper.filter_by(status=status_filter)
        p_docs = q_paper.all()
        for d in p_docs:
            d.doc_type = 'paper'
        documents.extend(p_docs)

    # 2. Lấy dữ liệu từ bảng DATASET
    if not type_filter or type_filter == 'dataset':
        q_data = Dataset.query
        if status_filter:
            q_data = q_data.filter_by(status=status_filter)
        d_docs = q_data.all()
        for d in d_docs:
            d.doc_type = 'dataset'
        documents.extend(d_docs)

    # 3. Sắp xếp trộn lẫn cả 2 loại: Bài nào nộp sau cùng thì ưu tiên hiển thị lên đầu
    documents.sort(key=lambda x: x.created_at, reverse=True)

    # 4. Đóng gói JSON trả về
    result = []
    for d in documents:
        # Lấy tên Tác giả (Người đăng)
        author_name = "Ẩn danh"
        user = User.query.get(d.uploader_id) if d.uploader_id else None
        if user:
            author_name = user.full_name

        # Lấy tên Chuyên ngành
        category_name = "Chưa phân loại"
        cat = Category.query.get(d.category_id) if getattr(d, 'category_id', None) else None
        if cat:
            category_name = cat.name

        result.append({
            "id": d.id,
            "title": d.title,
            "doc_type": d.doc_type,  # 'paper' hoặc 'dataset'
            "author": author_name,
            "category": category_name,
            "status": d.status,
            "reject_reason": getattr(d, 'reject_reason', None),
            "created_at": d.created_at.strftime("%d/%m/%Y %H:%M") if d.created_at else ""
        })

    return jsonify({
        "message": "Thành công",
        "total": len(result),
        "documents": result
    }), 200


# ==========================================
# API 2: CẬP NHẬT TRẠNG THÁI (DUYỆT / TỪ CHỐI)
# ==========================================
@admin_bp.route('/documents/<string:doc_id>/review', methods=['PUT', 'OPTIONS'])
@admin_required
def review_document(current_user, doc_id):
    if request.method == 'OPTIONS':
        return jsonify({"message": "OK"}), 200

    data = request.get_json()
    new_status = data.get('status')  # 'approved' hoặc 'rejected'
    reject_reason = data.get('reject_reason')  # Lý do từ chối (Chỉ cần khi bị rejected)

    if new_status not in ['approved', 'rejected']:
        return jsonify({"message": "Trạng thái không hợp lệ!"}), 400

    # Nếu Admin bấm từ chối mà quên ghi lý do -> Bắt nhập
    if new_status == 'rejected' and not reject_reason:
        return jsonify({"message": "Vui lòng nhập lý do từ chối để Giảng viên biết đường sửa!"}), 400

    # Kỹ thuật tìm kiếm chéo: Tìm bên Paper trước, nếu không thấy qua Dataset tìm
    doc = Paper.query.get(doc_id)
    if not doc:
        doc = Dataset.query.get(doc_id)

    # Nếu tìm cả 2 bảng không thấy -> Lỗi 404
    if not doc:
        return jsonify({"message": "Không tìm thấy tài liệu!"}), 404

    # Cập nhật trạng thái
    doc.status = new_status
    if new_status == 'rejected':
        doc.reject_reason = reject_reason
    else:
        doc.reject_reason = None  # Nếu duyệt rồi thì xóa lý do từ chối cũ (nếu có) đi

    try:
        db.session.commit()
        return jsonify({
            "message": f"Đã {'duyệt' if new_status == 'approved' else 'từ chối'} tài liệu thành công!",
            "status": doc.status
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"LỖI DUYỆT BÀI: {e}")
        return jsonify({"message": "Lỗi máy chủ khi cập nhật trạng thái!"}), 500