/* ===========================================================================
   CompanyDashboard.js — GET /api/company/dashboard.
   Brief §6.7: gated variant for unapproved companies (pending banner, NO
   post affordance). Brief §5: drop vanity metrics (Hired YTD / Avg Time to
   Hire / Applicant Volume %). Brief §6.2: spec status enums, not Active/Draft.
   =========================================================================== */
import api from '../../api.js';

const TONES = { pending: 'amber', approved: 'green', rejected: 'red' };

export default {
  name: 'CompanyDashboard',
  data() { return { loading: true, error: '', dash: null, filter: 'all' }; },
  computed: {
    approved() { return this.dash && this.dash.approval_status === 'approved'; },
    drives() {
      const list = (this.dash && this.dash.drives) || [];
      return this.filter === 'all' ? list : list.filter(d => d.status === this.filter);
    },
  },
  async created() { await this.load(); },
  methods: {
    async load() {
      this.loading = true; this.error = '';
      try { const { data } = await api.get('/company/dashboard'); this.dash = data; }
      catch (e) { this.error = (e.response && e.response.data && e.response.data.error) || 'Could not load dashboard.'; }
      finally { this.loading = false; }
    },
    tone(s) { return TONES[s] || 'grey'; },
    initial(n) { return (n || '?')[0].toUpperCase(); },
    fmtDate(d) { return d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' }) : '—'; },
  },
  template: `
    <div data-screen-label="Company Dashboard">
      <div class="page-head">
        <div class="ttl"><h1>Company Workspace</h1><p class="page-sub">Manage your recruitment drives and applicant volume.</p></div>
      </div>

      <div v-if="loading" class="state-wrap"><div class="spinner-eh"></div></div>
      <div v-else-if="error" class="alert alert-danger" style="border-radius:10px">{{ error }} <button class="btn btn-sm btn-ghost ms-2" @click="load">Retry</button></div>

      <template v-else>
        <!-- Pending / gated variant (brief §6.7) -->
        <div v-if="!approved" class="card-soft" style="text-align:center;padding:48px 24px">
          <div class="row-ava" style="width:56px;height:56px;margin:0 auto 16px;background:var(--tone-amber-bg);color:var(--tone-amber-dot);border-radius:14px"><i class="bi bi-hourglass-split" style="font-size:24px"></i></div>
          <h2 style="margin-bottom:8px">Your account is awaiting approval</h2>
          <p class="page-sub" style="max-width:460px;margin:0 auto 4px">
            <strong>{{ dash.company_name }}</strong> is currently
            <span class="pill" :class="'tone-' + tone(dash.approval_status)" style="vertical-align:middle"><span class="pdot"></span>{{ dash.approval_status }}</span>.
            You'll be able to post placement drives once an administrator approves your company.
          </p>
        </div>

        <!-- Approved variant -->
        <template v-else>
          <div class="row g-3 mb-3">
            <div class="col-lg-8">
              <div class="card-soft h-100">
                <div class="d-flex align-items-start gap-3">
                  <div class="row-ava" style="width:52px;height:52px;font-size:20px">{{ initial(dash.company_name) }}</div>
                  <div class="flex-grow-1">
                    <div class="d-flex align-items-center gap-2 flex-wrap">
                      <h2 style="margin:0">{{ dash.company_name }}</h2>
                      <span class="pill tone-green"><span class="pdot"></span>Approved</span>
                    </div>
                    <div class="cell-sub" style="margin-top:2px">{{ dash.website }}</div>
                  </div>
                </div>
                <hr class="divider" style="margin:20px 0">
                <div class="d-flex gap-5 flex-wrap">
                  <div><div class="cell-sub">Active Drives</div><div style="font-size:26px;font-weight:700">{{ dash.active_drives }}</div></div>
                  <div><div class="cell-sub">Total Applicants</div><div style="font-size:26px;font-weight:700">{{ dash.total_applicants.toLocaleString() }}</div></div>
                </div>
              </div>
            </div>
            <div class="col-lg-4">
              <div class="card-soft h-100" style="background:var(--color-structure);color:#fff;display:flex;flex-direction:column;justify-content:space-between">
                <div>
                  <div style="color:#94a3b8;font-size:14px;font-weight:600">Post a new opening</div>
                  <p style="color:#cbd5e1;font-size:14px;margin:8px 0 0">Drives are submitted for admin approval before students can see them.</p>
                </div>
                <button class="btn btn-action mt-3" @click="$router.push('/company/drives/new')"><i class="bi bi-plus-lg me-1"></i> Post Drive</button>
              </div>
            </div>
          </div>

          <div class="sheet">
            <div class="d-flex justify-content-between align-items-center" style="padding:20px 24px">
              <div><div class="section-title">Your Drives</div><div class="cell-sub">Manage ongoing and upcoming recruitment activities.</div></div>
              <select v-model="filter" class="form-select" style="width:auto">
                <option value="all">All Statuses</option><option value="pending">Pending</option><option value="approved">Approved</option><option value="rejected">Rejected</option>
              </select>
            </div>
            <div v-if="!drives.length" class="state-wrap"><i class="bi bi-briefcase ic"></i><h3>No drives yet</h3><p>Post your first drive to start receiving applicants.</p></div>
            <table v-else class="tbl">
              <thead><tr><th>Title</th><th>Status</th><th>Deadline</th><th class="text-end">Applicant Count</th><th class="text-end">Action</th></tr></thead>
              <tbody>
                <tr v-for="d in drives" :key="d.id">
                  <td><div class="cell-strong">{{ d.title }}</div><div class="cell-sub">{{ d.location }}</div></td>
                  <td><span class="pill" :class="'tone-' + tone(d.status)"><span class="pdot"></span>{{ d.status }}</span></td>
                  <td class="text-muted-2">{{ fmtDate(d.application_deadline) }}</td>
                  <td class="text-end cell-strong">{{ d.applicant_count.toLocaleString() }}</td>
                  <td class="text-end">
                    <button class="btn-link-quiet" @click="$router.push('/company/drives/' + d.id + '/applications')">View Details</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>
      </template>
    </div>
  `,
};
