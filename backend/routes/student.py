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

@student_bp.route('/profile', methods=['GET'])
@role_required('student')
def get_profile():
    sp = _own_student()
    user = sp.user
    return jsonify({
        'name': sp.name,
        'phone': sp.phone,
        'branch': sp.branch,
        'year': sp.year,
        'cgpa': sp.cgpa,
        'resume_path': sp.resume_path,
        'email': user.email
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
    return jsonify({
        'name': sp.name, 'phone': sp.phone, 'branch': sp.branch,
        'year': sp.year, 'cgpa': sp.cgpa, 'resume_path': sp.resume_path,
        'email': sp.user.email
    }), 200

@student_bp.route('/dashboard', methods=['GET'])
@role_required('student')
def dashboard():
    sp = _own_student()
    apps = Application.query.filter_by(student_id=sp.id).all()

    # Aggregate counts by status
    counts = {'applied': 0, 'shortlisted': 0, 'selected': 0, 'rejected': 0}
    for app in apps:
        if app.status in counts:
            counts[app.status] += 1

    # Get first 3 approved drives with future deadlines (teaser list, ignore eligibility)
    today = date.today()
    all_drives = PlacementDrive.query.filter_by(status='approved').filter(
        PlacementDrive.application_deadline >= today
    ).all()
    recommended = [_drive_dict(d) for d in all_drives[:3]]

    return jsonify({
        'name': sp.name,
        'branch': sp.branch,
        'counts': counts,
        'recommended': recommended
    }), 200

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
    head = f.read(5)
    f.seek(0)
    if not head.startswith(b'%PDF'):
        return jsonify({'error': 'File is not a valid PDF',
                        'code': 'INVALID_FILE_TYPE'}), 400
    filename = secure_filename(f'{sp.id}_{f.filename}')
    if not filename or not filename.lower().endswith('.pdf'):
        filename = f'{sp.id}_resume.pdf'
    upload_dir = os.path.join(current_app.root_path, 'uploads', 'resumes')
    os.makedirs(upload_dir, exist_ok=True)
    f.save(os.path.join(upload_dir, filename))
    sp.resume_path = f'uploads/resumes/{filename}'
    db.session.commit()
    return jsonify({'resume_path': sp.resume_path, 'filename': filename}), 200

@student_bp.route('/drives', methods=['GET'])
@role_required('student')
def list_drives():
    sp = _own_student()
    today = date.today()
    all_drives_raw = PlacementDrive.query.filter_by(status='approved').filter(
        PlacementDrive.application_deadline >= today
    ).all()

    # Load all student applications once to avoid N+1 queries
    student_app_drive_ids = {
        a.drive_id for a in Application.query.filter_by(student_id=sp.id).all()
    }

    result = []
    for d in all_drives_raw:
        applied, eligible, reasons = _elig_state(sp, d, student_app_drive_ids)
        result.append({
            'id': d.id,
            'title': d.title,
            'company_name': d.company.company_name,
            'ctc': d.ctc,
            'location': d.location,
            'application_deadline': str(d.application_deadline),
            'eligibility_cgpa': d.eligibility_cgpa,
            'eligibility_branch': _parse_eligibility_branch(d.eligibility_branch),
            'applied': applied,
            'eligible': eligible,
            'reasons': reasons
        })
    return jsonify(result), 200

@student_bp.route('/drives/<int:drive_id>/apply', methods=['POST'])
@role_required('student')
def apply(drive_id):
    sp = _own_student()
    drive = db.session.get(PlacementDrive, drive_id)
    if drive is None:
        return jsonify({'error': 'Drive not found', 'code': 'NOT_FOUND'}), 404
    if drive.status != 'approved' or drive.application_deadline < date.today():
        return jsonify({'error': 'This drive is not open for applications',
                        'code': 'NOT_OPEN'}), 400
    # already-applied takes precedence over eligibility (matches mock.js order)
    if Application.query.filter_by(student_id=sp.id, drive_id=drive_id).first():
        return jsonify({'error': 'You have already applied to this drive',
                        'code': 'DUPLICATE'}), 409
    _, eligible, reasons = _elig_state(sp, drive, set())
    if not eligible:
        return jsonify({'error': '; '.join(reasons) or 'Not eligible',
                        'code': 'INELIGIBLE', 'reasons': reasons}), 400
    app_obj = Application(student_id=sp.id, drive_id=drive_id, status='applied')
    db.session.add(app_obj)
    from sqlalchemy.exc import IntegrityError
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'You have already applied to this drive',
                        'code': 'DUPLICATE'}), 409
    from cache import cache_delete
    cache_delete('admin:dashboard:stats')
    return jsonify({'ok': True}), 201

