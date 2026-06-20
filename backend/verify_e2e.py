#!/usr/bin/env python
"""
verify_e2e.py — Programmatic verification of §7 checklist items.
Tests the live backend API for correctness and edge cases.

Run: cd ppa/backend && python verify_e2e.py
"""
import os
import sys
import subprocess
import time
import json
import tempfile
import requests
from datetime import date, timedelta

BASE_URL = 'http://localhost:5000/api'
SEED_SCRIPT = os.path.join(os.path.dirname(__file__), 'seed_demo.py')

# Demo credentials
ADMIN_CREDS = {'email': 'admin@ppa.com', 'password': 'admin123'}
PENDING_COMPANY_CREDS = {'email': 'apex@apex.com', 'password': 'password123'}
APPROVED_COMPANY_CREDS = {'email': 'technova@technova.com', 'password': 'password123'}
STUDENT_CREDS = {'email': 'alex@university.edu', 'password': 'password123'}
INACTIVE_STUDENT_CREDS = {'email': 'inactive@university.edu', 'password': 'password123'}

class Tester:
    def __init__(self):
        self.results = []
        self.admin_token = None
        self.company_token = None
        self.approved_company_token = None
        self.student_token = None
        self.inactive_token = None
        self.flask_process = None

    def log_result(self, name, passed, details=""):
        status = "✓ PASS" if passed else "✗ FAIL"
        msg = f"{status}: {name}"
        if details:
            msg += f" — {details}"
        print(msg)
        self.results.append((name, passed, details))

    def login(self, email, password):
        """Get JWT token for a user."""
        try:
            resp = requests.post(f'{BASE_URL}/auth/login', json={
                'email': email,
                'password': password
            })
            if resp.status_code == 200:
                return resp.json().get('token')
            return None
        except Exception as e:
            print(f"Login error: {e}")
            return None

    def request_with_token(self, method, endpoint, token=None, json_data=None, files=None):
        """Make HTTP request with optional JWT token."""
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        url = f'{BASE_URL}{endpoint}'
        try:
            if method == 'GET':
                resp = requests.get(url, headers=headers)
            elif method == 'POST':
                resp = requests.post(url, headers=headers, json=json_data, files=files)
            elif method == 'PUT':
                resp = requests.put(url, headers=headers, json=json_data)
            else:
                return None
            return resp
        except Exception as e:
            print(f"Request error: {e}")
            return None

    def seed_data(self):
        """Run seed_demo.py to populate test data."""
        print("\n[Setup] Seeding demo data...")
        try:
            result = subprocess.run(
                [sys.executable, SEED_SCRIPT],
                cwd=os.path.dirname(SEED_SCRIPT),
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                print(result.stdout)
                return True
            else:
                print(f"Seed failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"Seed error: {e}")
            return False

    def start_flask(self):
        """Start Flask app in background."""
        print("[Setup] Starting Flask...")
        try:
            env = os.environ.copy()
            env['FLASK_ENV'] = 'development'
            env['DATABASE_URL'] = 'sqlite:///ppa.db'
            self.flask_process = subprocess.Popen(
                [sys.executable, '-c', '''
import os
os.chdir(r"''' + os.path.dirname(__file__) + '''")
from app import create_app
app = create_app()
app.run(port=5000, debug=False, use_reloader=False)
'''],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            # Wait for Flask to start
            time.sleep(3)
            # Test connectivity
            for i in range(10):
                try:
                    resp = requests.get(f'{BASE_URL}/auth/me')
                    if resp.status_code in (200, 401):
                        print("[Setup] Flask started successfully")
                        return True
                except:
                    time.sleep(1)
            print("[Setup] Flask failed to start")
            return False
        except Exception as e:
            print(f"Flask start error: {e}")
            return False

    def stop_flask(self):
        """Stop Flask process."""
        if self.flask_process:
            print("[Cleanup] Stopping Flask...")
            self.flask_process.terminate()
            try:
                self.flask_process.wait(timeout=5)
            except:
                self.flask_process.kill()

    def test_auth_tokens(self):
        """Get tokens for all test users."""
        print("\n=== Auth Setup ===")
        self.admin_token = self.login(ADMIN_CREDS['email'], ADMIN_CREDS['password'])
        self.company_token = self.login(PENDING_COMPANY_CREDS['email'], PENDING_COMPANY_CREDS['password'])
        self.approved_company_token = self.login(APPROVED_COMPANY_CREDS['email'], APPROVED_COMPANY_CREDS['password'])
        self.student_token = self.login(STUDENT_CREDS['email'], STUDENT_CREDS['password'])
        self.inactive_token = self.login(INACTIVE_STUDENT_CREDS['email'], INACTIVE_STUDENT_CREDS['password'])

        self.log_result("Admin login", bool(self.admin_token))
        self.log_result("Pending company login", bool(self.company_token))
        self.log_result("Approved company login", bool(self.approved_company_token))
        self.log_result("Student login", bool(self.student_token))
        self.log_result("Inactive student login", bool(self.inactive_token))

    def test_pending_company_gate(self):
        """Pending company cannot access dashboard."""
        print("\n=== Pending Company Gate ===")
        if not self.company_token:
            self.log_result("Pending company gate", False, "No token")
            return

        resp = self.request_with_token('GET', '/company/dashboard', self.company_token)
        # Should be 403 NOT_APPROVED
        passed = resp and resp.status_code == 403
        self.log_result("Pending company dashboard (should be 403)", passed,
                       f"Status: {resp.status_code if resp else 'No response'}")

    def test_auth_edges(self):
        """Test auth edge cases."""
        print("\n=== Auth Edges ===")

        # Expired/blank token
        resp = self.request_with_token('GET', '/student/dashboard', token='invalid_token')
        passed = resp and resp.status_code == 401
        self.log_result("Invalid token → 401", passed, f"Status: {resp.status_code if resp else 'No'}")

        # No token
        resp = self.request_with_token('GET', '/student/dashboard', token=None)
        passed = resp and resp.status_code == 401
        self.log_result("No token → 401", passed, f"Status: {resp.status_code if resp else 'No'}")

    def test_wrong_role_guard(self):
        """Student token hits admin endpoint."""
        print("\n=== Role Guard ===")
        if not self.student_token:
            self.log_result("Role guard (student → admin)", False, "No student token")
            return

        resp = self.request_with_token('GET', '/admin/companies', self.student_token)
        # Should be 403 WRONG_ROLE
        passed = resp and resp.status_code == 403
        self.log_result("Student token hits /admin/companies → 403", passed,
                       f"Status: {resp.status_code if resp else 'No'}")

    def test_blacklist_lockout(self):
        """Blacklist a company and verify lockout."""
        print("\n=== Blacklist Lockout ===")
        if not self.admin_token or not self.company_token:
            self.log_result("Blacklist lockout", False, "Missing tokens")
            return

        # Get pending company ID
        resp = self.request_with_token('GET', '/admin/companies', self.admin_token)
        if not resp or resp.status_code != 200:
            self.log_result("Blacklist: fetch companies", False)
            return

        companies = resp.json()
        pending_company = next((c for c in companies if c['email'] == PENDING_COMPANY_CREDS['email']), None)
        if not pending_company:
            self.log_result("Blacklist: find pending company", False)
            return

        # Blacklist it
        resp = self.request_with_token('PUT', f'/admin/companies/{pending_company["id"]}/blacklist', self.admin_token)
        if not resp or resp.status_code != 200:
            self.log_result("Blacklist: blacklist call", False)
            return
        self.log_result("Blacklist: company blacklisted", True)

        # Now pending company's next request should be rejected
        # Re-login to get a new token (old one might still work briefly)
        new_pending_token = self.login(PENDING_COMPANY_CREDS['email'], PENDING_COMPANY_CREDS['password'])
        if new_pending_token:
            # New login after deactivation should fail
            resp = self.request_with_token('GET', '/company/dashboard', new_pending_token)
            passed = resp and resp.status_code == 403
            self.log_result("Blacklisted company: next request → 403", passed,
                           f"Status: {resp.status_code if resp else 'No'}")
        else:
            self.log_result("Blacklisted company: login blocked", True)

    def test_student_drives_and_eligibility(self):
        """Get student's drive list and check eligibility."""
        print("\n=== Student Drives & Eligibility ===")
        if not self.student_token:
            self.log_result("Student drives", False, "No token")
            return

        resp = self.request_with_token('GET', '/student/drives', self.student_token)
        passed = resp and resp.status_code == 200
        self.log_result("Student /drives endpoint", passed, f"Status: {resp.status_code if resp else 'No'}")

        if not (resp and resp.status_code == 200):
            return

        drives = resp.json()
        self.log_result("Student drives: response is list", isinstance(drives, list))

        # Check for Software Engineer (should be eligible and applied)
        software_eng = next((d for d in drives if d.get('title') == 'Software Engineer'), None)
        if software_eng:
            applied = software_eng.get('applied', False)
            eligible = software_eng.get('eligible', False)
            self.log_result("Software Engineer: marked as applied", applied)
            self.log_result("Software Engineer: marked as eligible (has applied)",
                           eligible or applied, "Either eligible=true or applied=true is OK")

        # Check for Quant Researcher (should be ineligible, with reason)
        quant_res = next((d for d in drives if d.get('title') == 'Quant Researcher'), None)
        if quant_res:
            eligible = quant_res.get('eligible', False)
            reasons = quant_res.get('reasons', [])
            self.log_result("Quant Researcher: marked as ineligible", not eligible)
            self.log_result("Quant Researcher: has ineligibility reasons", len(reasons) > 0,
                           f"Reasons: {reasons}")

    def test_apply_errors(self):
        """Test application errors."""
        print("\n=== Apply Errors ===")
        if not self.student_token:
            self.log_result("Apply errors", False, "No token")
            return

        # Get Software Engineer drive ID
        resp = self.request_with_token('GET', '/student/drives', self.student_token)
        if not (resp and resp.status_code == 200):
            self.log_result("Apply: fetch drives", False)
            return

        drives = resp.json()
        software_eng = next((d for d in drives if d.get('title') == 'Software Engineer'), None)
        if not software_eng:
            self.log_result("Apply: find Software Engineer drive", False)
            return

        drive_id = software_eng['id']

        # Re-apply (should be 409 already applied or eligible)
        resp = self.request_with_token('POST', f'/student/drives/{drive_id}/apply', self.student_token)
        passed = resp and resp.status_code == 409
        self.log_result("Re-apply to same drive → 409", passed,
                       f"Status: {resp.status_code if resp else 'No'}")

        # Try to apply to ineligible drive (Quant Researcher)
        quant_res = next((d for d in drives if d.get('title') == 'Quant Researcher'), None)
        if quant_res:
            resp = self.request_with_token('POST', f'/student/drives/{quant_res["id"]}/apply', self.student_token)
            passed = resp and resp.status_code == 400
            self.log_result("Apply to ineligible drive → 400", passed,
                           f"Status: {resp.status_code if resp else 'No'}")

    def test_offer_letter(self):
        """Test offer letter endpoint."""
        print("\n=== Offer Letter ===")
        if not self.approved_company_token or not self.student_token:
            self.log_result("Offer letter", False, "Missing tokens")
            return

        # Company: get applications for Software Engineer drive
        resp = self.request_with_token('GET', '/admin/drives', self.admin_token)
        if not (resp and resp.status_code == 200):
            self.log_result("Offer letter: fetch drives", False)
            return

        drives = resp.json()
        software_eng = next((d for d in drives if d.get('title') == 'Software Engineer' and d.get('company_name') == 'TechNova'), None)
        if not software_eng:
            self.log_result("Offer letter: find Software Engineer", False)
            return

        resp = self.request_with_token('GET', f'/company/drives/{software_eng["id"]}/applications', self.approved_company_token)
        if not (resp and resp.status_code == 200):
            self.log_result("Offer letter: fetch applications", False)
            return

        apps = resp.json().get('applicants', [])
        if not apps:
            self.log_result("Offer letter: no applications found", False)
            return

        app_id = apps[0]['id']

        # Update status to selected
        resp = self.request_with_token('PUT', f'/company/applications/{app_id}/status',
                                      self.approved_company_token, {'status': 'selected'})
        passed = resp and resp.status_code == 200
        self.log_result("Company: mark applicant as selected", passed)

        # Get offer letter (should succeed now)
        resp = self.request_with_token('GET', f'/company/applications/{app_id}/offer-letter', self.approved_company_token)
        passed = resp and resp.status_code == 200
        self.log_result("Offer letter for selected applicant → 200", passed,
                       f"Status: {resp.status_code if resp else 'No'}")

        if resp and resp.status_code == 200:
            letter = resp.json()
            required_keys = ['company', 'date', 'student_name', 'position', 'ctc', 'location']
            has_keys = all(k in letter for k in required_keys)
            self.log_result("Offer letter has required keys", has_keys)

        # Try to get offer letter for non-selected applicant
        if len(apps) > 1:
            app2_id = apps[1]['id']
            resp = self.request_with_token('GET', f'/company/applications/{app2_id}/offer-letter', self.approved_company_token)
            passed = resp and resp.status_code == 400
            self.log_result("Offer letter for non-selected → 400", passed)

    def test_resume_upload(self):
        """Test resume upload."""
        print("\n=== Resume Upload ===")
        if not self.student_token:
            self.log_result("Resume upload", False, "No token")
            return

        # Create a test PDF
        pdf_content = b'%PDF-1.4\n%fake pdf'
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(pdf_content)
            pdf_path = f.name

        try:
            with open(pdf_path, 'rb') as f:
                files = {'resume': ('test.pdf', f, 'application/pdf')}
                headers = {'Authorization': f'Bearer {self.student_token}'}
                resp = requests.post(f'{BASE_URL}/student/profile/resume', files=files, headers=headers)

            passed = resp and resp.status_code == 200
            self.log_result("Resume upload (PDF) → 200", passed, f"Status: {resp.status_code if resp else 'No'}")

            if resp and resp.status_code == 200:
                data = resp.json()
                has_path = 'resume_path' in data
                self.log_result("Resume response has resume_path", has_path)

            # Try non-PDF (should fail)
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
                f.write(b'not a pdf')
                txt_path = f.name

            try:
                with open(txt_path, 'rb') as f:
                    files = {'resume': ('test.txt', f, 'text/plain')}
                    headers = {'Authorization': f'Bearer {self.student_token}'}
                    resp = requests.post(f'{BASE_URL}/student/profile/resume', files=files, headers=headers)

                passed = resp and resp.status_code == 400
                self.log_result("Resume upload (non-PDF) → 400", passed)
            finally:
                os.unlink(txt_path)
        finally:
            os.unlink(pdf_path)

    def test_empty_states(self):
        """Test empty states."""
        print("\n=== Empty States ===")
        if not self.admin_token:
            self.log_result("Empty states", False, "No admin token")
            return

        # Search with no match
        resp = self.request_with_token('GET', '/admin/search?type=student&q=NOMATCHXYZ123', self.admin_token)
        passed = resp and resp.status_code == 200
        self.log_result("Admin search: no match query returns 200", passed)

        if resp and resp.status_code == 200:
            data = resp.json()
            is_empty = data.get('results', []) == []
            self.log_result("Admin search: no-match results is empty list", is_empty)

    def test_deactivated_student(self):
        """Test deactivated student cannot login."""
        print("\n=== Deactivated Student ===")
        # Inactive student's login should work (account is deactivated but auth succeeds)
        # But any API call should fail
        if self.inactive_token:
            resp = self.request_with_token('GET', '/student/dashboard', self.inactive_token)
            passed = resp and resp.status_code == 403
            self.log_result("Deactivated student: dashboard access → 403", passed,
                           f"Status: {resp.status_code if resp else 'No'}")
        else:
            self.log_result("Deactivated student: login failed (expected)", True)

    def test_company_approve_reject(self):
        """Test admin approve/reject company."""
        print("\n=== Company Approve/Reject ===")
        if not self.admin_token:
            self.log_result("Company approve/reject", False, "No admin token")
            return

        # Get companies
        resp = self.request_with_token('GET', '/admin/companies', self.admin_token)
        if not (resp and resp.status_code == 200):
            self.log_result("Company approve: fetch companies", False)
            return

        companies = resp.json()
        pending = next((c for c in companies if c.get('approval_status') == 'pending'), None)
        if pending:
            # Approve it
            resp = self.request_with_token('PUT', f'/admin/companies/{pending["id"]}/approve', self.admin_token)
            passed = resp and resp.status_code == 200
            self.log_result("Admin: approve company → 200", passed)

    def test_drive_approve_reject(self):
        """Test admin approve/reject drive."""
        print("\n=== Drive Approve/Reject ===")
        if not self.admin_token:
            self.log_result("Drive approve/reject", False, "No admin token")
            return

        # Get drives
        resp = self.request_with_token('GET', '/admin/drives', self.admin_token)
        if not (resp and resp.status_code == 200):
            self.log_result("Drive approve: fetch drives", False)
            return

        drives = resp.json()
        pending_drive = next((d for d in drives if d.get('status') == 'pending'), None)
        if pending_drive:
            # Approve it
            resp = self.request_with_token('PUT', f'/admin/drives/{pending_drive["id"]}/approve', self.admin_token)
            passed = resp and resp.status_code == 200
            self.log_result("Admin: approve drive → 200", passed)

    def run(self):
        """Run all tests."""
        print("\n" + "=" * 60)
        print("TASK 7: END-TO-END VERIFICATION")
        print("=" * 60)

        # Setup
        if not self.seed_data():
            print("ERROR: Failed to seed data")
            return False

        if not self.start_flask():
            print("ERROR: Failed to start Flask")
            return False

        try:
            # Auth
            self.test_auth_tokens()

            # §7 Checks
            self.test_pending_company_gate()
            self.test_company_approve_reject()
            self.test_drive_approve_reject()
            self.test_blacklist_lockout()
            self.test_student_drives_and_eligibility()
            self.test_apply_errors()
            self.test_offer_letter()
            self.test_resume_upload()
            self.test_empty_states()
            self.test_deactivated_student()
            self.test_auth_edges()
            self.test_wrong_role_guard()

            # Summary
            print("\n" + "=" * 60)
            print("TEST SUMMARY")
            print("=" * 60)
            passed = sum(1 for _, p, _ in self.results if p)
            total = len(self.results)
            print(f"\nResults: {passed}/{total} passed")

            for name, passed, details in self.results:
                status = "✓" if passed else "✗"
                print(f"  {status} {name}" + (f" ({details})" if details else ""))

            return passed == total

        finally:
            self.stop_flask()

if __name__ == '__main__':
    tester = Tester()
    success = tester.run()
    sys.exit(0 if success else 1)
