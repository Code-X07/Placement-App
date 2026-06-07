from datetime import date, timedelta

def _stu(client, student_user):
    return {'Authorization': f"Bearer {student_user['token']}"}

def _set_profile(client, headers):
    client.put('/api/student/profile', headers=headers, json={
        'name': 'Alice', 'phone': '9876543210', 'branch': 'CS', 'year': 3, 'cgpa': 8.0
    })

def test_update_profile(client, student_user):
    resp = client.put('/api/student/profile', headers=_stu(client, student_user), json={
        'name': 'Alice', 'phone': '9876543210', 'branch': 'CS', 'year': 3, 'cgpa': 8.0
    })
    assert resp.status_code == 200

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

def test_apply_to_drive(client, student_user, approved_drive):
    headers = _stu(client, student_user)
    _set_profile(client, headers)
    resp = client.post(f'/api/student/drives/{approved_drive}/apply', headers=headers)
    assert resp.status_code == 201
    assert 'application_id' in resp.json

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

def test_application_history(client, student_user, approved_drive):
    headers = _stu(client, student_user)
    _set_profile(client, headers)
    client.post(f'/api/student/drives/{approved_drive}/apply', headers=headers)
    resp = client.get('/api/student/applications', headers=headers)
    assert resp.status_code == 200
    assert len(resp.json) == 1

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
        'email': 'stu2@test.com', 'password': 'pw', 'role': 'student', 'name': 'Bob'
    })
    stu2_headers = {'Authorization': f"Bearer {stu2.json['token']}"}
    resp = client.get(f'/api/student/export/{job_id}', headers=stu2_headers)
    assert resp.status_code == 403
    assert resp.json['code'] == 'FORBIDDEN'

def test_export_download(client, student_user):
    headers = _stu(client, student_user)
    _set_profile(client, headers)
    # In eager mode the Celery task runs synchronously
    export_resp = client.post('/api/student/export', headers=headers)
    assert export_resp.status_code == 202
    job_id = export_resp.json['job_id']
    status_resp = client.get(f'/api/student/export/{job_id}', headers=headers)
    assert status_resp.status_code == 200
    assert 'download_url' in status_resp.json
    download_url = status_resp.json['download_url']
    dl_resp = client.get(download_url, headers=headers)
    assert dl_resp.status_code == 200
    # Flask maps .csv to application/vnd.ms-excel or text/csv depending on config
    assert dl_resp.content_type in ('text/csv', 'application/vnd.ms-excel')

def test_export_download_idor(client, student_user):
    headers = _stu(client, student_user)
    _set_profile(client, headers)
    export_resp = client.post('/api/student/export', headers=headers)
    job_id = export_resp.json['job_id']
    stu2 = client.post('/api/auth/register', json={
        'email': 'stu2b@test.com', 'password': 'pw', 'role': 'student', 'name': 'Bob'
    })
    stu2_headers = {'Authorization': f"Bearer {stu2.json['token']}"}
    resp = client.get(f'/api/student/export/{job_id}/download', headers=stu2_headers)
    assert resp.status_code == 403
