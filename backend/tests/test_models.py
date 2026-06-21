import json
import pytest
from models.models import db, User, StudentProfile, CompanyProfile, PlacementDrive, Application, ExportJob

def test_user_create(app):
    with app.app_context():
        u = User(email='x@test.com', password_hash='h', role='student', is_active=True)
        db.session.add(u)
        db.session.commit()
        assert u.id is not None

def test_student_profile_fk(app):
    with app.app_context():
        u = User(email='s@test.com', password_hash='h', role='student', is_active=True)
        db.session.add(u)
        db.session.commit()
        sp = StudentProfile(user_id=u.id, name='Alice', phone='1234567890',
                            branch='CS', year=3, cgpa=8.5)
        db.session.add(sp)
        db.session.commit()
        assert sp.user_id == u.id

def test_company_profile_default_status(app):
    with app.app_context():
        u = User(email='c@test.com', password_hash='h', role='company', is_active=True)
        db.session.add(u)
        db.session.commit()
        cp = CompanyProfile(user_id=u.id, company_name='Acme', approval_status='pending')
        db.session.add(cp)
        db.session.commit()
        assert cp.approval_status == 'pending'

def test_application_unique_constraint(app):
    from sqlalchemy.exc import IntegrityError
    from datetime import date, timedelta
    with app.app_context():
        u1 = User(email='s2@t.com', password_hash='h', role='student', is_active=True)
        u2 = User(email='c2@t.com', password_hash='h', role='company', is_active=True)
        db.session.add_all([u1, u2])
        db.session.commit()
        sp = StudentProfile(user_id=u1.id, name='Bob', phone='9999999999',
                            branch='IT', year=2, cgpa=7.0)
        cp = CompanyProfile(user_id=u2.id, company_name='Corp', approval_status='approved')
        db.session.add_all([sp, cp])
        db.session.commit()
        drive = PlacementDrive(
            company_id=cp.id, title='SWE', description='test', ctc=10.0,
            location='Mumbai', eligibility_cgpa=6.0,
            eligibility_branch=json.dumps(['CS', 'IT']),
            application_deadline=date.today() + timedelta(days=30),
            status='approved'
        )
        db.session.add(drive)
        db.session.commit()
        a1 = Application(student_id=sp.id, drive_id=drive.id, status='applied')
        db.session.add(a1)
        db.session.commit()
        a2 = Application(student_id=sp.id, drive_id=drive.id, status='applied')
        db.session.add(a2)
        with pytest.raises(IntegrityError):
            db.session.commit()

def test_user_created_at_is_timezone_aware(app):
    with app.app_context():
        u = User(email='tz@t.com', password_hash='x', role='student', is_active=True)
        db.session.add(u); db.session.commit()
        assert u.created_at is not None
        assert u.created_at.tzinfo is not None