@student_bp.route('/applications', methods=['GET'])
@role_required('student')
def applications():
    sp = _own_student()
    apps = Application.query.filter_by(student_id=sp.id).all()
    return jsonify([{
        'id': a.id,
        'company_name': a.drive.company.company_name,
        'location': a.drive.location,
        'role': a.drive.title,
        'applied_at': str(a.applied_at),
        'status': a.status
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
    job = db.session.get(ExportJob, job_id)
    if job is None:
        return jsonify({'error': 'Export job not found', 'code': 'NOT_FOUND'}), 404
    if job.student_id != sp.id:
        return jsonify({'error': 'Export job not found', 'code': 'NOT_FOUND'}), 404
    resp = {'job_id': job.id, 'status': job.status}
    if job.status == 'done' and job.file_path:
        resp['file_path'] = f'/student/export/{job.id}/download'
        resp['filename'] = os.path.basename(job.file_path)
    elif job.status == 'failed':
        resp['error'] = 'Export failed to generate the file. Please retry.'
    return jsonify(resp), 200

@student_bp.route('/export/<int:job_id>/download', methods=['GET'])
@role_required('student')
def download_export(job_id):
    sp = _own_student()
    job = db.session.get(ExportJob, job_id)
    if job is None:
        return jsonify({'error': 'Export job not found', 'code': 'NOT_FOUND'}), 404
    if job.student_id != sp.id:
        return jsonify({'error': 'Export job not found', 'code': 'NOT_FOUND'}), 404
    if job.status != 'done' or not job.file_path:
        return jsonify({'error': 'Export not ready', 'code': 'NOT_READY'}), 404
    directory = os.path.join(current_app.root_path, 'uploads', 'exports')
    filename = os.path.basename(job.file_path)
    return send_from_directory(directory, filename, as_attachment=True)

def _parse_eligibility_branch(eligibility_branch_str):
    """Parse eligibility_branch JSON string to a list (never a scalar)."""
    if not eligibility_branch_str:
        return []
    try:
        parsed = json.loads(eligibility_branch_str)
    except (ValueError, TypeError):
        return []
    return parsed if isinstance(parsed, list) else []

def _elig_state(sp, drive, applied_drive_ids):
    """
    Compute eligibility state for a student-drive pair.
    Returns: (applied: bool, eligible: bool, reasons: list[str])
    """
    reasons = []

    # Check if already applied
    applied = drive.id in applied_drive_ids
    if applied:
        reasons.append("Already applied")

    # Check CGPA eligibility (a drive with eligibility_cgpa 0/None imposes no bar)
    if drive.eligibility_cgpa:
        if sp.cgpa is None or sp.cgpa < drive.eligibility_cgpa:
            reasons.append(f"Requires CGPA ≥ {drive.eligibility_cgpa:.1f}")

    # Check branch eligibility (empty branch list imposes no bar)
    branches = _parse_eligibility_branch(drive.eligibility_branch)
    if branches and (not sp.branch or sp.branch not in branches):
        reasons.append("Branch not eligible")

    # Eligible if there are no blocking reasons (an "Already applied" note doesn't block)
    eligible = all(r == "Already applied" for r in reasons)

    return applied, eligible, reasons

def _drive_dict(d):
    """Create a minimal drive dict for dashboard teaser list."""
    return {
        'id': d.id,
        'title': d.title,
        'company_name': d.company.company_name,
        'ctc': d.ctc,
        'location': d.location,
        'application_deadline': str(d.application_deadline),
    }
