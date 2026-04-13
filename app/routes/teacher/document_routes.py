import os
import uuid
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, current_app

from app.models.document_model import Document, Category, Tag
from app.extensions import db
from app.utils.auth_middleware import token_required

teacher_bp = Blueprint('teacher', __name__, url_prefix='/api/teacher')

# Cấu hình đuôi file cho phép
ALLOWED_PDF = {'pdf'}
ALLOWED_ATTACHMENTS = {'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar'}
ALLOWED_DATASETS = {'zip', 'rar', '7z', 'csv', 'json', 'xml', 'txt'}


def allowed_file(filename, allowed_set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set


@teacher_bp.route('/documents/paper', methods=['POST'])
@token_required
def upload_paper(current_user):
    # 1. Kiểm tra quyền (Chỉ Giảng viên mới được upload)
    if current_user.role not in ['teacher', 'admin']:
        return jsonify({"message": "Chỉ giảng viên và quảm trị viên mới có quyền đăng tải tài liệu!"}), 403

    # 2. Lấy dữ liệu Text từ Form-data
    title = request.form.get('title')
    description = request.form.get('description')
    category_id = request.form.get('category_id')

    # Dữ liệu mảng (Authors, Tags) truyền qua form-data thường là chuỗi JSON, cần parse ra
    try:
        authors = json.loads(request.form.get('authors', '[]'))
        tag_names = json.loads(request.form.get('tags', '[]'))
    except json.JSONDecodeError:
        return jsonify({"message": "Định dạng danh sách Tác giả hoặc Từ khóa không hợp lệ!"}), 400

    if not title or not description or not category_id:
        return jsonify({"message": "Vui lòng nhập đủ Tiêu đề, Tóm tắt và Chọn danh mục!"}), 400

    # 3. Xử lý File PDF chính (Bắt buộc)
    if 'main_file' not in request.files:
        return jsonify({"message": "Thiếu file bài báo (PDF)!"}), 400

    main_file = request.files['main_file']
    if main_file.filename == '' or not allowed_file(main_file.filename, ALLOWED_PDF):
        return jsonify({"message": "File chính bắt buộc phải là định dạng .pdf!"}), 400

    # Tạo đường dẫn lưu file an toàn
    upload_dir = os.path.join(os.getcwd(), 'app', 'storage', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)  # Tự động tạo thư mục nếu chưa có

    # Đổi tên file: Gắn thêm UUID để tránh trùng tên nếu 2 thầy cùng up file "baocao.pdf"
    safe_main_filename = f"{uuid.uuid4().hex}_{secure_filename(main_file.filename)}"
    main_file_path = os.path.join(upload_dir, safe_main_filename)
    main_file.save(main_file_path)

    # Đường dẫn lưu vào DB (Đường dẫn tương đối)
    db_main_file_url = f"/storage/uploads/{safe_main_filename}"

    # 4. Xử lý các File đính kèm (Tùy chọn)
    attachments_data = []
    if 'attachments' in request.files:
        files = request.files.getlist('attachments')
        for file in files:
            if file and allowed_file(file.filename, ALLOWED_ATTACHMENTS):
                safe_att_filename = f"{uuid.uuid4().hex[:8]}_{secure_filename(file.filename)}"
                att_file_path = os.path.join(upload_dir, safe_att_filename)
                file.save(att_file_path)

                attachments_data.append({
                    "file_name": file.filename,  # Tên gốc để hiển thị cho đẹp
                    "url": f"/storage/uploads/{safe_att_filename}"
                })

    # 5. Xử lý Tags (Từ khóa)
    db_tags = []
    for t_name in tag_names:
        t_name = t_name.strip().lower()
        tag = Tag.query.filter_by(name=t_name).first()
        if not tag:
            tag = Tag(name=t_name)
            db.session.add(tag)
        db_tags.append(tag)

    # 6. Lưu vào Database
    new_paper = Document(
        title=title,
        doc_type='paper',
        description=description,
        authors=authors,
        category_id=int(category_id),
        uploader_id=current_user.id,
        main_file_url=db_main_file_url,
        attachments=attachments_data,
        tags=db_tags,
        status='pending'  # Mặc định là chờ Admin duyệt
    )

    db.session.add(new_paper)
    db.session.commit()

    return jsonify({
        "message": "Đăng tải bài báo thành công! Vui lòng chờ Admin phê duyệt.",
        "document_id": new_paper.id
    }), 201


# ==========================================
# API 2: ĐĂNG TẢI DATASET / GITHUB / NGUỒN NGOÀI
# ==========================================
@teacher_bp.route('/documents/dataset', methods=['POST'])
@token_required
def upload_dataset(current_user):
    # 1. Kiểm tra quyền
    if current_user.role not in ['teacher', 'admin']:
        return jsonify({"message": "Chỉ giảng viên và quản trị viên mới có quyền đăng tải!"}), 403

    # 2. Lấy dữ liệu Text
    title = request.form.get('title')
    description = request.form.get('description')  # Bài viết mô tả chi tiết data
    category_id = request.form.get('category_id')
    external_link = request.form.get('external_link', '').strip()

    try:
        authors = json.loads(request.form.get('authors', '[]'))
        tag_names = json.loads(request.form.get('tags', '[]'))
    except json.JSONDecodeError:
        return jsonify({"message": "Định dạng danh sách Tác giả hoặc Từ khóa không hợp lệ!"}), 400

    if not title or not description or not category_id:
        return jsonify({"message": "Vui lòng nhập đủ Tiêu đề, Mô tả và Chọn danh mục!"}), 400
    has_valid_file = False
    if 'attachments' in request.files:
        files = request.files.getlist('attachments')
        for file in files:
            if file.filename != '':  # Phải có tên file thì mới tính là có chọn
                has_valid_file = True
                break

    # Nếu link rỗng VÀ không có file hợp lệ nào -> Chặn lại ngay
    if not external_link and not has_valid_file:
        return jsonify(
            {"message": "Vui lòng cung cấp Link truy cập ngoài (URL) HOẶC tải lên ít nhất 1 file dữ liệu!"}), 400
    # 3. Xử lý File Data tải lên cục bộ (Nếu có)
    attachments_data = []
    if 'attachments' in request.files:
        files = request.files.getlist('attachments')
        upload_dir = os.path.join(os.getcwd(), 'app', 'storage', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)

        for file in files:
            if file.filename != '':
                if allowed_file(file.filename, ALLOWED_DATASETS):
                    safe_att_filename = f"{uuid.uuid4().hex[:8]}_data_{secure_filename(file.filename)}"
                    att_file_path = os.path.join(upload_dir, safe_att_filename)
                    file.save(att_file_path)

                    attachments_data.append({
                        "file_name": file.filename,
                        "url": f"/storage/uploads/{safe_att_filename}"
                    })
                else:
                    return jsonify({"message": f"Định dạng file '{file.filename}' không được hỗ trợ cho Dataset!"}), 400

    # 4. Xử lý Tags (Từ khóa)
    db_tags = []
    for t_name in tag_names:
        t_name = t_name.strip().lower()
        tag = Tag.query.filter_by(name=t_name).first()
        if not tag:
            tag = Tag(name=t_name)
            db.session.add(tag)
        db_tags.append(tag)

    # 5. Lưu vào Database
    new_dataset = Document(
        title=title,
        doc_type='dataset',  # Đánh dấu đây là dataset
        description=description,
        authors=authors,
        category_id=int(category_id),
        uploader_id=current_user.id,
        main_file_url=None,  # Dataset không có main_file PDF
        attachments=attachments_data,  # Chứa file .zip, .csv
        external_link=external_link if external_link else None,
        tags=db_tags,
        status='pending'
    )

    db.session.add(new_dataset)
    db.session.commit()

    return jsonify({
        "message": "Đăng tải Dataset/Tài nguyên thành công! Vui lòng chờ Admin phê duyệt.",
        "document_id": new_dataset.id,
        "has_local_files": len(attachments_data) > 0,
        "has_external_link": bool(external_link)
    }), 201


# ==========================================
# API 3: XEM DANH SÁCH TÀI LIỆU CỦA TÔI
# ==========================================
@teacher_bp.route('/documents', methods=['GET'])
@token_required
def get_my_documents(current_user):
    # 1. Kiểm tra quyền
    if current_user.role not in ['teacher', 'admin']:
        return jsonify({"message": "Truy cập bị từ chối!"}), 403

    # 2. Lấy tham số lọc trên URL (Ví dụ: ?type=paper hoặc ?status=pending)
    filter_type = request.args.get('type')
    filter_status = request.args.get('status')

    # 3. Tạo Query cơ bản: Chỉ lấy tài liệu do CHÍNH user này up lên
    query = Document.query.filter_by(uploader_id=current_user.id)

    # Áp dụng bộ lọc nếu có
    if filter_type:
        query = query.filter_by(doc_type=filter_type)
    if filter_status:
        query = query.filter_by(status=filter_status)

    # 4. Thực thi Query, sắp xếp bài mới nhất lên đầu
    documents = query.order_by(Document.created_at.desc()).all()

    # 5. Format dữ liệu trả về
    result = []
    for doc in documents:
        # Lấy danh sách tên từ khóa (tags)
        tag_list = [tag.name for tag in doc.tags]

        result.append({
            "id": doc.id,
            "title": doc.title,
            "doc_type": "Bài báo khoa học" if doc.doc_type == 'paper' else "Dataset / Nguồn ngoài",
            "category_name": doc.category.name if doc.category else "Không có",
            "authors": doc.authors,
            "tags": tag_list,
            "status": doc.status,
            "created_at": doc.created_at.strftime('%Y-%m-%d %H:%M'),

            # Trả về cờ để Frontend biết hiển thị icon gì
            "has_pdf": bool(doc.main_file_url),
            "has_external_link": bool(doc.external_link),
            "attachments_count": len(doc.attachments) if doc.attachments else 0
        })

    return jsonify({
        "message": "Lấy danh sách thành công",
        "total": len(result),
        "documents": result
    }), 200