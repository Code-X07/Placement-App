from datetime import date, timedelta
import io

def _stu(client, student_user):
    return {'Authorization': f"Bearer {student_user['token']}"}

def _student_headers(client, cgpa=None, branch=None):
    r = client.post('/api/auth/register', json={
        'email': f'sx{cgpa}{branch}@t.com', 'password': 'pw1234', 'role': 'student', 'name': 'Sx'})
    h = {'Authorization': f"Bearer {r.json['token']}"}
    if cgpa is not None or branch is not None:
        client.put('/api/student/profile', headers=h, json={'cgpa': cgpa or 0, 'branch': branch or ''})
    return h

def _set_profile(client, headers, cgpa=8.0, branch='CS'):
    client.put('/api/student/profile', headers=headers, json={
        'name': 'Alice', 'phone': '9876543210', 'branch': branch, 'year': 3, 'cgpa': cgpa
    })

def test_update_profile(client, student_user):
    resp = client.put('/api/student/profile', headers=_stu(client, student_user), json={
        'name': 'Alice', 'phone': '9876543210', 'branch': 'CS', 'year': 3, 'cgpa': 8.0
    })
    assert resp.status_code == 200

def test_get_profile(client, student_user):
    headers = _stu(client, student_user)
    _set_profile(client, headers)
    resp = client.get('/api/student/profile', headers=headers)
    assert resp.status_code == 200
    assert resp.json['name'] == 'Alice'
    assert resp.json['branch'] == 'CS'
    assert resp.json['cgpa'] == 8.0
    assert resp.json['email'] == 'stu@test.com'
    assert 'phone' in resp.json
    assert 'year' in resp.json
    assert 'resume_path' in resp.json

def test_invalid_cgpa_rejected(client, student_user):
    resp = client.put('/api/student/profile', headers=_stu(client, student_user),
                      json={'cgpa': 11.0})
    assert resp.status_code == 400

def test_list_eligible_drives(client, student_user, approved_drive):
    headers = _stu(client, student_user)
    _set_profile(client, headers)
    resp = client.get('/api/student/drives', headers=headers)
    assert resp.status_code == 200
    assert any(d['id'] == approved_drive for d in resp.json)

def test_list_drives_includes_ineligible_with_reasons(client, student_user, approved_drive):
    """Test that list_drives returns ineligible drives with reasons."""
    headers = _stu(client, student_user)
    # Set CGPA lower than drive requirement (drive requires 6.0)
    _set_profile(client, headers, cgpa=3.0, branch='CS')
    resp = client.get('/api/student/drives', headers=headers)
    assert resp.status_code == 200
    drives = resp.json
    # Should include the drive even though CGPA is too low
    ineligible_drive = next((d for d in drives if d['id'] == approved_drive), None)
    assert ineligible_drive is not None
    assert ineligible_drive['eligible'] is False
    assert any('CGPA' in reason for reason in ineligible_drive['reasons'])

def test_apply_to_drive(client, student_user, approved_drive):
    headers = _stu(client, student_user)
    _set_profile(client, headers)
    resp = client.post(f'/api/student/drives/{approved_drive}/apply', headers=headers)
    assert resp.status_code == 201
    assert resp.json['ok'] is True

def test_double_apply_rejected(client, student_user, approved_drive):
    headers = _stu(client, student_user)
    _set_profile(client, headers)
    client.post(f'/api/student/drives/{approved_drive}/apply', headers=headers)
    resp = client.post(f'/api/student/drives/{approved_drive}/apply', headers=headers)
    assert resp.status_code == 409
    assert resp.json['code'] == 'DUPLICATE'

def test_cgpa_too_low_rejected(client, student_user, approved_drive):
    headers = _stu(client, student_user)
    client.put('/api/student/profile', headers=headers, json={
        'name': 'Alice', 'phone': '9876543210', 'branch': 'CS', 'year': 3, 'cgpa': 3.0
    })
    resp = client.post(f'/api/student/drives/{approved_drive}/apply', headers=headers)
    assert resp.status_code == 400
    assert resp.json['code'] == 'INELIGIBLE'

