from flask import Blueprint

# Khởi tạo Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# IMPORT CÁC FILE ROUTE CON Ở DƯỚI CÙNG (Bắt buộc để tránh lỗi circular import)
from . import auth_routes