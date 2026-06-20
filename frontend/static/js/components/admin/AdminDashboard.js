/* ===========================================================================
   AdminDashboard.js — GET /api/admin/dashboard. FOUR stat cards only.
   Brief §5: no charts, no "Recent Activity", no trend deltas.
   =========================================================================== */
import api from '../../api.js';

export default {
  name: 'AdminDashboard',
  data() {
    return { loading: true, error: '', stats: null };
  },
  computed: {
    cards() {
      const s = this.stats || {};
      return [
        { lbl: 'Total Students',     val: s.students,     icon: 'people' },
        { lbl: 'Total Companies',    val: s.companies,    icon: 'building' },
        { lbl: 'Total Drives',       val: s.drives,       icon: 'calendar-event' },
        { lbl: 'Total Applications', val: s.applications, icon: 'file-earmark-text' },
      ];
    },
  },
  async created() { await this.load(); },
  methods: {
    async load() {
      this.loading = true; this.error = '';
      try {
        const { data } = await api.get('/admin/dashboard');
        this.stats = data;
      } catch (e) {
        this.error = (e.response && e.response.data && e.response.data.error) || 'Could not load dashboard.';
      } finally {
        this.loading = false;
      }
    },
    fmt(n) { return n == null ? '—' : Number(n).toLocaleString(); },
  },
  template: `
    <div data-screen-label="Admin Dashboard">
      <div class="page-head">
        <div class="ttl"><h1>Overview</h1><p class="page-sub">Key metrics for the current placement season.</p></div>
      </div>

      <div v-if="loading" class="state-wrap"><div class="spinner-eh"></div></div>
      <div v-else-if="error" class="alert alert-danger" style="border-radius:10px">{{ error }}
        <button class="btn btn-sm btn-ghost ms-2" @click="load">Retry</button>
      </div>

      <div v-else class="row g-3">
        <div class="col-12 col-sm-6 col-xl-3" v-for="c in cards" :key="c.lbl">
          <div class="stat-card">
            <div class="lbl"><span>{{ c.lbl }}</span><span class="ic"><i :class="'bi bi-' + c.icon"></i></span></div>
            <div class="val">{{ fmt(c.val) }}</div>
          </div>
        </div>
      </div>
    </div>
  `,
};
