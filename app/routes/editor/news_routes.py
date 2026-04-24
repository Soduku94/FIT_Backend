from flask import Blueprint, request, jsonify
from app.models.news_model import News, NewsStatus
from app.extensions import db
from app.utils.auth_middleware import token_required
import slugify  # Cần cài đặt: pip install python-slugify

editor_bp = Blueprint('editor', __name__, url_prefix='/api/editor')


@editor_bp.route('/news', methods=['POST', 'OPTIONS'])
@token_required
def create_article(current_user):
    if request.method == 'OPTIONS':
        return jsonify({"message": "OK"}), 200
    # Chỉ Admin và Editor mới có quyền viết bài PR
    if current_user.role.value not in ['admin', 'editor']:
        return jsonify({"message": "Bạn không có quyền thực hiện chức năng này!"}), 403

    data = request.get_json()
    title = data.get('title')
    content = data.get('content')  # Nhận HTML từ React Quill

    if not title or not content:
        return jsonify({"message": "Tiêu đề và nội dung không được để trống!"}), 400

    new_post = News(
        title=title,
        content=content,
        slug=slugify.slugify(title),  # Tự động tạo slug từ tiêu đề
        thumbnail_url=data.get('thumbnail_url'),
        category=data.get('category', 'Tin tức'),
        status=NewsStatus.PUBLISHED if data.get('publish') else NewsStatus.DRAFT,
        author_id=current_user.id
    )

    db.session.add(new_post)
    db.session.commit()

    return jsonify({"message": "Đăng bài viết thành công!", "id": new_post.id}), 201