from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch
from models.models import db, ExportJob, StudentProfile, User, CompanyProfile, PlacementDrive, Application

def _make_student_job(app):
    with app.app_context():
        u = User(email='t@t.com', password_hash='x', role='student', is_active=True)
        db.session.add(u); db.session.flush()
        sp = StudentProfile(user_id=u.id, name='T'); db.session.add(sp); db.session.flush()
        job = ExportJob(student_id=sp.id, status='pending'); db.session.add(job)
        db.session.commit()
        return job.id

def test_export_failure_marks_job_failed(app):
    job_id = _make_student_job(app)
    from tasks.export import export_student_data
    with app.app_context():
        with patch('tasks.export.csv.writer', side_effect=RuntimeError('boom')):
            try:
                export_student_data(job_id)
            except RuntimeError:
                pass
        job = db.session.get(ExportJob, job_id)
        assert job.status == 'failed'

def _drive_with_two_applicants_due_tomorrow(app):
    with app.app_context():
        cu = User(email='remco@x.com', password_hash='x', role='company', is_active=True)
        db.session.add(cu); db.session.flush()
        cp = CompanyProfile(user_id=cu.id, company_name='RemCo', approval_status='approved')
        db.session.add(cp); db.session.flush()
        d = PlacementDrive(company_id=cp.id, title='T', description='d', ctc=5.0,
                           location='X', eligibility_cgpa=0.0, eligibility_branch='[]',
                           application_deadline=datetime.now(timezone.utc).date() + timedelta(days=1), status='approved')
        db.session.add(d); db.session.flush()
        for i in range(2):
            u = User(email=f'rem{i}@x.com', password_hash='x', role='student', is_active=True)
            db.session.add(u); db.session.flush()
            sp = StudentProfile(user_id=u.id, name=f'S{i}'); db.session.add(sp); db.session.flush()
            db.session.add(Application(student_id=sp.id, drive_id=d.id, status='applied'))
        db.session.commit()

def test_reminder_continues_after_single_failure(app):
    _drive_with_two_applicants_due_tomorrow(app)
    from tasks.reminders import send_deadline_reminders
    with app.app_context():
        with patch('tasks.reminders.mail.send', side_effect=[Exception('smtp'), None]) as m:
            res = send_deadline_reminders.apply()
            assert res.successful()        # task did not blow up / retry
            assert m.call_count == 2       # both recipients attempted, none skipped
