from app import create_app, celery
from config import TestConfig

def test_beat_schedule_is_loaded():
    create_app(TestConfig)
    schedule = celery.conf.beat_schedule
    assert 'daily-reminders' in schedule
    assert 'monthly-report' in schedule
    assert schedule['daily-reminders']['task'] == 'tasks.reminders.send_deadline_reminders'
    assert schedule['monthly-report']['task'] == 'tasks.report.send_monthly_report'
