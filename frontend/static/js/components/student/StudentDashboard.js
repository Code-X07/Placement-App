/* ===========================================================================
   StudentDashboard.js — GET /api/student/dashboard.
   Welcome + application-status counts + recommended drives.
   =========================================================================== */
import api from '../../api.js';

export default {
  name: 'StudentDashboard',
  data() { return { loading: true, error: '', dash: null }; },
  async created() { await this.load(); },
  methods: {
    async load() {
      this.loading = true; this.error = '';
      try { const { data } = await api.get('/student/dashboard'); this.dash = data; }
      catch (e) { this.error = (e.response && e.response.data && e.response.data.error) || 'Could not load dashboard.'; }
      finally { this.loading = false; }
    },
    fmtDate(d) { return d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' }) : '—'; },
  },
  template: `
    <div data-screen-label="Student Dashboard">
      <div v-if="loading" class="state-wrap"><div class="spinner-eh"></div></div>
      <div v-else-if="error" class="alert alert-danger" style="border-radius:10px">{{ error }} <button class="btn btn-sm btn-ghost ms-2" @click="load">Retry</button></div>

      <template v-else>
        <div class="row g-3 mb-4">
          <div class="col-lg-8">
            <div class="card-soft h-100" style="padding:40px">
              <h1 style="font-size:34px;margin-bottom:10px">Welcome back, {{ (dash.name || '').split(' ')[0] }}!</h1>
              <p class="page-sub" style="font-size:17px;max-width:560px">Your placement journey is looking promising. Keep up the good work and prepare for your upcoming assessments.</p>
            </div>
          </div>
          <div class="col-lg-4">
            <div class="card-soft h-100">
              <h3 style="margin-bottom:16px">Application Status</h3>
              <div class="d-flex flex-column gap-2">
                <div class="d-flex justify-content-between align-items-center" style="background:var(--color-bg-surface);border-radius:10px;padding:14px 16px">
                  <span class="d-flex align-items-center gap-2"><i class="bi bi-send"></i> Applied</span><span style="font-size:20px;font-weight:700">{{ dash.counts.applied }}</span>
                </div>
                <div class="d-flex justify-content-between align-items-center" style="background:var(--tone-green-bg);border-radius:10px;padding:14px 16px">
                  <span class="d-flex align-items-center gap-2"><i class="bi bi-star"></i> Shortlisted</span><span style="font-size:20px;font-weight:700">{{ dash.counts.shortlisted }}</span>
                </div>
                <div class="d-flex justify-content-between align-items-center" style="background:var(--color-bg-surface);border-radius:10px;padding:14px 16px">
                  <span class="d-flex align-items-center gap-2"><i class="bi bi-check2-circle"></i> Selected</span><span style="font-size:20px;font-weight:700">{{ dash.counts.selected }}</span>
                </div>
                <div class="d-flex justify-content-between align-items-center" style="background:var(--color-bg-surface);border-radius:10px;padding:14px 16px">
                  <span class="d-flex align-items-center gap-2"><i class="bi bi-x-circle"></i> Rejected</span><span style="font-size:20px;font-weight:700">{{ dash.counts.rejected }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="d-flex justify-content-between align-items-end mb-3">
          <div><h2>Recommended Drives</h2><p class="page-sub">Based on your profile and preferences.</p></div>
          <router-link to="/student/drives">View All →</router-link>
        </div>

        <div v-if="!dash.recommended.length" class="card-soft state-wrap"><i class="bi bi-briefcase ic"></i><h3>No drives available</h3><p>Check back soon for new opportunities.</p></div>
        <div v-else class="row g-3">
          <div class="col-md-4" v-for="d in dash.recommended" :key="d.id">
            <div class="card-soft h-100 d-flex flex-column">
              <div class="d-flex justify-content-between align-items-start mb-3">
                <div class="row-ava soft"><i class="bi bi-laptop"></i></div>
              </div>
              <h3 style="font-size:18px;margin-bottom:4px">{{ d.title }}</h3>
              <div class="cell-sub mb-3">{{ d.company_name }}</div>
              <div class="d-flex flex-column gap-2 cell-sub" style="font-size:14px">
                <span><i class="bi bi-cash me-2"></i>{{ d.ctc }} LPA</span>
                <span><i class="bi bi-geo-alt me-2"></i>{{ d.location }}</span>
                <span><i class="bi bi-clock me-2"></i>Closes {{ fmtDate(d.application_deadline) }}</span>
              </div>
              <button class="btn btn-action w-100 mt-3" @click="$router.push('/student/drives')">View Details</button>
            </div>
          </div>
        </div>
      </template>
    </div>
  `,
};
