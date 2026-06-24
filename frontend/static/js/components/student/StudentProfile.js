/* ===========================================================================
   StudentProfile.js — PUT /api/student/profile + POST /profile/resume.
   Brief §7: email is READ-ONLY (login identity, not a profile field).
   Resume PDF only, ≤5MB, with uploaded-file chip.
   Validation (spec §9): CGPA 0–10, phone 10 digits.
   =========================================================================== */
import api from '../../api.js';

const BRANCHES = ['Computer Science', 'Information Technology', 'Electrical Engineering', 'Mechanical Engineering', 'Civil Engineering', 'Electronics'];

export default {
  name: 'StudentProfile',
  data() {
    return { loading: true, saving: false, error: '', ok: '', branches: BRANCHES,
      form: { name: '', email: '', phone: '', branch: '', year: '', cgpa: '' }, resumeName: '', resumeError: '' };
  },
  async created() {
    try {
      const { data } = await api.get('/student/profile');
      this.form = { name: data.name, email: data.email, phone: data.phone, branch: data.branch, year: data.year, cgpa: data.cgpa };
      if (data.resume_path) this.resumeName = data.resume_path.split('/').pop();
    } catch (e) { this.error = 'Could not load profile.'; }
    finally { this.loading = false; }
  },
  methods: {
    validate() {
      const f = this.form;
      if (!f.name.trim()) return 'Full name is required.';
      if (!/^\d{10}$/.test(String(f.phone).replace(/\D/g, ''))) return 'Phone number must be 10 digits.';
      if (f.cgpa === '' || f.cgpa < 0 || f.cgpa > 10) return 'CGPA must be between 0 and 10.';
      return '';
    },
    async save() {
      this.error = ''; this.ok = '';
      this.error = this.validate();
      if (this.error) return;
      this.saving = true;
      try {
        await api.put('/student/profile', { name: this.form.name, phone: this.form.phone, branch: this.form.branch, year: this.form.year, cgpa: Number(this.form.cgpa) });
        this.ok = 'Profile saved.'; this.$bus.$emit('toast', { type: 'success', msg: 'Profile updated.' });
      } catch (e) { this.error = (e.response && e.response.data && e.response.data.error) || 'Save failed.'; }
      finally { this.saving = false; }
    },
    pick() { this.$refs.file.click(); },
    async onFile(e) {
      this.resumeError = '';
      const f = e.target.files[0];
      e.target.value = '';
      if (!f) return;
      if (f.type !== 'application/pdf') { this.resumeError = 'Resume must be a PDF file.'; return; }
      if (f.size > 5 * 1024 * 1024) { this.resumeError = 'Resume must be 5MB or smaller.'; return; }
      try {
        const formData = new FormData();
        formData.append('resume', f);
        await api.post('/student/profile/resume', formData, { headers: { 'Content-Type': undefined } });
        this.resumeName = f.name;
        this.$bus.$emit('toast', { type: 'success', msg: 'Resume uploaded.' });
      } catch (err) { this.resumeError = 'Upload failed.'; }
    },
  },
  template: `
    <div data-screen-label="Student Profile" style="max-width:920px">
      <div class="page-head">
        <div class="ttl"><h1>Student Profile Management</h1><p class="page-sub">Update and maintain your academic and personal records for placement opportunities.</p></div>
      </div>

      <div v-if="loading" class="state-wrap"><div class="spinner-eh"></div></div>

      <div v-else class="card-soft" style="padding:36px 40px">
        <div v-if="error" class="alert alert-danger py-2 px-3 mb-3" style="border-radius:8px;font-size:14px">{{ error }}</div>
        <div v-if="ok" class="alert alert-success py-2 px-3 mb-3" style="border-radius:8px;font-size:14px">{{ ok }}</div>

        <h2 style="margin-bottom:6px">Personal Information</h2>
        <hr class="divider" style="margin:0 0 20px">
        <div class="row g-3 mb-3">
          <div class="col-md-6"><label class="form-label">Full Name</label><input v-model="form.name" class="form-control"></div>
          <div class="col-md-6">
            <label class="form-label">Email Address <span class="cell-sub">(login identity — read only)</span></label>
            <input :value="form.email" class="form-control" disabled style="background:var(--color-bg-surface)">
          </div>
        </div>
        <div class="mb-2">
          <label class="form-label">Phone Number</label><input v-model="form.phone" class="form-control" placeholder="10-digit number">
        </div>

        <h2 style="margin:28px 0 6px">Academic Details</h2>
        <hr class="divider" style="margin:0 0 20px">
        <div class="row g-3 mb-2">
          <div class="col-md-4"><label class="form-label">Branch</label>
            <select v-model="form.branch" class="form-select"><option v-for="b in branches" :key="b">{{ b }}</option></select></div>
          <div class="col-md-4"><label class="form-label">Year of Graduation</label><input v-model="form.year" type="number" class="form-control"></div>
          <div class="col-md-4"><label class="form-label">CGPA (0-10)</label><input v-model="form.cgpa" type="number" step="0.1" min="0" max="10" class="form-control"></div>
        </div>

        <h2 style="margin:28px 0 6px">Resume Upload</h2>
        <hr class="divider" style="margin:0 0 20px">
        <div v-if="resumeError" class="alert alert-danger py-2 px-3 mb-3" style="border-radius:8px;font-size:14px">{{ resumeError }}</div>
        <div @click="pick" style="border:2px dashed var(--color-border);border-radius:12px;background:var(--color-bg-surface);padding:36px;text-align:center;cursor:pointer">
          <i class="bi bi-file-earmark-arrow-up" style="font-size:28px;color:var(--color-text-muted)"></i>
          <div class="cell-strong mt-2">Click to upload or drag and drop</div>
          <div class="cell-sub">PDF up to 5MB</div>
          <input ref="file" type="file" accept="application/pdf" class="d-none" @change="onFile">
          <div v-if="resumeName" class="chip mt-3" style="background:var(--tone-green-bg);border-color:#bbe7c9;color:var(--tone-green-fg);display:inline-flex">
            <i class="bi bi-check-circle"></i> Uploaded: {{ resumeName }}
          </div>
        </div>

        <div class="d-flex justify-content-end mt-4">
          <button class="btn btn-action" :disabled="saving" @click="save">
            <span v-if="saving" class="spinner-border spinner-border-sm me-2"></span>Save Profile
          </button>
        </div>
      </div>
    </div>
  `,
};
