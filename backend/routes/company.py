import json
import os
from datetime import date
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import get_jwt_identity
from routes.decorators import role_required
from models.models import db, CompanyProfile, PlacementDrive, Application

company_bp = Blueprint('company', __name__, url_prefix='/api/company')

def _own_company():
    user_id = get_jwt_identity()
    return CompanyProfile.query.filter_by(user_id=int(user_id)).first_or_404()

@company_bp.route('/dashboard', methods=['GET'])
@role_required('company')
def dashboard():
    from cache import cache_get, cache_set
    user_id = get_jwt_identity()
    cache_key = f'company:{user_id}:dashboard'
    cached = cache_get(cache_key)
    if cached:
        return jsonify(cached), 200
    cp = _own_company()
    drives = PlacementDrive.query.filter_by(company_id=cp.id).all()
    drive_data = [{
        'id': d.id, 'title': d.title, 'status': d.status,
        'application_deadline': str(d.application_deadline),
        'location': d.location,
        'applicant_count': Application.query.filter_by(drive_id=d.id).count()
    } for d in drives]
    active_drives = sum(1 for d in drives if d.status == 'approved')
    total_applicants = sum(Application.query.filter_by(drive_id=d.id).count() for d in drives)
    result = {
        'company_name': cp.company_name,
        'approval_status': cp.approval_status,
        'website': cp.website,
        'active_drives': active_drives,
        'total_applicants': total_applicants,
        'drives': drive_data
    }
    cache_set(cache_key, result, ttl=300)
    return jsonify(result), 200

@company_bp.route('/profile', methods=['PUT'])
@role_required('company')
def update_profile():
    cp = _own_company()
    data = request.get_json() or {}
    for field in ('company_name', 'hr_contact', 'website'):
        if field in data:
            setattr(cp, field, data[field])
    db.session.commit()
    from cache import cache_delete
    cache_delete(f'company:{get_jwt_identity()}:dashboard')
    return jsonify({'message': 'Profile updated'}), 200

@company_bp.route('/drives', methods=['POST'])
@role_required('company')
def create_drive():
    cp = _own_company()
    data = request.get_json() or {}
    required = ('title', 'description', 'ctc', 'location',
                 'eligibility_cgpa', 'eligibility_branch', 'application_deadline')
    for field in required:
        if field not in data:
            return jsonify({'error': f'{field} required', 'code': 'MISSING_FIELDS'}), 400
    try:
        deadline = date.fromisoformat(data['application_deadline'])
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD',
                        'code': 'INVALID_DATE_FORMAT'}), 400
    if deadline <= date.today():
        return jsonify({'error': 'Deadline must be a future date',
                        'code': 'INVALID_DEADLINE'}), 400
    try:
        ctc = float(data['ctc'])
        eligibility_cgpa = float(data['eligibility_cgpa'])
    except (ValueError, TypeError):
        return jsonify({'error': 'ctc and eligibility_cgpa must be numbers',
                        'code': 'INVALID_NUMBER'}), 400
    if not isinstance(data['eligibility_branch'], list):
        return jsonify({'error': 'eligibility_branch must be a list of strings',
                        'code': 'INVALID_BRANCH_FORMAT'}), 400
    drive = PlacementDrive(
        company_id=cp.id,
        title=data['title'],
        description=data['description'],
        ctc=ctc,
        location=data['location'],
        eligibility_cgpa=eligibility_cgpa,
        eligibility_branch=json.dumps(data['eligibility_branch']),
        application_deadline=deadline,
        status='pending',
        department=data.get('department'),
    )
    db.session.add(drive)
    db.session.commit()
    from cache import cache_delete
    cache_delete(f'company:{get_jwt_identity()}:dashboard', 'admin:dashboard:stats')
    return jsonify({'id': drive.id, 'status': drive.status}), 201

@company_bp.route('/drives/<int:drive_id>/applications', methods=['GET'])
@role_required('company')
def drive_applications(drive_id):
    cp = _own_company()
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.company_id != cp.id:
        return jsonify({'error': 'Access denied', 'code': 'FORBIDDEN'}), 403
    apps = Application.query.filter_by(drive_id=drive_id).all()
    return jsonify({
        'drive_title': drive.title,
        'company_name': drive.company.company_name,
        'applicants': [{
            'id': a.id, 'name': a.student.name, 'roll': a.student.roll,
            'branch': a.student.branch, 'cgpa': a.student.cgpa,
            'resume_path': a.student.resume_path, 'status': a.status
        } for a in apps]
    }), 200

@company_bp.route('/applications/<int:app_id>/status', methods=['PUT'])
@role_required('company')
def update_application_status(app_id):
    cp = _own_company()
    app_obj = Application.query.get_or_404(app_id)
    if app_obj.drive.company_id != cp.id:
        return jsonify({'error': 'Access denied', 'code': 'FORBIDDEN'}), 403
    data = request.get_json() or {}
    allowed = ('shortlisted', 'selected', 'rejected')
    new_status = data.get('status')
    if new_status not in allowed:
        return jsonify({'error': f'status must be one of {allowed}',
                        'code': 'INVALID_STATUS'}), 400
    app_obj.status = new_status
    db.session.commit()
    from cache import cache_delete
    cache_delete(f'company:{get_jwt_identity()}:dashboard', 'admin:dashboard:stats')
    return jsonify({'id': app_obj.id, 'status': new_status}), 200

@company_bp.route('/applications/<int:app_id>/offer-letter', methods=['GET'])
@role_required('company')
def offer_letter(app_id):
    cp = _own_company()
    app_obj = Application.query.get_or_404(app_id)
    if app_obj.drive.company_id != cp.id:
        return jsonify({'error': 'Access denied', 'code': 'FORBIDDEN'}), 403
    if app_obj.status != 'selected':
        return jsonify({'error': 'Offer letter available only for selected applicants',
                        'code': 'NOT_SELECTED'}), 400
    student = app_obj.student
    drive = app_obj.drive
    company_address = (drive.company.address or '').splitlines() or [drive.company.website or '']
    return jsonify({
        'company': {'name': drive.company.company_name, 'address': company_address},
        'date': date.today().strftime('%B %d, %Y'),
        'student_name': student.name,
        'position': drive.title,
        'department': drive.department or '',
        'ctc': f'{drive.ctc} LPA',
        'location': drive.location,
        'intro': (f'Following our recent discussions, we are delighted to offer you the position of '
                  f'{drive.title} at {drive.company.company_name}. We were impressed with your academic '
                  f'record and approach to problem-solving.'),
        'body': ('In this role you will join our team and contribute to projects aligned with the '
                 'responsibilities outlined for this position. We believe your skills will be a valuable '
                 'asset to our organisation and look forward to welcoming you aboard.'),
    }), 200

@company_bp.route('/applications/<int:app_id>/resume', methods=['GET'])
@role_required('company')
def resume_download(app_id):
    cp = _own_company()
    app_obj = Application.query.get_or_404(app_id)
    if app_obj.drive.company_id != cp.id:
        return jsonify({'error': 'Access denied', 'code': 'FORBIDDEN'}), 403
    student = app_obj.student
    if not student.resume_path:
        return jsonify({'error': 'No resume available for this student',
                        'code': 'NO_RESUME'}), 404
    resume_dir = os.path.join(current_app.root_path, 'uploads', 'resumes')
    filename = os.path.basename(student.resume_path)
    return send_from_directory(resume_dir, filename, as_attachment=False)
