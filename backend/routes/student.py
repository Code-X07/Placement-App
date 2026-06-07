import os
import json
from datetime import date
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import get_jwt_identity
from werkzeug.utils import secure_filename
from routes.decorators import role_required
from models.models import db, StudentProfile, PlacementDrive, Application, ExportJob

student_bp = Blueprint('student', __name__, url_prefix='/api/student')

def _own_student():
    user_id = get_jwt_identity()
    return StudentProfile.query.filter_by(user_id=int(user_id)).first_or_404()

@student_bp.route('/dashboard', methods=['GET'])
@role_required('student')
def dashboard():
    sp = _own_student()
    drives = _eligible_drives(sp)
    apps = Application.query.filter_by(student_id=sp.id).all()
    return jsonify({
        'drives': [_drive_dict(d) for d in drives],
        'applications': [{'drive': a.drive.title, 'status': a.status,
                          'applied_at': str(a.applied_at)} for a in apps]
    }), 200

@student_bp.route('/profile', methods=['PUT'])
@role_required('student')
def update_profile():
    sp = _own_student()
    data = request.get_json() or {}
    for field in ('name', 'phone', 'branch', 'year'):
        if field in data:
            setattr(sp, field, data[field])
    if 'cgpa' in data:
        try:
            cgpa = float(data['cgpa'])
        except (ValueError, TypeError):
            return jsonify({'error': 'CGPA must be a number', 'code': 'INVALID_CGPA'}), 400
        if not 0 <= cgpa <= 10:
            return jsonify({'error': 'CGPA must be between 0 and 10',
                            'code': 'INVALID_CGPA'}), 400
        sp.cgpa = cgpa
    db.session.commit()
    return jsonify({'message': 'Profile updated'}), 200

@student_bp.route('/profile/resume', methods=['POST'])
@role_required('student')
def upload_resume():
    sp = _own_student()
    if 'resume' not in request.files:
        return jsonify({'error': 'No file provided', 'code': 'MISSING_FILE'}), 400
    f = request.files['resume']
    if not f.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files allowed',
                        'code': 'INVALID_FILE_TYPE'}), 400
    filename = secure_filename(f'{sp.id}_{f.filename}')
    upload_dir = os.path.join(current_app.root_path, '..', 'uploads', 'resumes')
    os.makedirs(upload_dir, exist_ok=True)
    f.save(os.path.join(upload_dir, filename))
    sp.resume_path = f'uploads/resumes/{filename}'
    db.session.commit()
    return jsonify({'message': 'Resume uploaded', 'path': sp.resume_path}), 200

@student_bp.route('/drives', methods=['GET'])
@role_required('student')
def list_drives():
    from cache import cache_get, cache_set
    sp = _own_student()
    cache_key = 'drives:approved:list'
    all_drives = cache_get(cache_key)
    if all_drives is None:
        raw = PlacementDrive.query.filter_by(status='approved').all()
        all_drives = [_drive_dict(d) for d in raw]
        cache_set(cache_key, all_drives, ttl=300)
    today = str(date.today())
    result = []
    for d in all_drives:
        if d['deadline'] < today:
            continue
        if sp.cgpa is not None and d['eligibility_cgpa'] is not None and sp.cgpa < d['eligibility_cgpa']:
            continue
        if sp.branch and d['eligibility_branch'] and sp.branch not in d['eligibility_branch']:
            continue
        result.append(d)
    return jsonify(result), 200

