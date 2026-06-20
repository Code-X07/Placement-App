#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
seed_demo.py — Idempotent data seeding script for Task 7.
Recreates mock's edge states for e2e verification and demo/grading.

Run: cd ppa/backend && python seed_demo.py

Upserts by email (safe to re-run).
"""
import sys
import io
from datetime import datetime, date, timedelta
from app import create_app, bcrypt
from models.models import db, User, StudentProfile, CompanyProfile, PlacementDrive, Application

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def seed():
    app = create_app()
    with app.app_context():
        print("=== PPA Demo Data Seeding ===\n")

        # 1. Pending (unapproved) company: Apex Solutions
        apex_email = 'apex@apex.com'
        apex_user = User.query.filter_by(email=apex_email).first()
        if not apex_user:
            apex_user = User(
                email=apex_email,
                password_hash=bcrypt.generate_password_hash('password123').decode('utf-8'),
                role='company',
                is_active=True,
            )
            db.session.add(apex_user)
            db.session.flush()
            apex_profile = CompanyProfile(
                user_id=apex_user.id,
                company_name='Apex Solutions',
                approval_status='pending',
            )
            db.session.add(apex_profile)
            db.session.commit()
            print("[CREATED] Apex Solutions (pending) — apex@apex.com / password123")
        else:
            print("[SKIPPED] Apex Solutions already exists")

        # 2. Approved company: TechNova with drives
        technova_email = 'technova@technova.com'
        technova_user = User.query.filter_by(email=technova_email).first()
        if not technova_user:
            technova_user = User(
                email=technova_email,
                password_hash=bcrypt.generate_password_hash('password123').decode('utf-8'),
                role='company',
                is_active=True,
            )
            db.session.add(technova_user)
            db.session.flush()
            technova_profile = CompanyProfile(
                user_id=technova_user.id,
                company_name='TechNova',
                approval_status='approved',
                website='https://technova.com',
                address='123 Tech Street, Bangalore',
            )
            db.session.add(technova_profile)
            db.session.flush()

            # Drive 1: Approved — Software Engineer (eligible for Alex)
            drive1 = PlacementDrive(
                company_id=technova_profile.id,
                title='Software Engineer',
                description='Core backend and frontend roles',
                ctc=12.0,
                location='Bangalore',
                eligibility_cgpa=7.0,
                eligibility_branch='["CS", "IT"]',  # JSON array string
                application_deadline=date.today() + timedelta(days=30),
                status='approved',
                department='Engineering',
            )
            db.session.add(drive1)

            # Drive 2: Pending — Data Analyst (not visible to students)
            drive2 = PlacementDrive(
                company_id=technova_profile.id,
                title='Data Analyst',
                description='Analytics and reporting roles',
                ctc=8.0,
                location='Mumbai',
                eligibility_cgpa=6.0,
                eligibility_branch='[]',  # No branch restriction
                application_deadline=date.today() + timedelta(days=20),
                status='pending',
                department='Analytics',
            )
            db.session.add(drive2)

            # Drive 3: Approved but CGPA-restricted — Quant Researcher (ineligible for Alex)
            drive3 = PlacementDrive(
                company_id=technova_profile.id,
                title='Quant Researcher',
                description='Quantitative analysis and research',
                ctc=20.0,
                location='Delhi',
                eligibility_cgpa=9.0,  # Alex has 8.7, so ineligible
                eligibility_branch='["CS"]',  # Only CS
                application_deadline=date.today() + timedelta(days=25),
                status='approved',
                department='Finance',
            )
            db.session.add(drive3)

            db.session.commit()
            print("[CREATED] TechNova (approved) — technova@technova.com / password123")
            print("  - Drive: Software Engineer (approved, deadline +30d)")
            print("  - Drive: Data Analyst (pending, deadline +20d)")
            print("  - Drive: Quant Researcher (approved, CGPA 9.0, deadline +25d)")
        else:
            print("[SKIPPED] TechNova already exists")

        # 3. Student: Alex Kumar with existing application
        alex_email = 'alex@university.edu'
        alex_user = User.query.filter_by(email=alex_email).first()
        if not alex_user:
            alex_user = User(
                email=alex_email,
                password_hash=bcrypt.generate_password_hash('password123').decode('utf-8'),
                role='student',
                is_active=True,
            )
            db.session.add(alex_user)
            db.session.flush()
            alex_profile = StudentProfile(
                user_id=alex_user.id,
                name='Alex Kumar',
                branch='CS',
                cgpa=8.7,
                year=3,
                phone='9876543210',
            )
            db.session.add(alex_profile)
            db.session.flush()
            alex_profile.roll = f"STU{alex_profile.id:05d}"

            # Apply to Software Engineer drive (if TechNova exists)
            technova_profile = CompanyProfile.query.filter_by(company_name='TechNova').first()
            if technova_profile:
                software_engineer_drive = PlacementDrive.query.filter_by(
                    company_id=technova_profile.id,
                    title='Software Engineer'
                ).first()
                if software_engineer_drive:
                    app = Application(
                        student_id=alex_profile.id,
                        drive_id=software_engineer_drive.id,
                        status='applied',
                    )
                    db.session.add(app)

            db.session.commit()
            print("[CREATED] Alex Kumar (student) — alex@university.edu / password123")
            print("  - Branch: CS, CGPA: 8.7, Year: 3")
            print("  - Applied to: Software Engineer drive")
        else:
            print("[SKIPPED] Alex Kumar already exists")

        # 4. Deactivated student: Inactive User
        inactive_email = 'inactive@university.edu'
        inactive_user = User.query.filter_by(email=inactive_email).first()
        if not inactive_user:
            inactive_user = User(
                email=inactive_email,
                password_hash=bcrypt.generate_password_hash('password123').decode('utf-8'),
                role='student',
                is_active=False,  # Key: deactivated
            )
            db.session.add(inactive_user)
            db.session.flush()
            inactive_profile = StudentProfile(
                user_id=inactive_user.id,
                name='Inactive User',
                branch='IT',
                cgpa=7.5,
                year=2,
            )
            db.session.add(inactive_profile)
            db.session.flush()
            inactive_profile.roll = f"STU{inactive_profile.id:05d}"

            db.session.commit()
            print("[CREATED] Inactive User (deactivated) — inactive@university.edu / password123")
        else:
            print("[SKIPPED] Inactive User already exists")

        print("\n=== Seeding Complete ===")
        print("\nDemo Credentials:")
        print("  Admin:      admin@ppa.com / admin123")
        print("  Company 1:  apex@apex.com / password123 (pending)")
        print("  Company 2:  technova@technova.com / password123 (approved)")
        print("  Student 1:  alex@university.edu / password123 (active, applied to Software Engineer)")
        print("  Student 2:  inactive@university.edu / password123 (deactivated)")

if __name__ == '__main__':
    try:
        seed()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
