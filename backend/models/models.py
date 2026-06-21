from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import TypeDecorator
from sqlalchemy.types import DateTime as DbDateTime

db = SQLAlchemy()

def _utcnow():
    return datetime.now(timezone.utc)

class TZDateTime(TypeDecorator):
    """DateTime type that ensures timezone-aware datetimes."""
    impl = DbDateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value

    def process_result_value(self, value, dialect):
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)      # admin|company|student
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(TZDateTime, default=_utcnow)

    student_profile = db.relationship('StudentProfile', backref='user',
                                      uselist=False, cascade='all, delete-orphan')
    company_profile = db.relationship('CompanyProfile', backref='user',
                                      uselist=False, cascade='all, delete-orphan')

class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    branch = db.Column(db.String(50))
    year = db.Column(db.Integer)
    cgpa = db.Column(db.Float)
    resume_path = db.Column(db.String(255))
    roll = db.Column(db.String(30), unique=True)

    applications = db.relationship('Application', backref='student',
                                   cascade='all, delete-orphan')
    export_jobs = db.relationship('ExportJob', backref='student',
                                  cascade='all, delete-orphan')

class CompanyProfile(db.Model):
    __tablename__ = 'company_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    hr_contact = db.Column(db.String(120))
    website = db.Column(db.String(200))
    approval_status = db.Column(db.String(20), default='pending', nullable=False)
    address = db.Column(db.Text)

    __table_args__ = (
        db.CheckConstraint("approval_status IN ('pending','approved','rejected')",
                           name='ck_company_approval_status'),
    )

    drives = db.relationship('PlacementDrive', backref='company',
                             cascade='all, delete-orphan')

class PlacementDrive(db.Model):
    __tablename__ = 'placement_drives'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company_profiles.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    ctc = db.Column(db.Float)
    location = db.Column(db.String(100))
    eligibility_cgpa = db.Column(db.Float, default=0.0)
    eligibility_branch = db.Column(db.Text)  # JSON array string e.g. '["CS","IT"]'
    application_deadline = db.Column(db.Date)
    status = db.Column(db.String(20), default='pending', nullable=False)
    created_at = db.Column(TZDateTime, default=_utcnow)
    department = db.Column(db.String(100))

    __table_args__ = (
        db.CheckConstraint("status IN ('pending','approved','rejected')",
                           name='ck_drive_status'),
    )

    applications = db.relationship('Application', backref='drive',
                                   cascade='all, delete-orphan')

class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drives.id'), nullable=False)
    applied_at = db.Column(TZDateTime, default=_utcnow)
    status = db.Column(db.String(20), default='applied', nullable=False)

    __table_args__ = (
        db.UniqueConstraint('student_id', 'drive_id'),
        db.CheckConstraint("status IN ('applied','shortlisted','selected','rejected')",
                           name='ck_application_status'),
    )

class ExportJob(db.Model):
    __tablename__ = 'export_jobs'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    celery_task_id = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending|done|failed
    file_path = db.Column(db.String(255))
    created_at = db.Column(TZDateTime, default=_utcnow)

    __table_args__ = (
        db.CheckConstraint("status IN ('pending','done','failed')",
                           name='ck_exportjob_status'),
    )
