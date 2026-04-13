import os
import time
from flask import request, jsonify
from werkzeug.utils import secure_filename
from app.models.document_model import Document
from app.utils.auth_middleware import token_required
from app.extensions import db
from app.routes.auth import auth_bp

# Cấu hình thư mục lưu file và định dạng cho phép
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Tự động tạo thư mục nếu chưa có


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@auth_bp.route('/upload', methods=['POST', 'OPTIONS'])
@token_required
def upload_document(current_user):
    if request.method == 'OPTIONS':
        return jsonify({"message": "OK"}), 200

    try:
        # 1. Lấy dữ liệu văn bản từ Form
        title = request.form.get('title')
        description = request.form.get('description')
        category_id = request.form.get('category_id')  # Tạm thời lấy ID chuyên ngành
        doc_type = request.form.get('doc_type')
        authors = request.form.get('authors')

        # 2. Xử lý File đính kèm
        if 'file' not in request.files:
            return jsonify({"message": "Thiếu file đính kèm!"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"message": "Chưa chọn file!"}), 400

        if file and allowed_file(file.filename):
            # Làm sạch tên file và thêm timestamp để không bị trùng lặp
            filename = secure_filename(file.filename)
            unique_filename = f"{int(time.time())}_{filename}"
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

            # Lưu file vào thư mục uploads
            file.save(file_path)

            # 3. Lưu thông tin vào Database (Trạng thái mặc định là 'pending')
            file_url = f"http://127.0.0.1:5000/uploads/{unique_filename}"

            new_doc = Document(
                title=title,
                description=description,
                category_id=category_id,
                doc_type=doc_type,
                authors=authors,
                uploader_id=current_user.id,
                status='pending',  # CHỜ ADMIN DUYỆT
                main_file_url=file_url
            )
            db.session.add(new_doc)
            db.session.commit()

            return jsonify({"message": "Tải lên thành công, đang chờ Admin duyệt!"}), 201
        else:
            return jsonify({"message": "Hệ thống chỉ chấp nhận định dạng PDF, DOC, DOCX!"}), 400

    except Exception as e:
        print(f"LỖI UPLOAD: {str(e)}")
        return jsonify({"message": "Lỗi máy chủ khi tải file"}), 500