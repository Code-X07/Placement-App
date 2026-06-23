from datetime import datetime, timedelta, timezone
import logging
from flask_mail import Message
from app import celery, mail
from models.models import PlacementDrive, Application

logger = logging.getLogger(__name__)

@celery.task(name='tasks.reminders.send_deadline_reminders', bind=True, max_retries=3)
def send_deadline_reminders(self):
    tomorrow = datetime.now(timezone.utc).date() + timedelta(days=1)
    try:
        drives = PlacementDrive.query.filter_by(
            application_deadline=tomorrow, status='approved'
        ).all()
    except Exception as e:
        # transient infra (DB/broker) — safe to retry the whole task
        raise self.retry(exc=e, countdown=300)
    failures = 0
    for drive in drives:
        if not drive.company:
            continue
        applicants = Application.query.filter_by(
            drive_id=drive.id, status='applied'
        ).all()
        for app in applicants:
            if not (app.student and app.student.user and app.student.user.email):
                continue
            msg = Message(
                subject=f'Reminder: {drive.title} deadline is tomorrow',
                recipients=[app.student.user.email],
                body=(
                    f'Dear {app.student.name},\n\n'
                    f'The application deadline for {drive.title} at '
                    f'{drive.company.company_name} is tomorrow ({tomorrow}).\n\n'
                    f'Regards,\nPPA Team'
                ),
            )
            try:
                mail.send(msg)
            except Exception as e:
                # per-recipient failure must NOT restart the batch (would duplicate
                # already-sent emails); log and move on.
                failures += 1
                logger.error(f'Failed to send reminder to {app.student.user.email}: {e}')
    if failures:
        logger.warning(f'{failures} reminder email(s) failed this run')
