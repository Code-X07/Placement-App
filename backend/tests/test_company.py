from datetime import date, timedelta

def _drive_payload(**over):
    base = {'title': 'X', 'description': 'Y', 'ctc': 5.0, 'location': 'Z',
            'eligibility_cgpa': 6.0, 'eligibility_branch': ['CS'],
            'application_deadline': str(date.today() + timedelta(days=10))}
    base.update(over)
    return base

def test_pending_company_can_view_dashboard(client, company_user):
    headers = {'Authorization': f"Bearer {company_user['token']}"}
    resp = client.get('/api/company/dashboard', headers=headers)
    assert resp.status_code == 200
    assert resp.json['approval_status'] == 'pending'

def test_pending_company_cannot_create_drive(client, company_user):
    headers = {'Authorization': f"Bearer {company_user['token']}"}
    resp = client.post('/api/company/drives', headers=headers, json={
        'title': 'X', 'description': 'Y', 'ctc': 5.0, 'location': 'Z',
        'eligibility_cgpa': 6.0, 'eligibility_branch': ['CS'],
        'application_deadline': str(date.today() + timedelta(days=10))
    })
    assert resp.status_code == 403
    assert resp.json['code'] == 'NOT_APPROVED'

def test_unapproved_company_blocked(client, company_user):
    headers = {'Authorization': f"Bearer {company_user['token']}"}
    resp = client.post('/api/company/drives', headers=headers, json={
        'title': 'D', 'description': 'x', 'ctc': 10.0, 'location': 'Delhi',
        'eligibility_cgpa': 6.0, 'eligibility_branch': ['CS'],
        'application_deadline': str(date.today() + timedelta(days=10))
    })
    assert resp.status_code == 403

def test_create_drive(client, approved_company_headers):
    resp = client.post('/api/company/drives', headers=approved_company_headers, json={
        'title': 'Backend Dev', 'description': 'Python role', 'ctc': 15.0,
        'location': 'Hyderabad', 'eligibility_cgpa': 6.5,
        'eligibility_branch': ['CS', 'IT', 'ECE'],
        'application_deadline': str(date.today() + timedelta(days=20))
    })
    assert resp.status_code == 201
    assert resp.json['id'] is not None
    assert resp.json['status'] == 'pending'

def test_drive_past_deadline_rejected(client, approved_company_headers):
    resp = client.post('/api/company/drives', headers=approved_company_headers, json={
        'title': 'Old', 'description': 'x', 'ctc': 5.0, 'location': 'X',
        'eligibility_cgpa': 5.0, 'eligibility_branch': ['CS'],
        'application_deadline': str(date.today() - timedelta(days=1))
    })
    assert resp.status_code == 400

def test_view_own_drive_applications(client, approved_company_headers, approved_drive):
    resp = client.get(f'/api/company/drives/{approved_drive}/applications',
                      headers=approved_company_headers)
    assert resp.status_code == 200
    assert 'drive_title' in resp.json
    assert 'company_name' in resp.json
    assert 'applicants' in resp.json
    assert isinstance(resp.json['applicants'], list)

def test_idor_other_company_drive(client, approved_company_headers, admin_headers, app):
    # Register and approve a second company
    resp2 = client.post('/api/auth/register', json={
        'email': 'co2@test.com', 'password': 'pw1234', 'role': 'company', 'name': 'Corp2'
    })
    with app.app_context():
        from models.models import CompanyProfile
        cp2 = CompanyProfile.query.filter_by(company_name='Corp2').first()
        client.put(f'/api/admin/companies/{cp2.id}/approve', headers=admin_headers)
    co2_headers = {'Authorization': f"Bearer {resp2.json['token']}"}
    # Corp2 creates a drive
    d2 = client.post('/api/company/drives', headers=co2_headers, json={
        'title': 'Drive2', 'description': 'x', 'ctc': 5.0, 'location': 'x',
        'eligibility_cgpa': 5.0, 'eligibility_branch': ['CS'],
        'application_deadline': str(date.today() + timedelta(days=10))
    })
    drive2_id = d2.json['id']
    # Company 1 tries to read Corp2's drive applications
    resp = client.get(f'/api/company/drives/{drive2_id}/applications',
                      headers=approved_company_headers)
    assert resp.status_code == 403

