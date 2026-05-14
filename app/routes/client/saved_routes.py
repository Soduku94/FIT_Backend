from flask import Blueprint, request, jsonify
from app.models.resource_model import Paper, Dataset, SavedResource
from app.models.news_model import News
from app.extensions import db
from app.utils.auth_middleware import token_required

saved_bp = Blueprint('saved', __name__)

@saved_bp.route('/saved', methods=['GET'])
@token_required
def get_saved_resources(current_user):
    """Lấy danh sách tất cả tài liệu đã lưu của người dùng hiện tại"""
    try:
        saved_items = SavedResource.query.filter_by(user_id=current_user.id).order_by(SavedResource.created_at.desc()).all()
        
        results = []
        for item in saved_items:
            resource = None
            if item.resource_type == 'paper':
                resource = Paper.query.get(item.resource_id)
            elif item.resource_type == 'dataset':
                resource = Dataset.query.get(item.resource_id)
            elif item.resource_type == 'news':
                resource = News.query.get(item.resource_id)
            
            if resource:
                results.append({
                    "id": resource.id,
                    "title": resource.title,
                    "type": item.resource_type,
                    "saved_at": item.created_at.strftime("%d/%m/%Y %H:%M"),
                    "thumbnail_url": getattr(resource, 'thumbnail_url', None),
                    "description": getattr(resource, 'description', getattr(resource, 'excerpt', '')),
                })
        
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@saved_bp.route('/saved/toggle', methods=['POST'])
@token_required
def toggle_save_resource(current_user):
    """Lưu hoặc bỏ lưu một tài liệu"""
    data = request.get_json()
    resource_id = data.get('resource_id')
    resource_type = data.get('resource_type') # 'paper', 'dataset', 'news'

    if not resource_id or not resource_type:
        return jsonify({"message": "Thiếu resource_id hoặc resource_type"}), 400

    try:
        existing = SavedResource.query.filter_by(
            user_id=current_user.id,
            resource_id=resource_id,
            resource_type=resource_type
        ).first()

        if existing:
            # Nếu đã tồn tại thì xóa đi (Unsave)
            db.session.delete(existing)
            db.session.commit()
            return jsonify({"message": "Đã bỏ lưu", "saved": False}), 200
        else:
            # Nếu chưa có thì thêm mới (Save)
            # Kiểm tra xem tài liệu có tồn tại không
            resource = None
            if resource_type == 'paper':
                resource = Paper.query.get(resource_id)
            elif resource_type == 'dataset':
                resource = Dataset.query.get(resource_id)
            elif resource_type == 'news':
                resource = News.query.get(resource_id)
            
            if not resource:
                return jsonify({"message": "Không tìm thấy tài liệu gốc"}), 404

            new_save = SavedResource(
                user_id=current_user.id,
                resource_id=resource_id,
                resource_type=resource_type
            )
            db.session.add(new_save)
            db.session.commit()
            return jsonify({"message": "Đã lưu tài liệu", "saved": True}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

@saved_bp.route('/saved/<string:resource_id>/check', methods=['GET'])
@token_required
def check_saved_status(current_user, resource_id):
    """Kiểm tra xem một tài liệu đã được người dùng này lưu chưa"""
    resource_type = request.args.get('type')
    
    query = SavedResource.query.filter_by(
        user_id=current_user.id,
        resource_id=resource_id
    )
    
    if resource_type:
        query = query.filter_by(resource_type=resource_type)
    
    saved_item = query.first()
    
    return jsonify({
        "is_saved": saved_item is not None
    }), 200