def test_dashboard(client, student_user, approved_drive):
    """Test dashboard returns name, branch, counts, and recommended."""
    headers = _stu(client, student_user)
    _set_profile(client, headers)
    # Apply to one drive
    client.post(f'/api/student/drives/{approved_drive}/apply', headers=headers)
    resp = client.get('/api/student/dashboard', headers=headers)
    assert resp.status_code == 200
    assert resp.json['name'] == 'Alice'
    assert resp.json['branch'] == 'CS'
    assert 'counts' in resp.json
    assert resp.json['counts']['applied'] == 1
    assert resp.json['counts']['shortlisted'] == 0
    assert resp.json['counts']['selected'] == 0
    assert resp.json['counts']['rejected'] == 0
    assert 'recommended' in resp.json
    assert isinstance(resp.json['recommended'], list)

def test_application_history(client, student_user, approved_drive):
    """Test applications endpoint returns correct field names."""
    headers = _stu(client, student_user)
    _set_profile(client, headers)
    client.post(f'/api/student/drives/{approved_drive}/apply', headers=headers)
    resp = client.get('/api/student/applications', headers=headers)
    assert resp.status_code == 200
    assert len(resp.json) == 1
    app = resp.json[0]
    assert 'id' in app
    assert 'company_name' in app
    assert 'location' in app
    assert 'role' in app
    assert 'applied_at' in app
    assert 'status' in app

def test_trigger_export(client, student_user):
    headers = _stu(client, student_user)
    _set_profile(client, headers)
    resp = client.post('/api/student/export', headers=headers)
    assert resp.status_code == 202
    assert 'job_id' in resp.json

def test_export_status_idor(client, student_user):
    headers = _stu(client, student_user)
    _set_profile(client, headers)
    export_resp = client.post('/api/student/export', headers=headers)
    job_id = export_resp.json['job_id']
    # Second student tries to poll the job
    stu2 = client.post('/api/auth/register', json={
        'email': 'stu2@test.com', 'password': 'pw1234', 'role': 'student', 'name': 'Bob'
    })
    stu2_headers = {'Authorization': f"Bearer {stu2.json['token']}"}
    resp = client.get(f'/api/student/export/{job_id}', headers=stu2_headers)
    assert resp.status_code == 404
    assert resp.json['code'] == 'NOT_FOUND'

def test_export_status_returns_file_path_and_filename(client, student_user):
    """Test export_status returns file_path and filename on done."""
    headers = _stu(client, student_user)
    _set_profile(client, headers)
    # In eager mode the Celery task runs synchronously
    export_resp = client.post('/api/student/export', headers=headers)
    assert export_resp.status_code == 202
    job_id = export_resp.json['job_id']
    status_resp = client.get(f'/api/student/export/{job_id}', headers=headers)
    assert status_resp.status_code == 200
    assert status_resp.json['status'] == 'done'
    assert 'file_path' in status_resp.json
    assert 'filename' in status_resp.json
    assert status_resp.json['file_path'].startswith('/student/export/')

def test_export_download(client, student_user):
    headers = _stu(client, student_user)
    _set_profile(client, headers)
    # In eager mode the Celery task runs synchronously
    export_resp = client.post('/api/student/export', headers=headers)
    assert export_resp.status_code == 202
    job_id = export_resp.json['job_id']
    status_resp = client.get(f'/api/student/export/{job_id}', headers=headers)
    assert status_resp.status_code == 200
    download_url = status_resp.json['file_path']
    dl_resp = client.get('/api' + download_url, headers=headers)
    assert dl_resp.status_code == 200
    # Flask maps .csv to application/vnd.ms-excel or text/csv depending on config
    assert dl_resp.content_type in ('text/csv', 'application/vnd.ms-excel')

def test_export_download_idor(client, student_user):
    headers = _stu(client, student_user)
    _set_profile(client, headers)
    export_resp = client.post('/api/student/export', headers=headers)
    job_id = export_resp.json['job_id']
    stu2 = client.post('/api/auth/register', json={
        'email': 'stu2b@test.com', 'password': 'pw1234', 'role': 'student', 'name': 'Bob'
    })
    stu2_headers = {'Authorization': f"Bearer {stu2.json['token']}"}
    resp = client.get(f'/api/student/export/{job_id}/download', headers=stu2_headers)
    assert resp.status_code == 404

