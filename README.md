# EduHire – Placement Portal

EduHire is a campus placement portal I built as a university project. It brings students, companies and the placement admin onto one site, so the whole hiring process, from posting a job drive to sending an offer letter, happens in one place.

## What it does

There are three kinds of users, and each one gets their own dashboard.

**Students**
- Fill in their profile (branch, CGPA, year) and upload a resume
- Browse approved placement drives and apply to the ones they're eligible for
- Track each application as it moves from *applied* to *shortlisted* to *selected* (or *rejected*)
- Export their application history as a CSV file

**Companies**
- Register and wait for the admin to approve them
- Create placement drives with eligibility rules and a deadline
- Review applicants, shortlist or select them, and generate offer letters for selected students

**Admin**
- Approve or reject companies and their drives
- View and manage students, and deactivate accounts if needed
- Search across students, companies and drives from one place

There are also a few jobs that run in the background:
- A reminder email goes out every day at 8 AM to students who applied to a drive that closes the next day
- A monthly placement report is emailed to the admin on the 1st of each month
- Student CSV exports are built in the background, so the page doesn't hang

## Tech stack

- **Backend:** Flask, SQLAlchemy (SQLite), JWT login, Flask-Mail
- **Frontend:** Vue 2 with Vue Router and Vuex, styled with Bootstrap 5 (loaded from a CDN, so there's no build step)
- **Background jobs:** Celery with Redis
- **Caching:** Redis (optional, and the app still works without it)
- **Tests:** pytest

## Project layout

```
backend/
  app.py            # creates the Flask app and serves the frontend
  config.py         # settings and the Celery schedule
  models/           # database tables
  routes/           # API endpoints for auth, admin, company and student
  tasks/            # Celery jobs (reminders, monthly report, CSV export)
  celery_worker.py  # entry point for the Celery worker
  seed_demo.py      # fills the database with some demo data
  tests/
frontend/
  templates/        # index.html
  static/           # Vue components, CSS and the API helper
```

## Running it locally

You'll need Python 3.10+ and, for the background jobs, a running Redis server.

1. **Install the dependencies**

   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\activate        # on macOS/Linux: source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Set your environment variables.** `backend/.env.example` lists all of them. The app reads them from your shell and doesn't load a `.env` file on its own, so set them in your terminal. For local testing the defaults are fine. To send real emails, set `MAIL_USERNAME` and `MAIL_PASSWORD`, for example with a Gmail app password.

3. **Start the app**

   ```bash
   python app.py
   ```

   Open http://localhost:5000. The database is created on first run, along with an admin account (`admin@ppa.com` / `admin123` unless you've set `ADMIN_EMAIL` and `ADMIN_PASSWORD`).

4. **(Optional) Load demo data**

   ```bash
   python seed_demo.py
   ```

   This adds a few ready-made accounts, all with the password `password123`:

   | Role | Email |
   |---|---|
   | Company (approved) | technova@technova.com |
   | Company (pending approval) | apex@apex.com |
   | Student | alex@university.edu |
   | Student (deactivated) | inactive@university.edu |

5. **(Optional) Start the background jobs.** With Redis running, open two more terminals in `backend/`:

   ```bash
   celery -A celery_worker worker --pool=solo -l warning   # --pool=solo is needed on Windows
   celery -A celery_worker beat -l warning
   ```

## Running the tests

```bash
cd backend
pytest
```

The tests use an in-memory database and don't need Redis or a mail server.
