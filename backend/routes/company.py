import json
from datetime import date
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from routes.decorators import role_required
from models.models import db, CompanyProfile, PlacementDrive, Application

company_bp = Blueprint('company', __name__, url_prefix='/api/company')

def _own_company():
    user_id = get_jwt_identity()
    return CompanyProfile.query.filter_by(user_id=user_id).first_or_404()

@company_bp.route('/dashboard', methods=['GET'])
@role_required('company')
def dashboard():
    cp = _own_company()
    drives = PlacementDrive.query.filter_by(company_id=cp.id).all()
    drive_data = [{
        'id': d.id, 'title': d.title, 'status': d.status,
        'deadline': str(d.application_deadline),
        'applicant_count': Application.query.filter_by(drive_id=d.id).count()
    } for d in drives]
    return jsonify({
        'company': {'id': cp.id, 'company_name': cp.company_name,
                    'approval_status': cp.approval_status},
        'drives': drive_data
    }), 200

@company_bp.route('/profile', methods=['PUT'])
@role_required('company')
def update_profile():
    cp = _own_company()
    data = request.get_json() or {}
    for field in ('company_name', 'hr_contact', 'website'):
        if field in data:
            setattr(cp, field, data[field])
    db.session.commit()
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
    deadline = date.fromisoformat(data['application_deadline'])
    if deadline <= date.today():
        return jsonify({'error': 'Deadline must be a future date',
                        'code': 'INVALID_DEADLINE'}), 400
    drive = PlacementDrive(
        company_id=cp.id,
        title=data['title'],
        description=data['description'],
        ctc=float(data['ctc']),
        location=data['location'],
        eligibility_cgpa=float(data['eligibility_cgpa']),
        eligibility_branch=json.dumps(data['eligibility_branch']),
        application_deadline=deadline,
        status='pending',
    )
    db.session.add(drive)
    db.session.commit()
    return jsonify({'id': drive.id, 'title': drive.title, 'status': drive.status}), 201

@company_bp.route('/drives/<int:drive_id>/applications', methods=['GET'])
@role_required('company')
def drive_applications(drive_id):
    cp = _own_company()
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.company_id != cp.id:
        return jsonify({'error': 'Access denied', 'code': 'FORBIDDEN'}), 403
    apps = Application.query.filter_by(drive_id=drive_id).all()
    return jsonify([{
        'id': a.id, 'status': a.status, 'applied_at': str(a.applied_at),
        'student': {
            'name': a.student.name, 'branch': a.student.branch, 'cgpa': a.student.cgpa,
            'resume_path': a.student.resume_path
        }
    } for a in apps]), 200

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
    return jsonify({'message': 'Status updated', 'status': new_status}), 200

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
    html = f"""<!DOCTYPE html>
<html><head><title>Offer Letter</title></head><body>
<h1>Offer Letter</h1>
<p>Dear <strong>{student.name}</strong>,</p>
<p>We are pleased to offer you the position of <strong>{drive.title}</strong>
at <strong>{drive.company.company_name}</strong>.</p>
<ul>
  <li>Location: {drive.location}</li>
  <li>CTC: {drive.ctc} LPA</li>
</ul>
<p>Congratulations and welcome aboard!</p>
<p>HR Team, {drive.company.company_name}</p>
</body></html>"""
    return html, 200, {'Content-Type': 'text/html'}