def test_upload_resume_returns_correct_fields(client, student_user):
    """Test upload_resume returns resume_path and filename."""
    headers = _stu(client, student_user)
    # Create a minimal PDF file (for testing)
    from io import BytesIO
    pdf_data = b'%PDF-1.4\n%fake'
    data = {'resume': (BytesIO(pdf_data), 'test.pdf')}
    resp = client.post('/api/student/profile/resume', headers=headers, data=data, content_type='multipart/form-data')
    assert resp.status_code == 200
    assert 'resume_path' in resp.json
    assert 'filename' in resp.json
    assert resp.json['resume_path'].startswith('uploads/resumes/')

def test_apply_ineligible_uses_single_code(client, approved_drive):
    # student with low CGPA for a drive requiring 6.0
    h = _student_headers(client, cgpa=4.0, branch='CS')
    resp = client.post(f'/api/student/drives/{approved_drive}/apply', headers=h)
    assert resp.status_code == 400
    assert resp.json['code'] == 'INELIGIBLE'
    assert isinstance(resp.json['reasons'], list)

def test_apply_duplicate_uses_duplicate_code(client, approved_drive):
    h = _student_headers(client, cgpa=8.0, branch='CS')
    client.post(f'/api/student/drives/{approved_drive}/apply', headers=h)
    resp = client.post(f'/api/student/drives/{approved_drive}/apply', headers=h)
    assert resp.status_code == 409
    assert resp.json['code'] == 'DUPLICATE'

def test_apply_duplicate_takes_precedence_over_ineligibility(client, approved_drive):
    # eligible apply, then student's CGPA is dropped below the bar; re-apply must still be DUPLICATE
    h = _student_headers(client, cgpa=8.0, branch='CS')
    client.post(f'/api/student/drives/{approved_drive}/apply', headers=h)
    client.put('/api/student/profile', headers=h, json={'cgpa': 1.0})
    resp = client.post(f'/api/student/drives/{approved_drive}/apply', headers=h)
    assert resp.status_code == 409
    assert resp.json['code'] == 'DUPLICATE'

def test_apply_unapproved_drive_uses_not_open(client, approved_company_headers, admin_headers):
    r = client.post('/api/company/drives', headers=approved_company_headers, json={
        'title': 'Pending', 'description': 'd', 'ctc': 5.0, 'location': 'X',
        'eligibility_cgpa': 0.0, 'eligibility_branch': [],
        'application_deadline': str(date.today() + timedelta(days=10))})
    drive_id = r.json['id']  # left in 'pending'
    h = _student_headers(client, cgpa=8.0, branch='CS')
    resp = client.post(f'/api/student/drives/{drive_id}/apply', headers=h)
    assert resp.status_code == 400
    assert resp.json['code'] == 'NOT_OPEN'

def test_null_cgpa_student_can_apply_to_unrestricted_drive(client, approved_company_headers, admin_headers):
    r = client.post('/api/company/drives', headers=approved_company_headers, json={
        'title': 'Open', 'description': 'd', 'ctc': 5.0, 'location': 'X',
        'eligibility_cgpa': 0.0, 'eligibility_branch': [],
        'application_deadline': str(date.today() + timedelta(days=10))})
    drive_id = r.json['id']
    client.put(f'/api/admin/drives/{drive_id}/approve', headers=admin_headers)
    # student that never set a CGPA
    reg = client.post('/api/auth/register', json={
        'email': 'nocgpa@t.com', 'password': 'pw1234', 'role': 'student', 'name': 'NoCgpa'})
    h = {'Authorization': f"Bearer {reg.json['token']}"}
    resp = client.post(f'/api/student/drives/{drive_id}/apply', headers=h)
    assert resp.status_code == 201
    assert resp.json['ok'] is True

def test_put_profile_returns_full_profile(client, student_user):
    h = {'Authorization': f"Bearer {student_user['token']}"}
    resp = client.put('/api/student/profile', headers=h, json={'phone': '999', 'branch': 'CS'})
    assert resp.status_code == 200
    assert resp.json['branch'] == 'CS'
    assert resp.json['phone'] == '999'
    assert 'email' in resp.json

def test_upload_rejects_non_pdf_by_content(client, student_user):
    h = {'Authorization': f"Bearer {student_user['token']}"}
    data = {'resume': (io.BytesIO(b'GIF89a not a pdf'), 'evil.pdf')}
    resp = client.post('/api/student/profile/resume', headers=h,
                       data=data, content_type='multipart/form-data')
    assert resp.status_code == 400
    assert resp.json['code'] == 'INVALID_FILE_TYPE'

