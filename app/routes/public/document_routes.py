from flask import request, jsonify
from app.models.resource_model import Paper, Dataset, Category
from sqlalchemy import or_
from datetime import datetime
from app.extensions import db

# Giữ nguyên khai báo Blueprint y hệt code cũ của bạn
from . import public_bp

# ==========================================
# API 1: LẤY DANH SÁCH TÀI LIỆU PUBLIC (TRANG CHỦ)
# Đã tích hợp thêm bộ lọc doc_type
# ==========================================
@public_bp.route('/documents', methods=['GET', 'OPTIONS'])
def get_public_documents():
    if request.method == 'OPTIONS':
        return jsonify({"message": "OK"}), 200

    try:
        search_keyword = request.args.get('search', '').strip()
        category_id = request.args.get('category_id')
        doc_type = request.args.get('type', 'all')  # Lấy tham số type từ React (all, paper, dataset)

        all_docs = []
        categories_dict = {cat.id: cat.name for cat in Category.query.all()}

        # --- 1. Lọc bảng Bài báo (Paper) ---
        if doc_type in ['all', 'paper']:
            paper_query = Paper.query.filter_by(status='approved')
            if search_keyword:
                search_term = f"%{search_keyword}%"
                paper_query = paper_query.filter(
                    or_(
                        Paper.title.ilike(search_term),
                        Paper.description.ilike(search_term)
                    )
                )
            if category_id:
                paper_query = paper_query.filter_by(category_id=category_id)

            papers = paper_query.all()
            for doc in papers:
                all_docs.append({
                    "id": doc.id,
                    "title": doc.title,
                    "doc_type": "paper", # Frontend React đang nhận diện bằng chữ 'paper'
                    "description": doc.description,
                    "authors": doc.authors if doc.authors else [],
                    "category_name": categories_dict.get(doc.category_id, "Không có"),
                    "tags": doc.tags if doc.tags else [],
                    "view_count": getattr(doc, 'view_count', 0) or 0,
                    "created_at": doc.created_at,
                    "has_pdf": bool(doc.file_url)
                })

        # --- 2. Lọc bảng Bộ dữ liệu (Dataset) ---
        if doc_type in ['all', 'dataset']:
            dataset_query = Dataset.query.filter_by(status='approved')
            if search_keyword:
                search_term = f"%{search_keyword}%"
                dataset_query = dataset_query.filter(
                    or_(
                        Dataset.title.ilike(search_term),
                        Dataset.description.ilike(search_term)
                    )
                )
            if category_id:
                dataset_query = dataset_query.filter_by(category_id=category_id)

            datasets = dataset_query.all()
            for doc in datasets:
                all_docs.append({
                    "id": doc.id,
                    "title": doc.title,
                    "doc_type": "dataset", # Frontend React đang nhận diện bằng chữ 'dataset'
                    "description": doc.description,
                    "authors": doc.authors if doc.authors else [],
                    "category_name": categories_dict.get(doc.category_id, "Không có"),
                    "tags": doc.tags if doc.tags else [],
                    "view_count": getattr(doc, 'view_count', 0) or 0,
                    "created_at": doc.created_at,
                    "has_pdf": False, # Dataset ko dùng nhãn PDF
                    "has_external_link": bool(getattr(doc, 'github_url', None))
                })

        # Sắp xếp mới nhất lên đầu
        all_docs.sort(key=lambda x: x["created_at"] or datetime.min, reverse=True)

        # Đổi ngày giờ cho đẹp
        for doc in all_docs:
            doc["created_at"] = doc["created_at"].strftime('%d/%m/%Y') if doc["created_at"] else ""

        return jsonify({
            "message": "Danh sách tài liệu công khai",
            "total": len(all_docs),
            "documents": all_docs
        }), 200
    except Exception as e:
        print(f"LỖI LẤY DANH SÁCH TÀI LIỆU: {str(e)}")
        return jsonify({"message": "Lỗi máy chủ"}), 500

# ==========================================
# API 2: XEM CHI TIẾT TÀI LIỆU VÀ TĂNG LƯỢT XEM
# Cập nhật lấy thêm DOI, Github URL, License...
# ==========================================
@public_bp.route('/documents/<string:doc_id>', methods=['GET', 'OPTIONS'])
def get_document_detail(doc_id):
    if request.method == 'OPTIONS':
        return jsonify({"message": "OK"}), 200
    try:
        # 1. Tìm trong bảng Paper
        doc = Paper.query.get(doc_id)
        doc_type_str = "paper"

        # 2. Nếu không thấy, sang bảng Dataset tìm
        if not doc:
            doc = Dataset.query.get(doc_id)
            doc_type_str = "dataset"

        if not doc or doc.status != 'approved':
            return jsonify({"message": "Tài liệu không tồn tại hoặc chưa được công khai!"}), 404

        # Xử lý tăng lượt xem
        increase_view = request.args.get('increase_view')
        if increase_view == 'true':
            if getattr(doc, 'view_count', None) is None:
                doc.view_count = 0
            doc.view_count += 1
            db.session.commit()

        category = db.session.get(Category, doc.category_id)

        # 3. Đóng gói dữ liệu chung
        result = {
            "id": doc.id,
            "title": doc.title,
            "doc_type": doc_type_str,
            "description": doc.description,
            "authors": doc.authors if doc.authors else [],
            "category_name": category.name if category else "Không có",
            "tags": doc.tags if doc.tags else [],
            "view_count": getattr(doc, 'view_count', 0) or 0,
            "created_at": doc.created_at.strftime('%d/%m/%Y') if doc.created_at else "",
            "file_url": doc.file_url,
        }

        # 4. Đóng gói các trường đặc thù cho từng loại để Frontend hiển thị
        if doc_type_str == 'paper':
            result['doi'] = getattr(doc, 'doi', None)
            result['journal_name'] = getattr(doc, 'journal_name', None)
            result['publication_year'] = getattr(doc, 'publication_year', None)
        else:
            result['github_url'] = getattr(doc, 'github_url', None)
            result['file_size'] = getattr(doc, 'file_size', None)
            result['data_format'] = getattr(doc, 'data_format', None)
            result['license_type'] = getattr(doc, 'license_type', None)

        return jsonify({
            "message": "Thành công",
            "document": result
        }), 200

    except Exception as e:
        print(f"LỖI XEM CHI TIẾT: {str(e)}")
        return jsonify({"message": "Lỗi máy chủ"}), 500

# ==========================================
# API 3: LẤY DANH MỤC
# ==========================================
@public_bp.route('/categories', methods=['GET'])
def get_public_categories():
    try:
        categories = Category.query.all()
        result = [{"id": cat.id, "name": cat.name} for cat in categories]
        return jsonify({"categories": result}), 200
    except Exception as e:
        return jsonify({"message": "Lỗi khi lấy danh mục"}), 500