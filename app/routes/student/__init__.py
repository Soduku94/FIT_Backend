from flask import Blueprint

student_bp = Blueprint('student', __name__, url_prefix='/api/student')

from . import document_routes