def test_upload_accepts_real_pdf(client, student_user):
    h = {'Authorization': f"Bearer {student_user['token']}"}
    data = {'resume': (io.BytesIO(b'%PDF-1.4 minimal'), 'cv.pdf')}
    resp = client.post('/api/student/profile/resume', headers=h,
                       data=data, content_type='multipart/form-data')
    assert resp.status_code == 200
    assert resp.json['filename'].endswith('.pdf')

def test_parse_eligibility_branch_rejects_non_list():
    from routes.student import _parse_eligibility_branch
    assert _parse_eligibility_branch('"CS"') == []      # scalar JSON → []
    assert _parse_eligibility_branch('123') == []        # non-list JSON → []
    assert _parse_eligibility_branch('["CS","IT"]') == ['CS', 'IT']
    assert _parse_eligibility_branch('') == []

def test_applied_eligible_drive_still_marked_eligible(client, approved_drive):
    h = _student_headers(client, cgpa=8.0, branch='CS')
    client.post(f'/api/student/drives/{approved_drive}/apply', headers=h)
    drives = client.get('/api/student/drives', headers=h).json
    d = [x for x in drives if x['id'] == approved_drive][0]
    assert d['applied'] is True
    assert d['eligible'] is True
    assert 'Already applied' in d['reasons']

def test_application_unique_constraint(app):
    import pytest
    from datetime import date, timedelta
    from sqlalchemy.exc import IntegrityError
    from models.models import db, User, StudentProfile, CompanyProfile, PlacementDrive, Application
    with app.app_context():
        u = User(email='uc@x.com', password_hash='x', role='student', is_active=True)
        db.session.add(u); db.session.flush()
        sp = StudentProfile(user_id=u.id, name='U'); db.session.add(sp); db.session.flush()
        cu = User(email='ucc@x.com', password_hash='x', role='company', is_active=True)
        db.session.add(cu); db.session.flush()
        cp = CompanyProfile(user_id=cu.id, company_name='UC', approval_status='approved')
        db.session.add(cp); db.session.flush()
        d = PlacementDrive(company_id=cp.id, title='T', description='d', ctc=5.0,
                           location='X', eligibility_cgpa=0.0, eligibility_branch='[]',
                           application_deadline=date.today() + timedelta(days=5), status='approved')
        db.session.add(d); db.session.flush()
        db.session.add(Application(student_id=sp.id, drive_id=d.id, status='applied'))
        db.session.commit()
        db.session.add(Application(student_id=sp.id, drive_id=d.id, status='applied'))
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

def test_upload_empty_file_field_returns_missing_file(client, student_user):
    h = {'Authorization': f"Bearer {student_user['token']}"}
    data = {'resume': (io.BytesIO(b''), '')}
    resp = client.post('/api/student/profile/resume', headers=h,
                       data=data, content_type='multipart/form-data')
    assert resp.status_code == 400
    assert resp.json['code'] == 'MISSING_FILE'

def test_dashboard_recommended_capped_at_three(client, approved_company_headers, admin_headers):
    for i in range(4):
        r = client.post('/api/company/drives', headers=approved_company_headers, json={
            'title': f'D{i}', 'description': 'd', 'ctc': 5.0, 'location': 'X',
            'eligibility_cgpa': 0.0, 'eligibility_branch': [],
            'application_deadline': str(date.today() + timedelta(days=10))})
        client.put(f"/api/admin/drives/{r.json['id']}/approve", headers=admin_headers)
    reg = client.post('/api/auth/register', json={
        'email': 'dashstu@t.com', 'password': 'pw1234', 'role': 'student', 'name': 'D'})
    h = {'Authorization': f"Bearer {reg.json['token']}"}
    dash = client.get('/api/student/dashboard', headers=h).json
    assert len(dash['recommended']) == 3

def test_update_profile_rejects_nonstring_name(client, student_user):
    h = {'Authorization': f"Bearer {student_user['token']}"}
    resp = client.put('/api/student/profile', headers=h, json={'name': ['Alice']})
    assert resp.status_code == 400
    assert resp.json['code'] == 'INVALID_INPUT'

def test_update_profile_rejects_noninteger_year(client, student_user):
    h = {'Authorization': f"Bearer {student_user['token']}"}
    resp = client.put('/api/student/profile', headers=h, json={'year': 'senior'})
    assert resp.status_code == 400
    assert resp.json['code'] == 'INVALID_INPUT'
