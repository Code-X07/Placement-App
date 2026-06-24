from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
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

def test_monthly_report_runs(app):
    from tasks.report import send_monthly_report
    with app.app_context():
        with patch('tasks.report.mail.send') as m:
            res = send_monthly_report.apply()
            assert res.successful()
            m.assert_called_once()

def test_export_idempotent_on_done_job(app):
    job_id = _make_student_job(app)
    with app.app_context():
        job = db.session.get(ExportJob, job_id)
        job.status = 'done'; job.file_path = 'uploads/exports/original.csv'
        db.session.commit()
    from tasks.export import export_student_data
    with app.app_context():
        export_student_data(job_id)
        job = db.session.get(ExportJob, job_id)
        assert job.status == 'done'
        assert job.file_path == 'uploads/exports/original.csv'   # not overwritten

def test_mail_default_sender_configured(app):
    """Flask-Mail asserts a sender at send time; without MAIL_DEFAULT_SENDER
    every reminder/report send raises and the email is silently dropped."""
    from flask_mail import Message
    with app.app_context():
        assert app.config.get('MAIL_DEFAULT_SENDER')
        m = Message(subject='x', recipients=['a@b.com'], body='y')
        assert m.sender  # resolved from the configured default sender

def test_report_retries_on_db_error_during_counts(app):
    from tasks.report import send_monthly_report
    from models.models import PlacementDrive

    with app.app_context():
        # Patch retry to raise so we can catch it
        with patch.object(send_monthly_report, 'retry',
                          side_effect=RuntimeError('retried')) as mock_retry:
            # Patch only the query method to raise
            def mock_filter(*args, **kwargs):
                mock_qs = MagicMock()
                mock_qs.count.side_effect = Exception('db down')
                return mock_qs

            with patch.object(PlacementDrive, 'query') as query_mock:
                query_mock.filter = mock_filter
                try:
                    send_monthly_report.apply(throw=True)
                except RuntimeError as e:
                    assert str(e) == 'retried'
                assert mock_retry.called  # the DB failure routed through self.retry
