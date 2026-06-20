from flask import Blueprint, request, jsonify
from routes.decorators import role_required
from models.models import db, User, StudentProfile, CompanyProfile, PlacementDrive, Application
from cache import cache_get, cache_set, cache_delete

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/dashboard', methods=['GET'])
@role_required('admin')
def dashboard():
    cached = cache_get('admin:dashboard:stats')
    if cached:
        return jsonify(cached), 200
    stats = {
        'students': User.query.filter_by(role='student').count(),
        'companies': CompanyProfile.query.count(),
        'drives': PlacementDrive.query.count(),
        'applications': Application.query.count(),
    }
    cache_set('admin:dashboard:stats', stats, ttl=300)
    return jsonify(stats), 200

@admin_bp.route('/companies', methods=['GET'])
@role_required('admin')
def list_companies():
    status_filter = request.args.get('approval_status')
    q = CompanyProfile.query
    if status_filter and status_filter != 'all':
        q = q.filter_by(approval_status=status_filter)
    companies = q.all()
    return jsonify([{
        'id': c.id, 'company_name': c.company_name, 'hr_contact': c.hr_contact,
        'website': c.website, 'approval_status': c.approval_status, 'email': c.user.email
    } for c in companies]), 200

@admin_bp.route('/companies/<int:company_id>/approve', methods=['PUT'])
@role_required('admin')
def approve_company(company_id):
    cp = CompanyProfile.query.get_or_404(company_id)
    cp.approval_status = 'approved'
    db.session.commit()
    cache_delete('admin:dashboard:stats', 'drives:approved:list')
    return jsonify({'id': cp.id, 'approval_status': cp.approval_status}), 200

@admin_bp.route('/companies/<int:company_id>/reject', methods=['PUT'])
@role_required('admin')
def reject_company(company_id):
    cp = CompanyProfile.query.get_or_404(company_id)
    cp.approval_status = 'rejected'
    PlacementDrive.query.filter_by(company_id=cp.id, status='approved').update(
        {'status': 'rejected'})
    db.session.commit()
    cache_delete('admin:dashboard:stats', 'drives:approved:list')
    return jsonify({'id': cp.id, 'approval_status': cp.approval_status}), 200

@admin_bp.route('/companies/<int:company_id>/blacklist', methods=['PUT'])
@role_required('admin')
def blacklist_company(company_id):
    cp = CompanyProfile.query.get_or_404(company_id)
    cp.approval_status = 'rejected'
    cp.user.is_active = False
    PlacementDrive.query.filter_by(company_id=cp.id, status='approved').update(
        {'status': 'rejected'})
    db.session.commit()
    cache_delete('admin:dashboard:stats', 'drives:approved:list')
    return jsonify({'id': cp.id, 'approval_status': cp.approval_status}), 200

@admin_bp.route('/drives', methods=['GET'])
@role_required('admin')
def list_drives():
    drives = PlacementDrive.query.all()
    return jsonify([{
        'id': d.id, 'title': d.title, 'status': d.status,
        'company_name': d.company.company_name, 'application_deadline': str(d.application_deadline)
    } for d in drives]), 200

@admin_bp.route('/drives/<int:drive_id>/approve', methods=['PUT'])
@role_required('admin')
def approve_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = 'approved'
    db.session.commit()
    cache_delete('admin:dashboard:stats', 'drives:approved:list')
    return jsonify({'id': drive.id, 'status': drive.status}), 200

@admin_bp.route('/drives/<int:drive_id>/reject', methods=['PUT'])
@role_required('admin')
def reject_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = 'rejected'
    db.session.commit()
    cache_delete('admin:dashboard:stats', 'drives:approved:list')
    return jsonify({'id': drive.id, 'status': drive.status}), 200

@admin_bp.route('/students', methods=['GET'])
@role_required('admin')
def list_students():
    students = StudentProfile.query.all()
    return jsonify([{
        'id': s.user.id, 'roll': s.roll, 'name': s.name, 'email': s.user.email,
        'branch': s.branch, 'cgpa': s.cgpa, 'is_active': s.user.is_active
    } for s in students]), 200

@admin_bp.route('/students/<int:user_id>/deactivate', methods=['PUT'])
@role_required('admin')
def deactivate_student(user_id):
    user = User.query.get_or_404(user_id)
    if user.role != 'student':
        return jsonify({'error': 'Target is not a student', 'code': 'NOT_STUDENT'}), 400
    user.is_active = False
    db.session.commit()
    return jsonify({'id': user.id, 'is_active': False}), 200

@admin_bp.route('/search', methods=['GET'])
@role_required('admin')
def search():
    q = request.args.get('q', '')
    search_type = request.args.get('type', 'student')
    if not q:
        return jsonify({'type': search_type, 'results': []}), 200
    if search_type == 'student':
        rows = StudentProfile.query.filter(StudentProfile.name.ilike(f'%{q}%')).all()
        return jsonify({
            'type': search_type,
            'results': [{'id': s.user.id, 'name': s.name, 'email': s.user.email, 'branch': s.branch}
                        for s in rows]
        }), 200
    rows = CompanyProfile.query.filter(CompanyProfile.company_name.ilike(f'%{q}%')).all()
    return jsonify({
        'type': search_type,
        'results': [{'id': c.id, 'name': c.company_name, 'email': c.user.email, 'status': c.approval_status}
                    for c in rows]
    }), 200
