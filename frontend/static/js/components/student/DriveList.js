/* ===========================================================================
   DriveList.js (student / Browse) — GET /api/student/drives + apply.
   Brief §5: NO Industry/MinCTC/Location filter bar (no such params),
   NO pagination. Brief §6.5: show eligibility_cgpa + eligibility_branch on
   every row; Apply DISABLED with a reason when ineligible or already applied.
   =========================================================================== */
import api from '../../api.js';

export default {
  name: 'StudentDriveList',
  data() { return { loading: true, error: '', rows: [], applying: {} }; },
  async created() { await this.load(); },
  methods: {
    async load() {
      this.loading = true; this.error = '';
      try { const { data } = await api.get('/student/drives'); this.rows = data; }
      catch (e) { this.error = (e.response && e.response.data && e.response.data.error) || 'Could not load drives.'; }
      finally { this.loading = false; }
    },
    initial(n) { return (n || '?')[0].toUpperCase(); },
    fmtDate(d) { return d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' }) : '—'; },
    disabledReason(r) {
      if (r.applied && !r.eligible) return r.reasons.join(' · ');
      if (r.applied) return 'Already applied';
      if (!r.eligible) return r.reasons.filter(x => x !== 'Already applied').join(' · ');
      return '';
    },
    canApply(r) { return r.eligible && !r.applied; },
    async apply(r) {
      this.$set(this.applying, r.id, true);
      try { await api.post(`/student/drives/${r.id}/apply`); r.applied = true;
        r.reasons = Array.from(new Set([...(r.reasons || []), 'Already applied']));
        this.$bus.$emit('toast', { type: 'success', msg: `Applied to ${r.title}.` }); }
      catch (e) {} finally { this.$set(this.applying, r.id, false); }
    },
  },
  template: `
    <div data-screen-label="Browse Drives">
      <div class="page-head">
        <div class="ttl"><h1>Browse Drives</h1><p class="page-sub">Explore and apply for upcoming placement drives.</p></div>
      </div>

      <div class="sheet">
        <div v-if="loading" class="state-wrap"><div class="spinner-eh"></div></div>
        <div v-else-if="error" class="state-wrap"><i class="bi bi-exclamation-triangle ic"></i><h3>Couldn't load drives</h3><p>{{ error }}</p><button class="btn btn-ghost btn-sm" @click="load">Retry</button></div>
        <div v-else-if="!rows.length" class="state-wrap"><i class="bi bi-briefcase ic"></i><h3>No open drives</h3><p>There are no approved drives you're eligible to see right now.</p></div>

        <table v-else class="tbl">
          <thead><tr><th>Company</th><th>Drive Title</th><th>CTC</th><th>Eligibility</th><th>Deadline</th><th class="text-end">Action</th></tr></thead>
          <tbody>
            <tr v-for="r in rows" :key="r.id">
              <td>
                <div class="d-flex align-items-center gap-3">
                  <div class="row-ava soft">{{ initial(r.company_name) }}</div>
                  <div><div class="cell-strong">{{ r.company_name }}</div><div class="cell-sub">{{ r.location }}</div></div>
                </div>
              </td>
              <td class="cell-strong">{{ r.title }}</td>
              <td>{{ r.ctc.toFixed(1) }} LPA</td>
              <td>
                <div class="cell-sub">Min CGPA {{ r.eligibility_cgpa.toFixed(1) }}</div>
                <div class="cell-sub">{{ r.eligibility_branch.length ? r.eligibility_branch.join(', ') : 'All branches' }}</div>
              </td>
              <td class="text-muted-2">{{ fmtDate(r.application_deadline) }}</td>
              <td class="text-end">
                <button v-if="canApply(r)" class="btn btn-xs btn-action" :disabled="applying[r.id]" @click="apply(r)">
                  <span v-if="applying[r.id]" class="spinner-border spinner-border-sm"></span><span v-else>Apply</span>
                </button>
                <span v-else :title="disabledReason(r)">
                  <button class="btn btn-xs btn-ghost" disabled>
                    <i class="bi" :class="r.applied ? 'bi-check2' : 'bi-lock'"></i>
                    {{ r.applied && r.eligible ? 'Applied' : 'Unavailable' }}
                  </button>
                  <div class="cell-sub" style="font-size:12px;margin-top:4px;max-width:180px;margin-left:auto">{{ disabledReason(r) }}</div>
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `,
};
