def test_register_student(client):
    resp = client.post('/api/auth/register', json={
        'email': 'student@test.com', 'password': 'password123',
        'role': 'student', 'name': 'Alice'
    })
    assert resp.status_code == 201
    assert 'token' in resp.json
    user = resp.json['user']
    assert user['id'] > 0
    assert user['email'] == 'student@test.com'
    assert user['role'] == 'student'
    assert user['is_active'] is True
    assert user['name'] == 'Alice'
    assert 'branch' in user
    assert 'cgpa' in user
    assert 'student_id' in user

def test_register_company(client):
    resp = client.post('/api/auth/register', json={
        'email': 'co@test.com', 'password': 'password123',
        'role': 'company', 'name': 'Acme Corp'
    })
    assert resp.status_code == 201
    user = resp.json['user']
    assert user['id'] > 0
    assert user['email'] == 'co@test.com'
    assert user['role'] == 'company'
    assert user['is_active'] is True
    assert user['company_name'] == 'Acme Corp'
    assert user['approval_status'] == 'pending'
    assert 'company_id' in user

def test_register_admin_rejected(client):
    resp = client.post('/api/auth/register', json={
        'email': 'admin2@test.com', 'password': 'pw', 'role': 'admin'
    })
    assert resp.status_code == 400
    assert resp.json['code'] == 'ADMIN_FORBIDDEN'

def test_register_duplicate_email(client):
    data = {'email': 'dup@test.com', 'password': 'pw', 'role': 'student', 'name': 'Bob'}
    client.post('/api/auth/register', json=data)
    resp = client.post('/api/auth/register', json=data)
    assert resp.status_code == 409

def test_login_success(client):
    client.post('/api/auth/register', json={
        'email': 'log@test.com', 'password': 'pw123', 'role': 'student', 'name': 'C'
    })
    resp = client.post('/api/auth/login', json={
        'email': 'log@test.com', 'password': 'pw123'
    })
    assert resp.status_code == 200
    assert 'token' in resp.json
    assert resp.json['role'] == 'student'
    user = resp.json['user']
    assert user['email'] == 'log@test.com'
    assert user['role'] == 'student'
    assert user['is_active'] is True
    assert user['name'] == 'C'
    assert 'student_id' in user

def test_login_bad_password(client):
    client.post('/api/auth/register', json={
        'email': 'log2@test.com', 'password': 'pw123', 'role': 'student', 'name': 'D'
    })
    resp = client.post('/api/auth/login', json={
        'email': 'log2@test.com', 'password': 'wrong'
    })
    assert resp.status_code == 401

def test_admin_seed_login(client):
    resp = client.post('/api/auth/login', json={
        'email': 'admin@ppa.com', 'password': 'admin123'
    })
    assert resp.status_code == 200
    assert resp.json['role'] == 'admin'
    user = resp.json['user']
    assert user['email'] == 'admin@ppa.com'
    assert user['role'] == 'admin'
    assert user['is_active'] is True
    assert user['name'] == 'Administrator'

def test_me_returns_fresh_user(client):
    client.post('/api/auth/register', json={
        'email': 'me@test.com', 'password': 'pw123', 'role': 'student', 'name': 'E'
    })
    login = client.post('/api/auth/login', json={
        'email': 'me@test.com', 'password': 'pw123'
    })
    headers = {'Authorization': f"Bearer {login.json['token']}"}
    resp = client.get('/api/auth/me', headers=headers)
    assert resp.status_code == 200
    user = resp.json
    assert user['email'] == 'me@test.com'
    assert user['role'] == 'student'
    assert user['is_active'] is True
    assert user['name'] == 'E'
    assert 'student_id' in user

def test_register_student_has_roll(client):
    resp = client.post('/api/auth/register', json={
        'email': 'roll@test.com', 'password': 'pw', 'role': 'student', 'name': 'RollTest'
    })
    assert resp.status_code == 201
    user = resp.json['user']
    assert 'student_id' in user
    assert user.get('roll') is not None  # roll must be present after register

def test_register_company_name_maps_to_company_name(client):
    resp = client.post('/api/auth/register', json={
        'email': 'nametest@co.com', 'password': 'pw', 'role': 'company', 'name': 'TechCorp Ltd'
    })
    assert resp.status_code == 201
    user = resp.json['user']
    assert user['company_name'] == 'TechCorp Ltd'

def test_register_company_with_address(client):
    resp = client.post('/api/auth/register', json={
        'email': 'addr@co.com', 'password': 'pw', 'role': 'company',
        'name': 'AddrCorp', 'address': '123 Main St'
    })
    assert resp.status_code == 201
    assert resp.json['user']['company_name'] == 'AddrCorp'

def test_cors_preflight(client):
    resp = client.options('/api/auth/login',
                          headers={'Origin': 'http://localhost:5173',
                                   'Access-Control-Request-Method': 'POST'})
    assert 'Access-Control-Allow-Origin' in resp.headers
    assert resp.headers.get('Access-Control-Allow-Origin') == 'http://localhost:5173'
