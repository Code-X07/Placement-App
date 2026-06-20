/* ===========================================================================
   StudentList.js (admin) — GET /api/admin/students (+ deactivate).
   Brief §6.3: Deactivate shown only for currently-active students.
   CGPA on the spec's 0–10 scale. No pagination/search (brief §5).
   =========================================================================== */
import api from '../../api.js';

export default {
  name: 'StudentList',
  data() { return { loading: true, error: '', rows: [], acting: {} }; },
  async created() { await this.load(); },
  methods: {
    async load() {
      this.loading = true; this.error = '';
      try { const { data } = await api.get('/admin/students'); this.rows = data; }
      catch (e) { this.error = (e.response && e.response.data && e.response.data.error) || 'Could not load students.'; }
      finally { this.loading = false; }
    },
    initials(n) { return (n || 'U').split(' ').slice(0, 2).map(x => x[0]).join('').toUpperCase(); },
    async deactivate(row) {
      this.$set(this.acting, row.id, true);
      try { await api.put(`/admin/students/${row.id}/deactivate`); row.is_active = false;
        this.$bus.$emit('toast', { type: 'success', msg: `${row.name} deactivated.` }); }
      catch (e) {} finally { this.$set(this.acting, row.id, false); }
    },
  },
  template: `
    <div data-screen-label="Manage Students">
      <div class="page-head">
        <div class="ttl"><h1>Students Management</h1><p class="page-sub">Manage student profiles, placement eligibility, and academic records.</p></div>
      </div>

      <div class="sheet">
        <div v-if="loading" class="state-wrap"><div class="spinner-eh"></div></div>
        <div v-else-if="error" class="state-wrap"><i class="bi bi-exclamation-triangle ic"></i><h3>Couldn't load students</h3><p>{{ error }}</p><button class="btn btn-ghost btn-sm" @click="load">Retry</button></div>
        <div v-else-if="!rows.length" class="state-wrap"><i class="bi bi-people ic"></i><h3>No students yet</h3><p>Student records will appear here once they register.</p></div>

        <table v-else class="tbl">
          <thead><tr><th>Name</th><th>Email</th><th>Branch</th><th>CGPA</th><th>Status</th><th class="text-end">Actions</th></tr></thead>
          <tbody>
            <tr v-for="r in rows" :key="r.id">
              <td>
                <div class="d-flex align-items-center gap-3">
                  <div class="row-ava round soft">{{ initials(r.name) }}</div>
                  <div><div class="cell-strong">{{ r.name }}</div><div class="cell-sub">ID: {{ r.roll }}</div></div>
                </div>
              </td>
              <td class="text-muted-2">{{ r.email }}</td>
              <td>{{ r.branch }}</td>
              <td class="cell-strong">{{ r.cgpa.toFixed(2) }}</td>
              <td><span class="pill" :class="r.is_active ? 'tone-green' : 'tone-grey'"><span class="pdot"></span>{{ r.is_active ? 'Active' : 'Inactive' }}</span></td>
              <td class="text-end">
                <button v-if="r.is_active" class="btn btn-xs btn-ghost" style="color:var(--tone-red-fg)" :disabled="acting[r.id]" @click="deactivate(r)">Deactivate</button>
                <span v-else class="cell-sub">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `,
};
