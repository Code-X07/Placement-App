from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from models.models import User, CompanyProfile

def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            if not user or not user.is_active:
                return jsonify({'error': 'Account deactivated or not found',
                                'code': 'INACTIVE'}), 403
            if user.role != required_role:
                return jsonify({'error': 'Access denied', 'code': 'WRONG_ROLE'}), 403
            if required_role == 'company':
                profile = CompanyProfile.query.filter_by(user_id=user.id).first()
                if not profile or profile.approval_status != 'approved':
                    return jsonify({'error': 'Company account not approved',
                                    'code': 'NOT_APPROVED'}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator
