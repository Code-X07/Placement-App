from datetime import date, timedelta
from flask_mail import Message
from app import celery, mail
from models.models import PlacementDrive, Application

@celery.task
def send_deadline_reminders():
    tomorrow = date.today() + timedelta(days=1)
    drives = PlacementDrive.query.filter_by(
        application_deadline=tomorrow, status='approved'
    ).all()
    for drive in drives:
        applicants = Application.query.filter_by(
            drive_id=drive.id, status='applied'
        ).all()
        for app in applicants:
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
            mail.send(msg)
