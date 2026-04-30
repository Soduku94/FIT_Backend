from flask import request, jsonify
import os
from app.models.resource_model import Paper, Dataset, Category
from sqlalchemy import or_
from datetime import datetime
from app.extensions import db
from app.services.ai_service import generate_document_summary

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
        # --- 1. Lấy các tham số lọc từ URL ---
        search_keyword = request.args.get('search', '').strip()
        category_id = request.args.get('category_id')
        doc_type = request.args.get('type', 'all')  # all, paper, dataset
        year = request.args.get('year')             # Lọc theo năm xuất bản (chỉ cho paper)
        sort_by = request.args.get('sort_by', 'newest') # newest, oldest, view
        
        # Tham số phân trang
        try:
            page = int(request.args.get('page', 1))
            limit = int(request.args.get('limit', 12))
        except ValueError:
            page = 1
            limit = 12

        all_docs = []
        categories_dict = {cat.id: cat.name for cat in Category.query.all()}

        # --- 2. Lọc bảng Bài báo (Paper) ---
        if doc_type in ['all', 'paper']:
            paper_query = Paper.query.filter_by(status='approved')
            
            if search_keyword:
                search_term = f"%{search_keyword}%"
                paper_query = paper_query.filter(
                    or_(
                        Paper.title.ilike(search_term),
                        Paper.description.ilike(search_term),
                        Paper.journal_name.ilike(search_term)
                    )
                )
            
            if category_id:
                paper_query = paper_query.filter_by(category_id=category_id)
            
            if year:
                paper_query = paper_query.filter_by(publication_year=year)

            papers = paper_query.all()
            for doc in papers:
                all_docs.append({
                    "id": doc.id,
                    "title": doc.title,
                    "doc_type": "paper",
                    "description": doc.description,
                    "authors": doc.authors if doc.authors else [],
                    "category_name": categories_dict.get(doc.category_id, "Không có"),
                    "tags": doc.tags if doc.tags else [],
                    "view_count": getattr(doc, 'view_count', 0) or 0,
                    "created_at": doc.created_at,
                    "publication_year": getattr(doc, 'publication_year', None),
                    "has_pdf": bool(doc.file_url)
                })

        # --- 3. Lọc bảng Bộ dữ liệu (Dataset) ---
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
            
            # Dataset thường không có publication_year rõ ràng như Paper, 
            # nhưng nếu user chọn năm, ta có thể lọc theo năm của created_at nếu cần.
            # Hiện tại tạm để Year chỉ áp dụng cho Paper.

            datasets = dataset_query.all()
            for doc in datasets:
                all_docs.append({
                    "id": doc.id,
                    "title": doc.title,
                    "doc_type": "dataset",
                    "description": doc.description,
                    "authors": doc.authors if doc.authors else [],
                    "category_name": categories_dict.get(doc.category_id, "Không có"),
                    "tags": doc.tags if doc.tags else [],
                    "view_count": getattr(doc, 'view_count', 0) or 0,
                    "created_at": doc.created_at,
                    "has_pdf": False,
                    "has_external_link": bool(getattr(doc, 'github_url', None))
                })

        # --- 4. Sắp xếp kết quả ---
        if sort_by == 'oldest':
            all_docs.sort(key=lambda x: x["created_at"] or datetime.min)
        elif sort_by == 'view':
            all_docs.sort(key=lambda x: x["view_count"], reverse=True)
        else: # newest (mặc định)
            all_docs.sort(key=lambda x: x["created_at"] or datetime.min, reverse=True)

        # --- 5. Phân trang ---
        total_items = len(all_docs)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_docs = all_docs[start_idx:end_idx]

        # Định dạng lại ngày tháng để trả về
        for doc in paginated_docs:
            if isinstance(doc["created_at"], datetime):
                doc["created_at"] = doc["created_at"].strftime('%d/%m/%Y')

        return jsonify({
            "message": "Thành công",
            "metadata": {
                "total": total_items,
                "page": page,
                "limit": limit,
                "total_pages": (total_items + limit - 1) // limit
            },
            "documents": paginated_docs
        }), 200

    except Exception as e:
        print(f"LỖI LẤY DANH SÁCH TÀI LIỆU: {str(e)}")
        return jsonify({"message": f"Lỗi máy chủ: {str(e)}"}), 500

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
            result['citation'] = getattr(doc, 'citation', None)
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

# ==========================================
# API 4: AI TÓM TẮT TÀI LIỆU
# ==========================================
@public_bp.route('/documents/<id>/summary', methods=['GET', 'OPTIONS'])
def get_document_ai_summary(id):
    if request.method == 'OPTIONS':
        return jsonify({"message": "OK"}), 200
    
    try:
        doc = Paper.query.get(id)
        if not doc:
            doc = Dataset.query.get(id)
            
        if not doc:
            return jsonify({"message": "Không tìm thấy tài liệu"}), 404
            
        # --- BƯỚC 1: KIỂM TRA CACHE TRONG DATABASE ---
        if doc.ai_summary:
            print(f"--- ĐÃ TÌM THẤY TÓM TẮT TRONG CACHE (DB) CHO ID: {id} ---")
            return jsonify({
                "message": "Tóm tắt từ Cache",
                "summary": doc.ai_summary
            }), 200

        # --- BƯỚC 2: XỬ LÝ FILE PDF NẾU CHƯA CÓ CACHE ---
        abs_file_path = None
        if doc.file_url:
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
            relative_path = doc.file_url.lstrip('/')
            abs_file_path = os.path.join(root_dir, 'app', relative_path)
            abs_file_path = os.path.normpath(abs_file_path)
            
            if not os.path.exists(abs_file_path):
                print(f"--- KHÔNG TÌM THẤY FILE TẠI: {abs_file_path} ---")
                abs_file_path = None
            else:
                print(f"--- ĐÃ TÌM THẤY FILE PDF: {abs_file_path} ---")

        # --- BƯỚC 3: GỌI SERVICE AI ---
        summary_data = generate_document_summary(doc.title, doc.description, abs_file_path)
        
        # Nếu AI trả về kết quả hợp lệ (không phải lỗi), thì lưu vào Database
        if summary_data and "objective" in summary_data and "Lỗi" not in str(summary_data.get("objective")):
            try:
                doc.ai_summary = summary_data
                db.session.commit()
                print(f"--- ĐÃ LƯU TÓM TẮT MỚI VÀO DATABASE CHO ID: {id} ---")
            except Exception as db_err:
                db.session.rollback()
                print(f"LỖI LƯU CACHE AI: {str(db_err)}")

        return jsonify({
            "message": "Tóm tắt thành công",
            "summary": summary_data
        }), 200
        
    except Exception as e:
        print(f"LỖI AI SUMMARY: {str(e)}")
        return jsonify({"message": "Lỗi khi xử lý AI"}), 500