def test_update_application_status(client, approved_company_headers, approved_drive,
                                   student_user, app):
    stu_headers = {'Authorization': f"Bearer {student_user['token']}"}
    client.put('/api/student/profile', headers=stu_headers, json={
        'name': 'Stu', 'phone': '9876543210', 'branch': 'CS', 'year': 3, 'cgpa': 8.0
    })
    apply_resp = client.post(f'/api/student/drives/{approved_drive}/apply',
                             headers=stu_headers)
    assert apply_resp.status_code == 201
    with app.app_context():
        from models.models import Application, StudentProfile
        stu_profile = StudentProfile.query.filter_by(name='Stu').first()
        app_obj = Application.query.filter_by(student_id=stu_profile.id, drive_id=approved_drive).first()
        app_id = app_obj.id
    resp = client.put(f'/api/company/applications/{app_id}/status',
                      headers=approved_company_headers, json={'status': 'shortlisted'})
    assert resp.status_code == 200
    assert resp.json['id'] == app_id
    assert resp.json['status'] == 'shortlisted'

def test_offer_letter_only_for_selected(client, approved_company_headers, approved_drive,
                                        student_user, app):
    stu_headers = {'Authorization': f"Bearer {student_user['token']}"}
    client.put('/api/student/profile', headers=stu_headers, json={
        'name': 'Stu', 'phone': '9876543210', 'branch': 'CS', 'year': 3, 'cgpa': 8.0
    })
    apply_resp = client.post(f'/api/student/drives/{approved_drive}/apply',
                             headers=stu_headers)
    with app.app_context():
        from models.models import Application, StudentProfile
        stu_profile = StudentProfile.query.filter_by(name='Stu').first()
        app_obj = Application.query.filter_by(student_id=stu_profile.id, drive_id=approved_drive).first()
        app_id = app_obj.id
    # Status is 'applied', not 'selected' — should 400
    resp = client.get(f'/api/company/applications/{app_id}/offer-letter',
                      headers=approved_company_headers)
    assert resp.status_code == 400
    # Promote to selected
    client.put(f'/api/company/applications/{app_id}/status',
               headers=approved_company_headers, json={'status': 'selected'})
    resp = client.get(f'/api/company/applications/{app_id}/offer-letter',
                      headers=approved_company_headers)
    assert resp.status_code == 200
    json_data = resp.json
    assert 'company' in json_data
    assert 'name' in json_data['company']
    assert 'address' in json_data['company']
    assert 'date' in json_data
    assert 'student_name' in json_data
    assert json_data['student_name'] == 'Stu'
    assert 'position' in json_data
    assert 'department' in json_data
    assert 'ctc' in json_data
    assert 'location' in json_data
    assert 'intro' in json_data
    assert 'body' in json_data
    assert 'joining_date' not in json_data

def test_create_drive_branch_must_be_list(client, approved_company_headers):
    resp = client.post('/api/company/drives', headers=approved_company_headers, json={
        'title': 'Bad Branch', 'description': 'x', 'ctc': 10.0, 'location': 'x',
        'eligibility_cgpa': 6.0,
        'eligibility_branch': 'CS',
        'application_deadline': str(date.today() + timedelta(days=10))
    })
    assert resp.status_code == 400
    assert resp.json['code'] == 'INVALID_BRANCH_FORMAT'

def test_resume_own_applicant(client, approved_company_headers, approved_drive,
                              student_user, app):
    stu_headers = {'Authorization': f"Bearer {student_user['token']}"}
    # Create a minimal student profile
    client.put('/api/student/profile', headers=stu_headers, json={
        'name': 'Stu', 'phone': '9876543210', 'branch': 'CS', 'year': 3, 'cgpa': 8.0
    })
    # Mock a resume file
    with app.app_context():
        import os
        from models.models import StudentProfile
        stu = StudentProfile.query.filter_by(name='Stu').first()
        resume_dir = os.path.join(app.root_path, 'uploads', 'resumes')
        os.makedirs(resume_dir, exist_ok=True)
        # Create a dummy PDF file
        resume_path = os.path.join(resume_dir, 'test_resume.pdf')
        with open(resume_path, 'wb') as f:
            f.write(b'%PDF-1.4\n%EOF')
        stu.resume_path = 'test_resume.pdf'
        from models.models import db
        db.session.commit()

    # Apply to drive
    apply_resp = client.post(f'/api/student/drives/{approved_drive}/apply',
                             headers=stu_headers)
    with app.app_context():
        from models.models import Application, StudentProfile
        stu_profile = StudentProfile.query.filter_by(name='Stu').first()
        app_obj = Application.query.filter_by(student_id=stu_profile.id, drive_id=approved_drive).first()
        app_id = app_obj.id

    # Company views resume
    resp = client.get(f'/api/company/applications/{app_id}/resume',
                      headers=approved_company_headers)
    assert resp.status_code == 200
    assert resp.content_type == 'application/pdf'
    assert b'%PDF' in resp.data

