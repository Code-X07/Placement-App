from datetime import date, timedelta

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
    assert resp.json['title'] == 'Backend Dev'
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
    assert isinstance(resp.json, list)

def test_idor_other_company_drive(client, approved_company_headers, admin_headers, app):
    # Register and approve a second company
    resp2 = client.post('/api/auth/register', json={
        'email': 'co2@test.com', 'password': 'pw', 'role': 'company', 'name': 'Corp2'
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
    app_id = apply_resp.json['application_id']
    resp = client.put(f'/api/company/applications/{app_id}/status',
                      headers=approved_company_headers, json={'status': 'shortlisted'})
    assert resp.status_code == 200

def test_offer_letter_only_for_selected(client, approved_company_headers, approved_drive,
                                        student_user, app):
    stu_headers = {'Authorization': f"Bearer {student_user['token']}"}
    client.put('/api/student/profile', headers=stu_headers, json={
        'name': 'Stu', 'phone': '9876543210', 'branch': 'CS', 'year': 3, 'cgpa': 8.0
    })
    apply_resp = client.post(f'/api/student/drives/{approved_drive}/apply',
                             headers=stu_headers)
    app_id = apply_resp.json['application_id']
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
    assert b'Offer Letter' in resp.data

def test_create_drive_branch_must_be_list(client, approved_company_headers):
    resp = client.post('/api/company/drives', headers=approved_company_headers, json={
        'title': 'Bad Branch', 'description': 'x', 'ctc': 10.0, 'location': 'x',
        'eligibility_cgpa': 6.0,
        'eligibility_branch': 'CS',
        'application_deadline': str(date.today() + timedelta(days=10))
    })
    assert resp.status_code == 400
    assert resp.json['code'] == 'INVALID_BRANCH_FORMAT'

def test_offer_letter_escapes_xss(client, approved_company_headers, approved_drive,
                                  student_user, app):
    stu_headers = {'Authorization': f"Bearer {student_user['token']}"}
    client.put('/api/student/profile', headers=stu_headers, json={
        'name': '<script>alert(1)</script>', 'phone': '9876543210',
        'branch': 'CS', 'year': 3, 'cgpa': 8.0
    })
    apply_resp = client.post(f'/api/student/drives/{approved_drive}/apply',
                             headers=stu_headers)
    app_id = apply_resp.json['application_id']
    client.put(f'/api/company/applications/{app_id}/status',
               headers=approved_company_headers, json={'status': 'selected'})
    resp = client.get(f'/api/company/applications/{app_id}/offer-letter',
                      headers=approved_company_headers)
    assert resp.status_code == 200
    assert b'<script>' not in resp.data
    assert b'&lt;script&gt;' in resp.data
