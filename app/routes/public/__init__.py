from flask import Blueprint

# Tạo nhánh public với tiền tố /api/public
public_bp = Blueprint('public', __name__, url_prefix='/api/public')

# Import các file con vào
from . import document_routes
from . import landing_routes