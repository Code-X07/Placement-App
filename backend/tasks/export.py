import os
import csv
from datetime import datetime, timezone
from app import celery
from models.models import db, ExportJob, Application

@celery.task(name='tasks.export.export_student_data')
def export_student_data(job_id):
    job = db.session.get(ExportJob, job_id)
    if not job:
        return
    if job.status in ('done', 'failed'):
        return
    try:
        apps = Application.query.filter_by(student_id=job.student_id).all()
        exports_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', 'uploads', 'exports'))
        os.makedirs(exports_dir, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
        filename = f'{job.student_id}_{timestamp}.csv'
        filepath = os.path.join(exports_dir, filename)
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Company', 'Drive Title', 'Application Status', 'Date'])
            for a in apps:
                writer.writerow([
                    a.drive.company.company_name,
                    a.drive.title,
                    a.status,
                    str(a.applied_at),
                ])
        job.status = 'done'
        job.file_path = f'uploads/exports/{filename}'
        db.session.commit()
    except Exception:
        db.session.rollback()
        job = db.session.get(ExportJob, job_id)  # re-fetch after rollback
        if job:
            job.status = 'failed'
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
        raise