@student_bp.route('/drives/<int:drive_id>/apply', methods=['POST'])
@role_required('student')
def apply(drive_id):
    sp = _own_student()
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.status != 'approved':
        return jsonify({'error': 'Drive not approved', 'code': 'DRIVE_NOT_APPROVED'}), 400
    if drive.application_deadline < date.today():
        return jsonify({'error': 'Application deadline has passed',
                        'code': 'DEADLINE_PASSED'}), 400
    if sp.cgpa is None or sp.cgpa < (drive.eligibility_cgpa or 0):
        return jsonify({'error': 'CGPA below drive requirement',
                        'code': 'INELIGIBLE_CGPA'}), 400
    if sp.branch and drive.eligibility_branch:
        try:
            allowed = json.loads(drive.eligibility_branch)
        except (ValueError, TypeError):
            allowed = []
        if sp.branch not in allowed:
            return jsonify({'error': 'Branch not eligible for this drive',
                            'code': 'INELIGIBLE_BRANCH'}), 400
    if Application.query.filter_by(student_id=sp.id, drive_id=drive_id).first():
        return jsonify({'error': 'Already applied to this drive',
                        'code': 'ALREADY_APPLIED'}), 409
    app_obj = Application(student_id=sp.id, drive_id=drive_id, status='applied')
    db.session.add(app_obj)
    db.session.commit()
    from cache import cache_delete
    cache_delete('admin:dashboard:stats', 'drives:approved:list')
    return jsonify({'message': 'Applied successfully', 'application_id': app_obj.id}), 201

@student_bp.route('/applications', methods=['GET'])
@role_required('student')
def applications():
    sp = _own_student()
    apps = Application.query.filter_by(student_id=sp.id).all()
    return jsonify([{
        'id': a.id, 'drive': a.drive.title,
        'company': a.drive.company.company_name,
        'status': a.status, 'applied_at': str(a.applied_at)
    } for a in apps]), 200

@student_bp.route('/export', methods=['POST'])
@role_required('student')
def trigger_export():
    sp = _own_student()
    job = ExportJob(student_id=sp.id, status='pending')
    db.session.add(job)
    db.session.commit()
    from tasks.export import export_student_data
    result = export_student_data.delay(job.id)
    job.celery_task_id = result.id
    db.session.commit()
    return jsonify({'job_id': job.id, 'status': 'pending'}), 202

@student_bp.route('/export/<int:job_id>', methods=['GET'])
@role_required('student')
def export_status(job_id):
    sp = _own_student()
    job = ExportJob.query.get_or_404(job_id)
    if job.student_id != sp.id:
        return jsonify({'error': 'Access denied', 'code': 'FORBIDDEN'}), 403
    resp = {'job_id': job.id, 'status': job.status}
    if job.status == 'done' and job.file_path:
        resp['download_url'] = f'/api/student/export/{job.id}/download'
    return jsonify(resp), 200

@student_bp.route('/export/<int:job_id>/download', methods=['GET'])
@role_required('student')
def download_export(job_id):
    sp = _own_student()
    job = ExportJob.query.get_or_404(job_id)
    if job.student_id != sp.id:
        return jsonify({'error': 'Access denied', 'code': 'FORBIDDEN'}), 403
    if job.status != 'done' or not job.file_path:
        return jsonify({'error': 'Export not ready', 'code': 'NOT_READY'}), 404
    directory = os.path.join(current_app.root_path, 'uploads', 'exports')
    filename = os.path.basename(job.file_path)
    return send_from_directory(directory, filename, as_attachment=True)

def _eligible_drives(sp):
    drives = PlacementDrive.query.filter_by(status='approved').all()
    result = []
    for d in drives:
        if d.application_deadline < date.today():
            continue
        if sp.cgpa is not None and d.eligibility_cgpa is not None and sp.cgpa < d.eligibility_cgpa:
            continue
        if sp.branch and d.eligibility_branch:
            try:
                branches = json.loads(d.eligibility_branch)
            except (ValueError, TypeError):
                branches = []
            if sp.branch not in branches:
                continue
        result.append(d)
    return result

def _drive_dict(d):
    try:
        branches = json.loads(d.eligibility_branch) if d.eligibility_branch else []
    except (ValueError, TypeError):
        branches = []
    return {
        'id': d.id, 'title': d.title, 'company': d.company.company_name,
        'ctc': d.ctc, 'location': d.location, 'deadline': str(d.application_deadline),
        'eligibility_cgpa': d.eligibility_cgpa,
        'eligibility_branch': branches,
    }
