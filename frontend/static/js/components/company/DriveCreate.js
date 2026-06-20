/* ===========================================================================
   DriveCreate.js — POST /api/company/drives.
   Brief §7 PRESERVE: full field set + tag-chip branches + "lands in pending"
   banner. Brief §5: NO "Save as Draft" — one button, "Submit for Approval".
   Validation (spec §9): deadline must be future, CTC numeric.
   =========================================================================== */
import api from '../../api.js';

export default {
  name: 'DriveCreate',
  data() {
    return {
      form: { title: '', description: '', ctc: '', location: '', department: '', eligibility_cgpa: 7.0, application_deadline: '', eligibility_branch: ['Computer Science', 'Information Technology'] },
      branchInput: '', submitting: false, error: '',
    };
  },
  computed: { today() { return new Date().toISOString().slice(0, 10); } },
  methods: {
    addBranch() {
      const v = this.branchInput.trim();
      if (v && !this.form.eligibility_branch.includes(v)) this.form.eligibility_branch.push(v);
      this.branchInput = '';
    },
    removeBranch(i) { this.form.eligibility_branch.splice(i, 1); },
    validate() {
      const f = this.form;
      if (!f.title.trim()) return 'Drive title is required.';
      if (!f.description.trim()) return 'Description is required.';
      if (f.ctc === '' || isNaN(Number(f.ctc)) || Number(f.ctc) <= 0) return 'CTC must be a positive number.';
      if (!f.location.trim()) return 'Job location is required.';
      if (f.eligibility_cgpa < 0 || f.eligibility_cgpa > 10) return 'Minimum CGPA must be between 0 and 10.';
      if (!f.application_deadline) return 'Application deadline is required.';
      if (f.application_deadline <= this.today) return 'Application deadline must be a future date.';
      return '';
    },
    async submit() {
      this.error = this.validate();
      if (this.error) return;
      this.submitting = true;
      try {
        await api.post('/company/drives', { ...this.form, ctc: Number(this.form.ctc) });
        this.$bus.$emit('toast', { type: 'success', msg: 'Drive submitted for approval.' });
        this.$router.push('/company/dashboard');
      } catch (e) { this.error = (e.response && e.response.data && e.response.data.error) || 'Submission failed.'; }
      finally { this.submitting = false; }
    },
  },
  template: `
    <div data-screen-label="Post New Drive" style="max-width:900px">
      <div class="page-head">
        <div class="ttl"><h1>Post New Drive</h1><p class="page-sub">Create a new placement drive listing. Submissions land in 'pending' status awaiting administrative approval.</p></div>
      </div>

      <div class="card-soft">
        <div class="banner mb-4">
          <i class="bi bi-info-circle"></i>
          <div><div class="cell-strong">Approval Workflow</div><div class="cell-sub">Once submitted, this drive will not be visible to students until an administrator reviews and approves the posting.</div></div>
        </div>

        <div v-if="error" class="alert alert-danger py-2 px-3 mb-3" style="border-radius:8px;font-size:14px">{{ error }}</div>

        <div class="mb-3">
          <label class="form-label">Drive Title <span class="req">*</span></label>
          <input v-model="form.title" class="form-control" placeholder="e.g., Software Engineering Campus Drive 2024">
        </div>
        <div class="mb-3">
          <label class="form-label">Description <span class="req">*</span></label>
          <textarea v-model="form.description" class="form-control" rows="4" placeholder="Provide details about the role, company, and selection process…"></textarea>
        </div>
        <div class="row g-3 mb-3">
          <div class="col-md-6">
            <label class="form-label">CTC (in LPA) <span class="req">*</span></label>
            <div class="input-ic"><i class="bi" style="font-style:normal">₹</i><input v-model="form.ctc" type="number" step="0.1" class="form-control" placeholder="0.00"></div>
          </div>
          <div class="col-md-6">
            <label class="form-label">Job Location <span class="req">*</span></label>
            <div class="input-ic"><i class="bi bi-geo-alt"></i><input v-model="form.location" class="form-control" placeholder="e.g., Bangalore, Remote"></div>
          </div>
        </div>
        <div class="mb-3">
          <label class="form-label">Department</label>
          <input v-model="form.department" class="form-control" placeholder="e.g., Engineering, Product, Sales">
        </div>

        <hr class="divider" style="margin:8px 0 20px">
        <h3 style="margin-bottom:16px">Eligibility Criteria</h3>

        <div class="row g-3 mb-3">
          <div class="col-md-6">
            <label class="form-label">Minimum CGPA <span class="req">*</span></label>
            <input v-model.number="form.eligibility_cgpa" type="number" step="0.1" min="0" max="10" class="form-control">
            <div class="form-hint">On a scale of 0 to 10.</div>
          </div>
          <div class="col-md-6">
            <label class="form-label">Application Deadline <span class="req">*</span></label>
            <input v-model="form.application_deadline" type="date" :min="today" class="form-control">
          </div>
        </div>

        <div class="mb-2">
          <label class="form-label">Eligible Branches <span class="req">*</span></label>
          <div class="d-flex flex-wrap gap-2 align-items-center form-control" style="height:auto;min-height:46px">
            <span v-for="(b, i) in form.eligibility_branch" :key="b" class="chip">{{ b }} <span class="x" @click="removeBranch(i)"><i class="bi bi-x"></i></span></span>
            <input v-model="branchInput" @keyup.enter.prevent="addBranch" class="flex-grow-1" style="border:0;outline:0;min-width:160px" placeholder="Type and press enter…">
          </div>
          <div class="form-hint">Select specific branches or leave empty for all branches.</div>
        </div>
      </div>

      <div class="d-flex justify-content-end mt-3">
        <button class="btn btn-action" :disabled="submitting" @click="submit">
          <span v-if="submitting" class="spinner-border spinner-border-sm me-2"></span>Submit for Approval <i class="bi bi-send ms-1"></i>
        </button>
      </div>
    </div>
  `,
};
