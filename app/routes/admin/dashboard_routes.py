from flask import Blueprint, jsonify, request
from app.models.user_model import User

from app.models.document_model import Document, Category
from app.utils.auth_middleware import admin_required
from app.extensions import db
from sqlalchemy import func

from . import admin_bp


@admin_bp.route('/dashboard/stats', methods=['GET', 'OPTIONS'])
@admin_required
def get_dashboard_stats(current_user):
    if request.method == 'OPTIONS':
        return jsonify({"message": "CORS preflight OK"}), 200

    try:
        # 1. Đếm số liệu tổng quan cho 4 thẻ (Cards)
        total_docs = Document.query.count()
        pending_docs = Document.query.filter_by(status='pending').count()
        total_users = User.query.count()

        # (Nếu bảng Document của bạn chưa có cột views/downloads thì trả về 0 tạm)
        total_downloads = 0

        # 2. Thống kê số bài báo theo từng Danh mục (Cho Biểu đồ cột)
        # Câu lệnh SQL: SELECT category.name, COUNT(document.id) ...
        category_stats = db.session.query(
            Category.name,
            func.count(Document.id)
        ).outerjoin(Document, Category.id == Document.category_id).group_by(Category.name).all()

        # Biến đổi dữ liệu cho đúng định dạng của Recharts Frontend
        category_data = [{"name": cat[0], "count": cat[1]} for cat in category_stats]

        # 3. Biểu đồ đường (Lượt tải theo tháng) - Tạm thời trả về dữ liệu giả để biểu đồ lên hình
        download_data = [
            {"month": "Tháng 1", "downloads": 12},
            {"month": "Tháng 2", "downloads": 45},
            {"month": "Tháng 3", "downloads": 28},
            {"month": "Tháng 4", "downloads": 80},
            {"month": "Tháng 5", "downloads": 65},
        ]

        return jsonify({
            "message": "Lấy dữ liệu thống kê thành công",
            "stats": {
                "total_docs": total_docs,
                "pending_docs": pending_docs,
                "total_users": total_users,
                "total_downloads": total_downloads
            },
            "category_data": category_data,
            "download_data": download_data
        }), 200

    except Exception as e:
        print(f"LỖI TẠI DASHBOARD: {str(e)}")
        return jsonify({"message": "Lỗi khi lấy dữ liệu thống kê"}), 500