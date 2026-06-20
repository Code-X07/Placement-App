/* ===========================================================================
   ApplicationHistory.js — GET /api/student/applications + async CSV export.
   Brief §6.6: full ExportJob lifecycle — trigger → polling(pending) →
   download link(done) → error(failed). Polls GET /student/export/<job_id>.
   The mock alternates done/failed on successive exports so both show.
   =========================================================================== */
import api from '../../api.js';

const TONES = { applied: 'grey', shortlisted: 'amber', selected: 'green', rejected: 'red' };

export default {
  name: 'ApplicationHistory',
  data() {
    return { loading: true, error: '', rows: [],
      exportState: 'idle', // idle | pending | done | failed
      exportFile: '', exportErr: '', poller: null };
  },
  async created() { await this.load(); },
  beforeDestroy() { if (this.poller) clearInterval(this.poller); },
  methods: {
    async load() {
      this.loading = true; this.error = '';
      try { const { data } = await api.get('/student/applications'); this.rows = data; }
      catch (e) { this.error = (e.response && e.response.data && e.response.data.error) || 'Could not load applications.'; }
      finally { this.loading = false; }
    },
    tone(s) { return TONES[s] || 'grey'; },
    initial(n) { return (n || '?')[0].toUpperCase(); },
    fmtDate(d) { return d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' }) : '—'; },
    async startExport() {
      this.exportState = 'pending'; this.exportErr = ''; this.exportFile = '';
      let jobId;
      try { const { data } = await api.post('/student/export'); jobId = data.job_id; }
      catch (e) { this.exportState = 'failed'; this.exportErr = 'Could not start export.'; return; }

      this.poller = setInterval(async () => {
        try {
          const { data } = await api.get('/student/export/' + jobId);
          if (data.status === 'done') {
            clearInterval(this.poller); this.exportState = 'done'; this.exportFile = data.file_path;
            this.$bus.$emit('toast', { type: 'success', msg: 'Export ready to download.' });
          } else if (data.status === 'failed') {
            clearInterval(this.poller); this.exportState = 'failed'; this.exportErr = data.error || 'Export failed.';
          }
        } catch (e) { clearInterval(this.poller); this.exportState = 'failed'; this.exportErr = 'Export failed.'; }
      }, 700);
    },
    reset() { this.exportState = 'idle'; this.exportErr = ''; this.exportFile = ''; },
    async downloadCsv(filePath) {
      try {
        const { data: blob } = await api.get(filePath, { responseType: 'blob' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'my_applications.csv';
        a.click();
        URL.revokeObjectURL(url);
      } catch (e) {
        this.$bus.$emit('toast', { type: 'danger', msg: 'Failed to download CSV.' });
      }
    },
  },
  template: `
    <div data-screen-label="Application History">
      <div class="page-head">
        <div class="ttl"><h1>Application History</h1><p class="page-sub">Track and manage your submitted job applications.</p></div>
        <div class="text-end">
          <button v-if="exportState==='idle' || exportState==='done' || exportState==='failed'" class="btn btn-ghost" @click="startExport">
            <i class="bi bi-download me-1"></i> Export CSV
          </button>
          <button v-else class="btn btn-ghost" disabled><span class="spinner-border spinner-border-sm me-2"></span>Preparing…</button>

          <div v-if="exportState==='pending'" class="cell-sub mt-2">Generating your export…</div>
          <div v-if="exportState==='done'" class="mt-2">
            <a href="javascript:void(0)" @click="downloadCsv(exportFile)" class="d-inline-flex align-items-center gap-1"><i class="bi bi-file-earmark-arrow-down"></i> Download my_applications.csv</a>
          </div>
          <div v-if="exportState==='failed'" class="mt-2 text-end" style="max-width:260px">
            <div class="cell-sub" style="color:var(--tone-red-fg)">{{ exportErr }}</div>
            <button class="btn-link-quiet" @click="startExport">Retry export</button>
          </div>
        </div>
      </div>

      <div class="sheet">
        <div v-if="loading" class="state-wrap"><div class="spinner-eh"></div></div>
        <div v-else-if="error" class="state-wrap"><i class="bi bi-exclamation-triangle ic"></i><h3>Couldn't load applications</h3><p>{{ error }}</p><button class="btn btn-ghost btn-sm" @click="load">Retry</button></div>
        <div v-else-if="!rows.length" class="state-wrap"><i class="bi bi-inbox ic"></i><h3>No applications yet</h3><p>Browse drives and apply to see your history here.</p><router-link to="/student/drives" class="btn btn-action btn-sm mt-2" style="color:#fff">Browse Drives</router-link></div>

        <table v-else class="tbl">
          <thead><tr><th>Company</th><th>Role</th><th>Applied Date</th><th>Status</th></tr></thead>
          <tbody>
            <tr v-for="r in rows" :key="r.id">
              <td>
                <div class="d-flex align-items-center gap-3">
                  <div class="row-ava soft">{{ initial(r.company_name) }}</div>
                  <div><div class="cell-strong">{{ r.company_name }}</div><div class="cell-sub">{{ r.location }}</div></div>
                </div>
              </td>
              <td>{{ r.role }}</td>
              <td class="text-muted-2">{{ fmtDate(r.applied_at) }}</td>
              <td><span class="pill" :class="'tone-' + tone(r.status)"><span class="pdot"></span>{{ r.status }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `,
};
