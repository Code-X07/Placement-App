from datetime import date, timedelta

def _stu(client, student_user):
    return {'Authorization': f"Bearer {student_user['token']}"}

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

def test_cgpa_too_low_rejected(client, student_user, approved_drive):
    headers = _stu(client, student_user)
    client.put('/api/student/profile', headers=headers, json={
        'name': 'Alice', 'phone': '9876543210', 'branch': 'CS', 'year': 3, 'cgpa': 3.0
    })
    resp = client.post(f'/api/student/drives/{approved_drive}/apply', headers=headers)
    assert resp.status_code == 400
    assert resp.json['code'] == 'INELIGIBLE_CGPA'

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
    assert resp.status_code == 403
    assert resp.json['code'] == 'FORBIDDEN'

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
    assert resp.status_code == 403

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
