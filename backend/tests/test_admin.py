def test_admin_dashboard(client, admin_headers, student_user, company_user):
    resp = client.get('/api/admin/dashboard', headers=admin_headers)
    assert resp.status_code == 200
    for key in ('students', 'companies', 'drives', 'applications'):
        assert key in resp.json

def test_non_admin_blocked(client, student_user):
    headers = {'Authorization': f"Bearer {student_user['token']}"}
    resp = client.get('/api/admin/dashboard', headers=headers)
    assert resp.status_code == 403

def test_list_companies(client, admin_headers, company_user):
    resp = client.get('/api/admin/companies', headers=admin_headers)
    assert resp.status_code == 200
    assert any(c['company_name'] == 'Corp' for c in resp.json)

def test_list_companies_all_filter(client, admin_headers, company_user):
    resp = client.get('/api/admin/companies?approval_status=all', headers=admin_headers)
    assert resp.status_code == 200
    assert any(c['company_name'] == 'Corp' for c in resp.json)

def test_approve_company(client, admin_headers, company_user, app):
    with app.app_context():
        from models.models import CompanyProfile
        cp = CompanyProfile.query.filter_by(company_name='Corp').first()
        resp = client.put(f'/api/admin/companies/{cp.id}/approve', headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json['id'] == cp.id
        assert resp.json['approval_status'] == 'approved'
        from models.models import db
        db.session.expire_all()
        assert CompanyProfile.query.get(cp.id).approval_status == 'approved'

def test_reject_company(client, admin_headers, company_user, app):
    with app.app_context():
        from models.models import CompanyProfile
        cp = CompanyProfile.query.filter_by(company_name='Corp').first()
        resp = client.put(f'/api/admin/companies/{cp.id}/reject', headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json['id'] == cp.id
        assert resp.json['approval_status'] == 'rejected'

def test_blacklist_company(client, admin_headers, company_user, app):
    with app.app_context():
        from models.models import CompanyProfile, User
        cp = CompanyProfile.query.filter_by(company_name='Corp').first()
        resp = client.put(f'/api/admin/companies/{cp.id}/blacklist', headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json['id'] == cp.id
        assert resp.json['approval_status'] == 'rejected'
        from models.models import db
        db.session.expire_all()
        u = User.query.get(cp.user_id)
        assert u.is_active == False

def test_list_drives(client, admin_headers, approved_drive):
    resp = client.get('/api/admin/drives', headers=admin_headers)
    assert resp.status_code == 200
    assert any(d['title'] == 'Test Drive' for d in resp.json)
    assert any('company_name' in d for d in resp.json)
    assert any('application_deadline' in d for d in resp.json)

def test_approve_drive(client, admin_headers, approved_drive, app):
    with app.app_context():
        from models.models import PlacementDrive
        drive = PlacementDrive.query.get(approved_drive)
        drive.status = 'pending'
        from models.models import db
        db.session.commit()
    resp = client.put(f'/api/admin/drives/{approved_drive}/approve', headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json['id'] == approved_drive
    assert resp.json['status'] == 'approved'

def test_reject_drive(client, admin_headers, approved_drive):
    resp = client.put(f'/api/admin/drives/{approved_drive}/reject', headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json['id'] == approved_drive
    assert resp.json['status'] == 'rejected'

def test_list_students_has_roll(client, admin_headers, student_user, app):
    with app.app_context():
        from models.models import StudentProfile
        sp = StudentProfile.query.filter_by(name='Stu').first()
        if sp:
            sp.roll = '2024001'
            from models.models import db
            db.session.commit()
    resp = client.get('/api/admin/students', headers=admin_headers)
    assert resp.status_code == 200
    assert any('roll' in s for s in resp.json)

def test_deactivate_student(client, admin_headers, student_user, app):
    with app.app_context():
        from models.models import User
        u = User.query.filter_by(email='stu@test.com').first()
        resp = client.put(f'/api/admin/students/{u.id}/deactivate', headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json['id'] == u.id
        assert resp.json['is_active'] == False
        from models.models import db
        db.session.expire_all()
        assert User.query.get(u.id).is_active == False

def test_deactivate_non_student_blocked(client, admin_headers, company_user, app):
    with app.app_context():
        from models.models import User
        u = User.query.filter_by(email='co@test.com').first()
        resp = client.put(f'/api/admin/students/{u.id}/deactivate', headers=admin_headers)
        assert resp.status_code == 400
        assert resp.json['code'] == 'NOT_STUDENT'

def test_search_student(client, admin_headers, student_user):
    resp = client.get('/api/admin/search?q=Stu&type=student', headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json['type'] == 'student'
    assert 'results' in resp.json
    assert isinstance(resp.json['results'], list)
    if resp.json['results']:
        result = resp.json['results'][0]
        assert 'id' in result and 'name' in result and 'email' in result and 'branch' in result

def test_search_company(client, admin_headers, company_user):
    resp = client.get('/api/admin/search?q=Corp&type=company', headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json['type'] == 'company'
    assert 'results' in resp.json
    assert isinstance(resp.json['results'], list)
    if resp.json['results']:
        result = resp.json['results'][0]
        assert 'id' in result and 'name' in result and 'email' in result and 'status' in result

def test_search_empty_query(client, admin_headers):
    resp = client.get('/api/admin/search?q=&type=student', headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json['type'] == 'student'
    assert resp.json['results'] == []

def test_blacklisted_company_drives_hidden(client, admin_headers,
                                           approved_company_headers, approved_drive,
                                           student_user, app):
    stu_headers = {'Authorization': f"Bearer {student_user['token']}"}
    client.put('/api/student/profile', headers=stu_headers, json={
        'name': 'Alice', 'phone': '9876543210', 'branch': 'CS', 'year': 3, 'cgpa': 8.0
    })
    # Confirm drive visible before blacklist
    before = client.get('/api/student/drives', headers=stu_headers)
    assert any(d['id'] == approved_drive for d in before.json)

    with app.app_context():
        from models.models import CompanyProfile
        cp = CompanyProfile.query.filter_by(company_name='ApprovedCorp').first()
        client.put(f'/api/admin/companies/{cp.id}/blacklist', headers=admin_headers)

    after = client.get('/api/student/drives', headers=stu_headers)
    assert all(d['id'] != approved_drive for d in after.json)


def test_rejected_company_drives_hidden(client, admin_headers,
                                        approved_company_headers, approved_drive,
                                        student_user, app):
    stu_headers = {'Authorization': f"Bearer {student_user['token']}"}
    client.put('/api/student/profile', headers=stu_headers, json={
        'name': 'Alice', 'phone': '9876543210', 'branch': 'CS', 'year': 3, 'cgpa': 8.0
    })
    with app.app_context():
        from models.models import CompanyProfile
        cp = CompanyProfile.query.filter_by(company_name='ApprovedCorp').first()
        client.put(f'/api/admin/companies/{cp.id}/reject', headers=admin_headers)

    after = client.get('/api/student/drives', headers=stu_headers)
    assert all(d['id'] != approved_drive for d in after.json)

def test_list_companies_omits_user_email_field(client, admin_headers, company_user):
    resp = client.get('/api/admin/companies', headers=admin_headers)
    assert resp.status_code == 200
    assert all('email' not in c for c in resp.json)

def test_search_escapes_like_wildcards(client, admin_headers, company_user):
    # a literal '%' query must not match everything
    resp = client.get('/api/admin/search?type=student&q=%25', headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json['results'] == []

def test_approve_company_after_blacklist_restores_login(client, admin_headers):
    reg = client.post('/api/auth/register', json={
        'email': 'reco@x.com', 'password': 'pw1234', 'role': 'company', 'name': 'RecoCo'})
    assert reg.status_code == 201
    companies = client.get('/api/admin/companies', headers=admin_headers).json
    cid = [c['id'] for c in companies if c['company_name'] == 'RecoCo'][0]
    # blacklist deactivates the user
    client.put(f'/api/admin/companies/{cid}/blacklist', headers=admin_headers)
    blocked = client.post('/api/auth/login', json={'email': 'reco@x.com', 'password': 'pw1234'})
    assert blocked.status_code == 403
    assert blocked.json['code'] == 'INACTIVE'
    # approve must restore is_active
    client.put(f'/api/admin/companies/{cid}/approve', headers=admin_headers)
    ok = client.post('/api/auth/login', json={'email': 'reco@x.com', 'password': 'pw1234'})
    assert ok.status_code == 200
