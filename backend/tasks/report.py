from datetime import date, datetime, timedelta, timezone
import logging
from flask import render_template_string, current_app
from flask_mail import Message
from app import celery, mail
from models.models import PlacementDrive, Application

logger = logging.getLogger(__name__)

_REPORT_TMPL = """<html><body>
<h2>Monthly Placement Activity Report — {{ month }}</h2>
<ul>
  <li>Drives conducted: {{ drives }}</li>
  <li>Total applications: {{ total }}</li>
  <li>Shortlisted: {{ shortlisted }}</li>
  <li>Selected: {{ selected }}</li>
</ul>
</body></html>"""

@celery.task(name='tasks.report.send_monthly_report', bind=True, max_retries=3)
def send_monthly_report(self):
    today = datetime.now(timezone.utc).date()
    first = today.replace(day=1)
    end = first - timedelta(days=1)
    start = end.replace(day=1)

    drives = PlacementDrive.query.filter(
        PlacementDrive.created_at >= start,
        PlacementDrive.created_at < first,
    ).count()

    base_q = Application.query.filter(
        Application.applied_at >= start,
        Application.applied_at < first,
    )
    total = base_q.count()
    shortlisted = base_q.filter(Application.status == 'shortlisted').count()
    selected = base_q.filter(Application.status == 'selected').count()

    html = render_template_string(_REPORT_TMPL,
        month=end.strftime('%B %Y'),
        drives=drives, total=total,
        shortlisted=shortlisted, selected=selected)

    msg = Message(
        subject=f'Monthly Placement Report — {end.strftime("%B %Y")}',
        recipients=[current_app.config['ADMIN_EMAIL']],
        html=html,
    )
    try:
        mail.send(msg)
        logger.info(f'Monthly report sent for {end.strftime("%B %Y")}')
    except Exception as e:
        logger.error(f'Failed to send monthly report: {e}')
        raise self.retry(exc=e, countdown=300)
