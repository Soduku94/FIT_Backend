from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

from . import user_routes
# Sau này có thêm file nào thì import tiếp ở đây\

from . import category_routes
from . import document_routes

from . import dashboard_routes


# admin_fit
# admin123


