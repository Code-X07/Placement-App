/* ===========================================================================
   CompanyList.js — GET /api/admin/companies (+ approve/reject/blacklist).
   Brief §6.3: real Actions column. No industry subtitle (not a field).
   No pagination, no in-table search, no export (brief §5).
   Status filter is the prototype's "All Statuses" -> server param.
   =========================================================================== */
import api from '../../api.js';

const TONES = { pending: 'amber', approved: 'green', rejected: 'red' };

export default {
  name: 'CompanyList',
  data() {
    return { loading: true, error: '', rows: [], filter: 'all', acting: {} };
  },
  async created() { await this.load(); },
  methods: {
    async load() {
      this.loading = true; this.error = '';
      try {
        const { data } = await api.get('/admin/companies', { params: { approval_status: this.filter } });
        this.rows = data;
      } catch (e) {
        this.error = (e.response && e.response.data && e.response.data.error) || 'Could not load companies.';
      } finally {
        this.loading = false;
      }
    },
    tone(s) { return TONES[s] || 'grey'; },
    initial(n) { return (n || '?')[0].toUpperCase(); },
    async act(row, action) {
      this.$set(this.acting, row.id, true);
      try {
        const { data } = await api.put(`/admin/companies/${row.id}/${action}`);
        row.approval_status = data.approval_status;
        this.$bus.$emit('toast', { type: 'success', msg: `${row.company_name} ${action}d.` });
      } catch (e) { /* interceptor toasts */ }
      finally { this.$set(this.acting, row.id, false); }
    },
  },
  template: `
    <div data-screen-label="Manage Companies">
      <div class="page-head">
        <div class="ttl"><h1>Companies Management</h1><p class="page-sub">Institutional oversight of recruiting partners.</p></div>
        <div class="d-flex gap-2">
          <select v-model="filter" @change="load" class="form-select" style="width:auto">
            <option value="all">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>
      </div>

      <div class="sheet">
        <div v-if="loading" class="state-wrap"><div class="spinner-eh"></div></div>
        <div v-else-if="error" class="state-wrap"><i class="bi bi-exclamation-triangle ic"></i><h3>Couldn't load companies</h3><p>{{ error }}</p><button class="btn btn-ghost btn-sm" @click="load">Retry</button></div>
        <div v-else-if="!rows.length" class="state-wrap"><i class="bi bi-building ic"></i><h3>No companies found</h3><p>No recruiting partners match this filter yet.</p></div>

        <table v-else class="tbl">
          <thead><tr><th>Company Name</th><th>Email Contact</th><th>Approval Status</th><th class="text-end">Actions</th></tr></thead>
          <tbody>
            <tr v-for="r in rows" :key="r.id">
              <td>
                <div class="d-flex align-items-center gap-3">
                  <div class="row-ava">{{ initial(r.company_name) }}</div>
                  <div><div class="cell-strong">{{ r.company_name }}</div><div class="cell-sub">{{ r.website }}</div></div>
                </div>
              </td>
              <td class="text-muted-2">{{ r.hr_contact }}</td>
              <td><span class="pill" :class="'tone-' + tone(r.approval_status)"><span class="pdot"></span>{{ r.approval_status }}</span></td>
              <td>
                <div class="d-flex gap-2 justify-content-end">
                  <button class="btn btn-xs btn-action" :disabled="r.approval_status==='approved' || acting[r.id]" @click="act(r,'approve')">Approve</button>
                  <button class="btn btn-xs btn-ghost" :disabled="r.approval_status==='rejected' || acting[r.id]" @click="act(r,'reject')">Reject</button>
                  <button class="btn btn-xs btn-ghost" style="color:var(--tone-red-fg)" :disabled="acting[r.id]" @click="act(r,'blacklist')">Blacklist</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `,
};
