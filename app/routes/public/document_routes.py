from flask import request, jsonify
from app.models.document_model import Document
from sqlalchemy import or_
from app.models.document_model import Category
# Import Blueprint của public (ta sẽ tạo ở bước 2)
from . import public_bp

from app.extensions import db

# ==========================================
# API: LẤY DANH SÁCH TÀI LIỆU PUBLIC
# ==========================================
@public_bp.route('/documents', methods=['GET'])
def get_public_documents():
    # 1. Luôn luôn khóa chặt điều kiện: Chỉ lấy bài đã được duyệt
    query = Document.query.filter_by(status='approved')

    # 2. Xử lý tính năng Tìm kiếm (Search) nếu có
    search_keyword = request.args.get('search')
    if search_keyword:
        # Tìm kiếm tương đối (LIKE) trong Tiêu đề HOẶC Tóm tắt
        search_term = f"%{search_keyword}%"
        query = query.filter(
            or_(
                Document.title.ilike(search_term),
                Document.description.ilike(search_term)
            )
        )

    # Lọc theo danh mục (nếu user click vào một chuyên ngành)
    category_id = request.args.get('category_id')
    if category_id:
        query = query.filter_by(category_id=category_id)

    # 3. Thực thi query, xếp bài mới nhất lên đầu
    documents = query.order_by(Document.created_at.desc()).all()

    # 4. Format dữ liệu trả về (TUYỆT ĐỐI BẢO MẬT LINK FILE)
    result = []
    for doc in documents:
        result.append({
            "id": doc.id,
            "title": doc.title,
            "doc_type": "Bài báo khoa học" if doc.doc_type == 'paper' else "Dataset",
            "description": doc.description, # Chỉ cho xem tóm tắt
            "authors": doc.authors,
            "category_name": doc.category.name if doc.category else "Không có",
            "tags": [tag.name for tag in doc.tags],
            "view_count": doc.view_count,
            "created_at": doc.created_at.strftime('%Y-%m-%d'),
            # Trả về cờ hiệu để Frontend biết mà vẽ nút "Tải PDF" hay "Link ngoài"
            "has_pdf": bool(doc.main_file_url),
            "has_external_link": bool(doc.external_link)
            # LƯU Ý: Không có main_file_url hay attachments ở đây!
        })

    return jsonify({
        "message": "Danh sách tài liệu công khai",
        "total": len(result),
        "documents": result
    }), 200


# ==========================================
# API: XEM CHI TIẾT TÀI LIỆU VÀ TĂNG LƯỢT XEM
# ==========================================
@public_bp.route('/documents/<string:doc_id>', methods=['GET'])
def get_document_detail(doc_id):
    try:
        # Tìm bài báo theo ID
        doc = Document.query.get(doc_id)

        # Nếu không thấy, hoặc bài đó chưa được Admin duyệt thì báo lỗi 404
        if not doc or doc.status != 'approved':
            return jsonify({"message": "Tài liệu không tồn tại hoặc chưa được công khai!"}), 404

        # TĂNG LƯỢT XEM LÊN 1
        increase_view = request.args.get('increase_view')

        if increase_view == 'true':
            if doc.view_count is None:
                doc.view_count = 0
            doc.view_count += 1
            db.session.commit()

        # Format dữ liệu trả về (Lấy chuẩn theo model của bạn)
        result = {
            "id": doc.id,
            "title": doc.title,
            "doc_type": "Bài báo khoa học" if doc.doc_type == 'paper' else "Dataset",
            "description": doc.description,
            "authors": doc.authors,
            "category_name": doc.category.name if doc.category else "Không có",
            "tags": [tag.name for tag in doc.tags],
            "view_count": doc.view_count,
            "created_at": doc.created_at.strftime('%d/%m/%Y') if doc.created_at else "",
            "file_url": doc.main_file_url,
            "external_link": doc.external_link
        }

        return jsonify({
            "message": "Thành công",
            "document": result
        }), 200

    except Exception as e:
        print(f"LỖI XEM CHI TIẾT: {str(e)}")
        return jsonify({"message": "Lỗi máy chủ"}), 500

@public_bp.route('/categories', methods=['GET'])
def get_public_categories():
        try:
            categories = Category.query.all()
            result = [{"id": cat.id, "name": cat.name} for cat in categories]
            return jsonify({"categories": result}), 200
        except Exception as e:
            return jsonify({"message": "Lỗi khi lấy danh mục"}), 500