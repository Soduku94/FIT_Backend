import os
from flask import request, jsonify, send_file
from app.models.resource_model import Paper, Dataset
from app.extensions import db
from app.utils.auth_middleware import token_required

# Import Blueprint từ file __init__ (ta sẽ tạo ở bước 2)
from . import student_bp


# ==========================================
# API: TẢI FILE TÀI LIỆU (SECURE DOWNLOAD)
# ==========================================
@student_bp.route('/documents/<string:document_id>/download', methods=['GET'])
@token_required  # Chốt chặn số 1: Bắt buộc phải có Token hợp lệ
def download_document(current_user, document_id):
    # 1. Tìm tài liệu trong DB
    doc = Paper.query.get(document_id)
    if not doc:
        # Check dataset ? Assuming document_id means paper for now
        doc = Dataset.query.get(document_id)
    if not doc:
        return jsonify({"message": "Không tìm thấy tài liệu!"}), 404

    # 2. Chốt chặn số 2: Kiểm tra quyền tải
    # (Chỉ cho phép tải nếu bài đã duyệt, HOẶC người đang tải chính là Admin / Tác giả của bài đó)
    is_approved = doc.status == 'approved'
    is_admin = current_user.role == 'admin'
    is_author = doc.uploader_id == current_user.id

    if not (is_approved or is_admin or is_author):
        return jsonify({"message": "Tài liệu này chưa được phê duyệt để tải xuống!"}), 403

    # 3. Kiểm tra xem tài liệu này có file không
    if not getattr(doc, 'file_url', None):
        return jsonify({"message": "Tài liệu này không có file đính kèm chính!"}), 404

    # 4. Xác định đường dẫn vật lý trên ổ cứng
    # Trong DB, file_url được lưu dạng: "/storage/uploads/xyz_file.pdf"
    # Ta cần ghép nó với thư mục gốc của project (os.getcwd())
    base_dir = os.getcwd()

    # Cắt bỏ dấu '/' ở đầu chuỗi đi để os.path.join hoạt động chính xác
    relative_path = doc.file_url.lstrip('/')

    # Đường dẫn thực tế sẽ kiểu như: D:\FIT_Backend\app\storage\uploads\xyz_file.pdf
    file_path = os.path.join(base_dir, 'app', relative_path)
    print(f"\n--- DEBUG: Flask đang tìm file tại đường dẫn: {file_path} ---\n")

    # 5. Kiểm tra file có thực sự tồn tại trong ổ cứng không (phòng trường hợp ai đó lỡ tay xóa file)
    if not os.path.exists(file_path):
        return jsonify({"message": "File vật lý đã bị mất hoặc di chuyển!"}), 404


    # 6. Tăng lượt tải lên 1 và lưu DB
    doc.download_count += 1
    db.session.commit()

    # 7. Trả file về cho người dùng tải xuống (Vũ khí bí mật của Flask)
    return send_file(
        file_path,
        as_attachment=True,  # Bắt buộc trình duyệt phải tải về máy thay vì mở lên xem
        download_name=f"FIT_Research_{doc.title}.pdf"  # Đổi tên file cho đẹp khi user tải về
    )