def test_resume_other_company_forbidden(client, approved_company_headers, approved_drive,
                                        student_user, admin_headers, app):
    # Register and approve a second company
    resp2 = client.post('/api/auth/register', json={
        'email': 'co2@test.com', 'password': 'pw1234', 'role': 'company', 'name': 'Corp2'
    })
    with app.app_context():
        from models.models import CompanyProfile
        cp2 = CompanyProfile.query.filter_by(company_name='Corp2').first()
        client.put(f'/api/admin/companies/{cp2.id}/approve', headers=admin_headers)
    co2_headers = {'Authorization': f"Bearer {resp2.json['token']}"}

    # Student applies to drive owned by first company
    stu_headers = {'Authorization': f"Bearer {student_user['token']}"}
    client.put('/api/student/profile', headers=stu_headers, json={
        'name': 'Stu', 'phone': '9876543210', 'branch': 'CS', 'year': 3, 'cgpa': 8.0
    })
    apply_resp = client.post(f'/api/student/drives/{approved_drive}/apply',
                             headers=stu_headers)
    with app.app_context():
        from models.models import Application, StudentProfile
        stu_profile = StudentProfile.query.filter_by(name='Stu').first()
        app_obj = Application.query.filter_by(student_id=stu_profile.id, drive_id=approved_drive).first()
        app_id = app_obj.id

    # Second company tries to access resume (IDOR)
    resp = client.get(f'/api/company/applications/{app_id}/resume',
                      headers=co2_headers)
    assert resp.status_code == 403

def test_resume_no_resume_404(client, approved_company_headers, approved_drive, student_user, app):
    stu_headers = {'Authorization': f"Bearer {student_user['token']}"}
    client.put('/api/student/profile', headers=stu_headers, json={
        'name': 'Stu', 'phone': '9876543210', 'branch': 'CS', 'year': 3, 'cgpa': 8.0
    })
    apply_resp = client.post(f'/api/student/drives/{approved_drive}/apply',
                             headers=stu_headers)
    with app.app_context():
        from models.models import Application, StudentProfile
        stu_profile = StudentProfile.query.filter_by(name='Stu').first()
        app_obj = Application.query.filter_by(student_id=stu_profile.id, drive_id=approved_drive).first()
        app_id = app_obj.id

    # Try to download resume when none exists
    resp = client.get(f'/api/company/applications/{app_id}/resume',
                      headers=approved_company_headers)
    assert resp.status_code == 404
    assert resp.json['code'] == 'NO_RESUME'

def test_create_drive_not_approved_has_code_and_human_error(client, company_user):
    h = {'Authorization': f"Bearer {company_user['token']}"}
    resp = client.post('/api/company/drives', headers=h, json={
        'title': 'X', 'description': 'Y', 'ctc': 5.0, 'location': 'Z',
        'eligibility_cgpa': 6.0, 'eligibility_branch': ['CS'],
        'application_deadline': str(date.today() + timedelta(days=10))})
    assert resp.status_code == 403
    assert resp.json['code'] == 'NOT_APPROVED'
    assert resp.json['error'] != 'NOT_APPROVED'  # human-readable, not the enum

def test_company_profile_update_returns_profile(client, approved_company_headers):
    resp = client.put('/api/company/profile', headers=approved_company_headers,
                      json={'website': 'https://x.io'})
    assert resp.status_code == 200
    assert resp.json['website'] == 'https://x.io'
    assert 'company_name' in resp.json

def test_pending_company_can_update_profile(client, company_user):
    headers = {'Authorization': f"Bearer {company_user['token']}"}
    resp = client.put('/api/company/profile', headers=headers, json={
        'company_name': 'Apex Updated', 'hr_contact': 'hr@apex.com',
        'website': 'https://apex.com', 'address': '123 Main St'
    })
    assert resp.status_code == 200
    assert resp.json['company_name'] == 'Apex Updated'

def test_create_drive_rejects_negative_ctc(client, approved_company_headers):
    resp = client.post('/api/company/drives', headers=approved_company_headers,
                       json=_drive_payload(ctc=-5.0))
    assert resp.status_code == 400
    assert resp.json['code'] == 'INVALID_NUMBER'

def test_create_drive_rejects_out_of_range_cgpa(client, approved_company_headers):
    resp = client.post('/api/company/drives', headers=approved_company_headers,
                       json=_drive_payload(eligibility_cgpa=50.0))
    assert resp.status_code == 400
    assert resp.json['code'] == 'INVALID_NUMBER'

def test_create_drive_rejects_nonstring_branch(client, approved_company_headers):
    resp = client.post('/api/company/drives', headers=approved_company_headers,
                       json=_drive_payload(eligibility_branch=[1, 2]))
    assert resp.status_code == 400
    assert resp.json['code'] == 'INVALID_BRANCH_FORMAT'

def test_create_drive_rejects_blank_title(client, approved_company_headers):
    resp = client.post('/api/company/drives', headers=approved_company_headers,
                       json=_drive_payload(title='   '))
    assert resp.status_code == 400
    assert resp.json['code'] == 'MISSING_FIELDS'
