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