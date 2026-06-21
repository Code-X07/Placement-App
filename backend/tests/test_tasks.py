from unittest.mock import patch
from models.models import db, ExportJob, StudentProfile, User

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
