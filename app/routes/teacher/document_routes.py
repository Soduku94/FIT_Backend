import os
import uuid
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, current_app

from app.models.resource_model import Paper, Dataset, Category
from app.extensions import db
from app.utils.auth_middleware import token_required

teacher_bp = Blueprint('teacher', __name__, url_prefix='/api/teacher')

ALLOWED_PDF = {'pdf'}
ALLOWED_DATASETS = {'zip', 'rar', '7z', 'csv', 'json', 'xml', 'txt'}


def allowed_file(filename, allowed_set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set


# ==========================================
# API 1: ĐĂNG TẢI BÀI BÁO (PAPER)
# ==========================================
@teacher_bp.route('/documents/paper', methods=['POST'])
@token_required
def upload_paper(current_user):
    if current_user.role not in ['teacher', 'admin', 'lecturer']:  # Sửa lại cho chuẩn role lecturer
        return jsonify({"message": "Chỉ giảng viên và quản trị viên mới có quyền đăng tải!"}), 403

    # 1. Lấy dữ liệu cơ bản
    title = request.form.get('title')
    description = request.form.get('description')
    category_id = request.form.get('category_id')

    # 2. Lấy các dữ liệu ĐẶC THÙ của BÀI BÁO (Các trường mới thêm)
    doi = request.form.get('doi')
    journal_name = request.form.get('journal_name')
    publication_year = request.form.get('publication_year')
    if publication_year:
        publication_year = int(publication_year)

    try:
        authors = json.loads(request.form.get('authors', '[]'))
        tag_names = json.loads(request.form.get('tags', '[]'))
    except json.JSONDecodeError:
        return jsonify({"message": "Định dạng danh sách Tác giả hoặc Từ khóa không hợp lệ!"}), 400

    if not title or not description or not category_id:
        return jsonify({"message": "Vui lòng nhập đủ Tiêu đề, Tóm tắt và Chọn danh mục!"}), 400

    # 3. Xử lý File PDF
    if 'main_file' not in request.files:
        return jsonify({"message": "Thiếu file bài báo (PDF)!"}), 400

    main_file = request.files['main_file']
    if main_file.filename == '' or not allowed_file(main_file.filename, ALLOWED_PDF):
        return jsonify({"message": "File bài báo bắt buộc phải là định dạng .pdf!"}), 400

    upload_dir = os.path.join(os.getcwd(), 'app', 'storage', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)

    safe_main_filename = f"paper_{uuid.uuid4().hex[:8]}_{secure_filename(main_file.filename)}"
    main_file_path = os.path.join(upload_dir, safe_main_filename)
    main_file.save(main_file_path)
    db_main_file_url = f"/storage/uploads/{safe_main_filename}"

    # 4. Lưu vào Database (Bảng Paper)
    new_paper = Paper(
        title=title,
        description=description,
        authors=authors,
        tags=tag_names,
        category_id=int(category_id),
        uploader_id=current_user.id,
        file_url=db_main_file_url,
        doi=doi,  # MỚI
        journal_name=journal_name,  # MỚI
        publication_year=publication_year,  # MỚI
        status='pending'
    )

    db.session.add(new_paper)
    db.session.commit()

    return jsonify({
        "message": "Đăng tải bài báo thành công! Vui lòng chờ Admin phê duyệt.",
        "document_id": new_paper.id
    }), 201


# ==========================================
# API 2: ĐĂNG TẢI BỘ DỮ LIỆU (DATASET)
# ==========================================
@teacher_bp.route('/documents/dataset', methods=['POST'])
@token_required
def upload_dataset(current_user):
    if current_user.role not in ['teacher', 'admin', 'lecturer']:
        return jsonify({"message": "Chỉ giảng viên và quản trị viên mới có quyền đăng tải!"}), 403

    # 1. Lấy dữ liệu cơ bản
    title = request.form.get('title')
    description = request.form.get('description')
    category_id = request.form.get('category_id')
    external_link = request.form.get('external_link', '').strip()

    # 2. Lấy dữ liệu ĐẶC THÙ của DATASET (Các trường mới thêm)
    file_size = request.form.get('file_size')
    data_format = request.form.get('data_format')
    license_type = request.form.get('license_type')

    try:
        authors = json.loads(request.form.get('authors', '[]'))
        tag_names = json.loads(request.form.get('tags', '[]'))
    except json.JSONDecodeError:
        return jsonify({"message": "Định dạng danh sách Tác giả hoặc Từ khóa không hợp lệ!"}), 400

    if not title or not description or not category_id:
        return jsonify({"message": "Vui lòng nhập đủ Tiêu đề, Mô tả và Chọn danh mục!"}), 400

    # 3. Xử lý File Data (Sửa lỗi hố đen mất file)
    db_file_url = None
    has_local_file = False

    # Ở Frontend, ta nên yêu cầu giảng viên nén thành 1 file ZIP và gửi lên với key là 'main_file'
    if 'main_file' in request.files:
        file = request.files['main_file']
        if file.filename != '':
            if allowed_file(file.filename, ALLOWED_DATASETS):
                upload_dir = os.path.join(os.getcwd(), 'app', 'storage', 'uploads')
                os.makedirs(upload_dir, exist_ok=True)

                safe_filename = f"dataset_{uuid.uuid4().hex[:8]}_{secure_filename(file.filename)}"
                file_path = os.path.join(upload_dir, safe_filename)
                file.save(file_path)

                db_file_url = f"/storage/uploads/{safe_filename}"  # Lưu đường dẫn này vào DB
                has_local_file = True
            else:
                return jsonify({"message": f"Định dạng file '{file.filename}' không được hỗ trợ!"}), 400

    if not external_link and not has_local_file:
        return jsonify({"message": "Vui lòng cung cấp Link Github HOẶC tải lên file dữ liệu!"}), 400

    # 4. Lưu vào Database (Bảng Dataset)
    new_dataset = Dataset(
        title=title,
        description=description,
        authors=authors,
        tags=tag_names,
        category_id=int(category_id),
        uploader_id=current_user.id,
        file_url=db_file_url,  # ĐÃ FIX: Giờ nó sẽ lưu link thực tế thay vì None
        github_url=external_link if external_link else None,
        file_size=file_size,  # MỚI
        data_format=data_format,  # MỚI
        license_type=license_type,  # MỚI
        status='pending'
    )

    db.session.add(new_dataset)
    db.session.commit()

    return jsonify({
        "message": "Đăng tải Dataset thành công! Vui lòng chờ Admin phê duyệt.",
        "document_id": new_dataset.id
    }), 201


# ==========================================
# API 3: XEM DANH SÁCH TÀI LIỆU CỦA TÔI
# ==========================================
@teacher_bp.route('/documents', methods=['GET'])
@token_required
def get_my_documents(current_user):
    if current_user.role not in ['teacher', 'admin', 'lecturer']:
        return jsonify({"message": "Truy cập bị từ chối!"}), 403

    filter_type = request.args.get('type')
    filter_status = request.args.get('status')

    documents = []

    # Query Bài Báo
    if filter_type == 'paper' or not filter_type:
        q_paper = Paper.query.filter_by(uploader_id=current_user.id)
        if filter_status:
            q_paper = q_paper.filter_by(status=filter_status)
        p_docs = q_paper.order_by(Paper.created_at.desc()).all()
        for p in p_docs:
            p.doc_type = 'paper'
        documents.extend(p_docs)

    # Query Dataset
    if filter_type == 'dataset' or not filter_type:
        q_data = Dataset.query.filter_by(uploader_id=current_user.id)
        if filter_status:
            q_data = q_data.filter_by(status=filter_status)
        d_docs = q_data.order_by(Dataset.created_at.desc()).all()
        for d in d_docs:
            d.doc_type = 'dataset'
        documents.extend(d_docs)

    # Sắp xếp tổng hợp mới nhất lên đầu
    documents.sort(key=lambda x: x.created_at, reverse=True)

    result = []
    for doc in documents:
        # Cách lấy category an toàn nhất tránh lỗi Relationship
        category = Category.query.get(doc.category_id)
        category_name = category.name if category else "Không có"

        result.append({
            "id": doc.id,
            "title": doc.title,
            "doc_type": "Bài báo khoa học" if doc.doc_type == 'paper' else "Bộ dữ liệu (Dataset)",
            "category_name": category_name,
            "status": doc.status,
            "reject_reason": getattr(doc, 'reject_reason', None),  # Nếu bị từ chối thì hiển thị lý do
            "created_at": doc.created_at.strftime('%d/%m/%Y %H:%M'),
            "has_file": bool(doc.file_url)
        })

    return jsonify({
        "message": "Lấy danh sách thành công",
        "total": len(result),
        "documents": result
    }), 200