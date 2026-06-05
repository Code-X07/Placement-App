from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import bcrypt
from models.models import db, User, StudentProfile, CompanyProfile

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided', 'code': 'MISSING_DATA'}), 400
    role = data.get('role', '')
    if role not in ('student', 'company'):
        return jsonify({'error': 'Invalid role — admin registration forbidden',
                        'code': 'ADMIN_FORBIDDEN'}), 400
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    if not email or not password:
        return jsonify({'error': 'Email and password required', 'code': 'MISSING_FIELDS'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered', 'code': 'DUPLICATE_EMAIL'}), 409

    user = User(
        email=email,
        password_hash=bcrypt.generate_password_hash(password).decode('utf-8'),
        role=role,
        is_active=True,
    )
    db.session.add(user)
    db.session.flush()

    if role == 'student':
        db.session.add(StudentProfile(user_id=user.id, name=data.get('name', '')))
    else:
        db.session.add(CompanyProfile(
            user_id=user.id,
            company_name=data.get('company_name', ''),
            approval_status='pending',
        ))
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({'token': token, 'role': user.role,
                    'user': {'id': user.id, 'email': user.email}}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data', 'code': 'MISSING_DATA'}), 400
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Invalid credentials', 'code': 'INVALID_CREDENTIALS'}), 401
    if not user.is_active:
        return jsonify({'error': 'Account deactivated', 'code': 'INACTIVE'}), 403
    token = create_access_token(identity=str(user.id))
    return jsonify({'token': token, 'role': user.role,
                    'user': {'id': user.id, 'email': user.email}}), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id) if user_id else None)
    if not user or not user.is_active:
        return jsonify({'error': 'Account not found', 'code': 'NOT_FOUND'}), 404
    return jsonify({'id': user.id, 'email': user.email, 'role': user.role}), 200
