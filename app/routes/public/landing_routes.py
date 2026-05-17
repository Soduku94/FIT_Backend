from flask import request, jsonify

from app.models.news_model import News, NewsStatus

from . import public_bp
# ==========================================
# API: LẤY DANH SÁCH TIN TỨC / SỰ KIỆN (PUBLIC)
# ==========================================
@public_bp.route('/news', methods=['GET', 'OPTIONS'])
def get_public_news():
    if request.method == 'OPTIONS':
        return jsonify({"message": "OK"}), 200

    try:
        category = request.args.get('category')  # Tùy chọn lọc theo danh mục

        # Chỉ lấy những bài viết đã được Publish (Xuất bản)
        query = News.query.filter_by(status=NewsStatus.PUBLISHED)

        if category:
            query = query.filter_by(category=category)

        # Sắp xếp mới nhất lên đầu
        news_list = query.order_by(News.created_at.desc()).all()

        result = []
        for item in news_list:
            result.append({
                "id": item.id,
                "title": item.title,
                "slug": item.slug,
                "thumbnail_url": item.thumbnail_url,
                "category": item.category,
                # Trả về 1 đoạn tóm tắt ngắn thay vì toàn bộ mã HTML để load nhanh hơn
                "excerpt": item.content[:150] + "..." if len(item.content) > 150 else item.content,
                "created_at": item.created_at.strftime('%d/%m/%Y') if item.created_at else "",
                "author_name": item.author.full_name if item.author else "Ban Quản Trị"
            })

        return jsonify({
            "message": "Danh sách tin tức",
            "news": result
        }), 200

    except Exception as e:
        print(f"LỖI LẤY TIN TỨC: {str(e)}")
        return jsonify({"message": "Lỗi máy chủ"}), 500

# ==========================================
# API: CHI TIẾT TIN TỨC / SỰ KIỆN (PUBLIC)
# ==========================================
@public_bp.route('/news/<id>', methods=['GET', 'OPTIONS'])
def get_public_news_detail(id):
    if request.method == 'OPTIONS':
        return jsonify({"message": "OK"}), 200

    try:
        news_item = News.query.filter_by(id=id, status=NewsStatus.PUBLISHED).first()
        if not news_item:
            return jsonify({"message": "Không tìm thấy bài viết"}), 404

        result = {
            "id": news_item.id,
            "title": news_item.title,
            "content": news_item.content,
            "category": news_item.category,
            "thumbnail_url": news_item.thumbnail_url,
            "created_at": news_item.created_at.strftime('%d/%m/%Y') if news_item.created_at else "",
            "author_name": news_item.author.full_name if news_item.author else "Ban Quản Trị",
        }

        return jsonify({"message": "Chi tiết bài viết", "news": result}), 200

    except Exception as e:
        print(f"LỖI LẤY CHI TIẾT TIN TỨC: {str(e)}")
        return jsonify({"message": "Lỗi máy chủ"}), 500

# ==========================================
# API: LẤY DANH SÁCH GIẢNG VIÊN (PUBLIC)
# ==========================================
@public_bp.route('/lecturers', methods=['GET', 'OPTIONS'])
def get_public_lecturers():
    if request.method == 'OPTIONS':
        return jsonify({"message": "OK"}), 200

    try:
        from app.models.user_model import User, UserRole

        # Lấy tất cả giảng viên đang hoạt động
        lecturers = User.query.filter_by(role=UserRole.LECTURER, is_active=True).all()

        result = []
        for lecturer in lecturers:
            result.append({
                "id": lecturer.id,
                "user_code": lecturer.user_code,
                "email": lecturer.email,
                "full_name": lecturer.full_name,
                "avatar_url": lecturer.avatar_url,
                "academic_title": lecturer.academic_title,
                "bio": lecturer.bio,
                "department": lecturer.department
            })

        return jsonify({
            "message": "Danh sách giảng viên",
            "lecturers": result
        }), 200

    except Exception as e:
        print(f"LỖI LẤY DANH SÁCH GIẢNG VIÊN: {str(e)}")
        return jsonify({"message": "Lỗi máy chủ"}), 500

# ==========================================
# API: CHI TIẾT GIẢNG VIÊN VÀ TÀI LIỆU CỦA HỌ (PUBLIC)
# ==========================================
@public_bp.route('/lecturers/<id>', methods=['GET', 'OPTIONS'])
def get_public_lecturer_detail(id):
    if request.method == 'OPTIONS':
        return jsonify({"message": "OK"}), 200

    try:
        from app.models.user_model import User, UserRole
        from app.models.resource_model import Paper, Dataset, Category

        lecturer = User.query.filter_by(id=id, role=UserRole.LECTURER, is_active=True).first()
        if not lecturer:
            return jsonify({"message": "Không tìm thấy giảng viên hoặc tài khoản đã bị khóa"}), 404

        # Lấy danh sách các tài liệu đã được duyệt của giảng viên này
        categories_dict = {cat.id: cat.name for cat in Category.query.all()}
        
        # 1. Lấy Papers
        papers = Paper.query.filter_by(uploader_id=lecturer.id, status='approved').order_by(Paper.created_at.desc()).all()
        paper_list = []
        for doc in papers:
            paper_list.append({
                "id": doc.id,
                "title": doc.title,
                "doc_type": "paper",
                "description": doc.description,
                "authors": doc.authors if doc.authors else [],
                "category_name": categories_dict.get(doc.category_id, "Không có"),
                "tags": doc.tags if doc.tags else [],
                "view_count": getattr(doc, 'view_count', 0) or 0,
                "created_at": doc.created_at,  # Raw datetime for correct sorting
                "publication_year": getattr(doc, 'publication_year', None),
                "has_pdf": bool(doc.file_url)
            })

        # 2. Lấy Datasets
        datasets = Dataset.query.filter_by(uploader_id=lecturer.id, status='approved').order_by(Dataset.created_at.desc()).all()
        dataset_list = []
        for doc in datasets:
            dataset_list.append({
                "id": doc.id,
                "title": doc.title,
                "doc_type": "dataset",
                "description": doc.description,
                "authors": doc.authors if doc.authors else [],
                "category_name": categories_dict.get(doc.category_id, "Không có"),
                "tags": doc.tags if doc.tags else [],
                "view_count": getattr(doc, 'view_count', 0) or 0,
                "created_at": doc.created_at,  # Raw datetime for correct sorting
                "has_pdf": False,
                "has_external_link": bool(getattr(doc, 'github_url', None))
            })

        all_docs = paper_list + dataset_list
        
        # Trộn sắp xếp theo ngày đăng mới nhất dùng datetime
        from datetime import datetime
        all_docs.sort(key=lambda x: x["created_at"] or datetime.min, reverse=True)

        # Định dạng lại ngày tháng sau khi đã sắp xếp xong
        for doc in all_docs:
            if isinstance(doc["created_at"], datetime):
                doc["created_at"] = doc["created_at"].strftime('%d/%m/%Y')
            else:
                doc["created_at"] = ""

        lecturer_info = {
            "id": lecturer.id,
            "user_code": lecturer.user_code,
            "email": lecturer.email,
            "full_name": lecturer.full_name,
            "avatar_url": lecturer.avatar_url,
            "academic_title": lecturer.academic_title,
            "bio": lecturer.bio,
            "department": lecturer.department
        }

        return jsonify({
            "message": "Chi tiết giảng viên",
            "lecturer": lecturer_info,
            "documents": all_docs
        }), 200

    except Exception as e:
        print(f"LỖI LẤY CHI TIẾT GIẢNG VIÊN: {str(e)}")
        return jsonify({"message": "Lỗi máy chủ"}), 500