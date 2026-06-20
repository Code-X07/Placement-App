/* ===========================================================================
   DriveList.js (admin) — GET /api/admin/drives (+ approve/reject).
   Brief §6.3: real Approve/Reject actions. Spec enums. No pagination/search.
   =========================================================================== */
import api from '../../api.js';

const TONES = { pending: 'amber', approved: 'green', rejected: 'red' };

export default {
  name: 'AdminDriveList',
  data() { return { loading: true, error: '', rows: [], filter: 'all', acting: {} }; },
  computed: {
    shown() { return this.filter === 'all' ? this.rows : this.rows.filter(r => r.status === this.filter); },
  },
  async created() { await this.load(); },
  methods: {
    async load() {
      this.loading = true; this.error = '';
      try { const { data } = await api.get('/admin/drives'); this.rows = data; }
      catch (e) { this.error = (e.response && e.response.data && e.response.data.error) || 'Could not load drives.'; }
      finally { this.loading = false; }
    },
    tone(s) { return TONES[s] || 'grey'; },
    initial(n) { return (n || '?')[0].toUpperCase(); },
    fmtDate(d) { return d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' }) : '—'; },
    async act(row, action) {
      this.$set(this.acting, row.id, true);
      try { const { data } = await api.put(`/admin/drives/${row.id}/${action}`); row.status = data.status;
        this.$bus.$emit('toast', { type: 'success', msg: `Drive ${action}d.` }); }
      catch (e) {} finally { this.$set(this.acting, row.id, false); }
    },
  },
  template: `
    <div data-screen-label="Manage Drives">
      <div class="page-head">
        <div class="ttl"><h1>Drives Management</h1><p class="page-sub">Review and manage placement drive requests.</p></div>
        <select v-model="filter" class="form-select" style="width:auto">
          <option value="all">All Statuses</option><option value="pending">Pending</option><option value="approved">Approved</option><option value="rejected">Rejected</option>
        </select>
      </div>

      <div class="sheet">
        <div v-if="loading" class="state-wrap"><div class="spinner-eh"></div></div>
        <div v-else-if="error" class="state-wrap"><i class="bi bi-exclamation-triangle ic"></i><h3>Couldn't load drives</h3><p>{{ error }}</p><button class="btn btn-ghost btn-sm" @click="load">Retry</button></div>
        <div v-else-if="!shown.length" class="state-wrap"><i class="bi bi-briefcase ic"></i><h3>No drives found</h3><p>Nothing matches this filter.</p></div>

        <table v-else class="tbl">
          <thead><tr><th>Title</th><th>Company</th><th>Deadline</th><th>Status</th><th class="text-end">Actions</th></tr></thead>
          <tbody>
            <tr v-for="r in shown" :key="r.id">
              <td><div class="cell-strong">{{ r.title }}</div><div class="cell-sub">ID: {{ r.id }}</div></td>
              <td>
                <div class="d-flex align-items-center gap-2">
                  <div class="row-ava soft" style="width:30px;height:30px;font-size:13px">{{ initial(r.company_name) }}</div>
                  <span>{{ r.company_name }}</span>
                </div>
              </td>
              <td class="text-muted-2">{{ fmtDate(r.application_deadline) }}</td>
              <td><span class="pill" :class="'tone-' + tone(r.status)"><span class="pdot"></span>{{ r.status }}</span></td>
              <td>
                <div class="d-flex gap-2 justify-content-end">
                  <button class="btn btn-xs btn-action" :disabled="r.status==='approved' || acting[r.id]" @click="act(r,'approve')">Approve</button>
                  <button class="btn btn-xs btn-ghost" :disabled="r.status==='rejected' || acting[r.id]" @click="act(r,'reject')">Reject</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `,
};
