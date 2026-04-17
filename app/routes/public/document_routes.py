from flask import request, jsonify
from app.models.resource_model import Paper, Dataset, Category
from sqlalchemy import or_
from datetime import datetime
# Import Blueprint của public (ta sẽ tạo ở bước 2)
from . import public_bp

from app.extensions import db

# ==========================================
# API: LẤY DANH SÁCH TÀI LIỆU PUBLIC
# ==========================================
@public_bp.route('/documents', methods=['GET'])
def get_public_documents():
    try:
        search_keyword = request.args.get('search')
        category_id = request.args.get('category_id')

        # Query Papers
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

        # Query Datasets
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

        all_docs = []
        categories_dict = {cat.id: cat.name for cat in Category.query.all()}

        for doc in papers:
            all_docs.append({
                "id": doc.id,
                "title": doc.title,
                "doc_type": "Bài báo khoa học",
                "description": doc.description,
                "authors": doc.authors if doc.authors else [],
                "category_name": categories_dict.get(doc.category_id, "Không có"),
                "tags": doc.tags if doc.tags else [],
                "view_count": doc.view_count,
                "created_at": doc.created_at,
                "has_pdf": bool(doc.file_url),
                "has_external_link": bool(doc.doi)
            })

        for doc in datasets:
            all_docs.append({
                "id": doc.id,
                "title": doc.title,
                "doc_type": "Dataset",
                "description": doc.description,
                "authors": doc.authors if doc.authors else [],
                "category_name": categories_dict.get(doc.category_id, "Không có"),
                "tags": doc.tags if doc.tags else [],
                "view_count": doc.view_count,
                "created_at": doc.created_at,
                "has_pdf": bool(doc.file_url),
                "has_external_link": bool(doc.github_url)
            })

        all_docs.sort(key=lambda x: x["created_at"] or datetime.min, reverse=True)

        for doc in all_docs:
            doc["created_at"] = doc["created_at"].strftime('%Y-%m-%d') if doc["created_at"] else ""

        return jsonify({
            "message": "Danh sách tài liệu công khai",
            "total": len(all_docs),
            "documents": all_docs
        }), 200
    except Exception as e:
        print(f"LỖI LẤY DANH SÁCH TÀI LIỆU: {str(e)}")
        return jsonify({"message": "Lỗi máy chủ"}), 500

# ==========================================
# API: XEM CHI TIẾT TÀI LIỆU VÀ TĂNG LƯỢT XEM
# ==========================================
@public_bp.route('/documents/<string:doc_id>', methods=['GET'])
def get_document_detail(doc_id):
    try:
        doc = Paper.query.get(doc_id)
        doc_type_str = "Bài báo khoa học"
        external_link_attr = None
        
        if doc:
            external_link_attr = doc.doi
        else:
            doc = Dataset.query.get(doc_id)
            doc_type_str = "Dataset"
            if doc:
                external_link_attr = doc.github_url

        if not doc or doc.status != 'approved':
            return jsonify({"message": "Tài liệu không tồn tại hoặc chưa được công khai!"}), 404

        increase_view = request.args.get('increase_view')

        if increase_view == 'true':
            if doc.view_count is None:
                doc.view_count = 0
            doc.view_count += 1
            db.session.commit()
            
        category = db.session.get(Category, doc.category_id)

        result = {
            "id": doc.id,
            "title": doc.title,
            "doc_type": doc_type_str,
            "description": doc.description,
            "authors": doc.authors if doc.authors else [],
            "category_name": category.name if category else "Không có",
            "tags": doc.tags if doc.tags else [],
            "view_count": doc.view_count,
            "created_at": doc.created_at.strftime('%d/%m/%Y') if doc.created_at else "",
            "file_url": doc.file_url,
            "external_link": external_link_attr
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