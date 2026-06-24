/* ===========================================================================
   DriveApplications.js — GET /api/company/drives/:id/applications
   + PUT /api/company/applications/:id/status.
   Brief §7 PRESERVE: "View Offer Letter" appears ONLY on the selected
   applicant. Brief §5: no Export CSV (company-side), no in-table search.
   =========================================================================== */
import api from '../../api.js';

const TONES = { applied: 'blue', shortlisted: 'amber', selected: 'green', rejected: 'red' };
const NEXT = ['shortlisted', 'selected', 'rejected'];

export default {
  name: 'DriveApplications',
  data() { return { loading: true, error: '', driveTitle: '', companyName: '', rows: [], menu: null, acting: {} }; },
  computed: { id() { return this.$route.params.id; } },
  watch: { '$route.params.id'() { this.load(); } },
  async created() { await this.load(); },
  methods: {
    async load() {
      this.loading = true; this.error = '';
      try { const { data } = await api.get(`/company/drives/${this.id}/applications`);
        this.driveTitle = data.drive_title; this.companyName = data.company_name; this.rows = data.applicants; }
      catch (e) { this.error = (e.response && e.response.data && e.response.data.error) || 'Could not load applicants.'; }
      finally { this.loading = false; }
    },
    tone(s) { return TONES[s] || 'grey'; },
    initials(n) { return (n || 'U').split(/\s+/).slice(0, 2).map(x => x[0]).join('').toUpperCase(); },
    options(s) { return NEXT.filter(x => x !== s); },
    async setStatus(row, status) {
      this.menu = null;
      this.$set(this.acting, row.id, true);
      try { await api.put(`/company/applications/${row.id}/status`, { status }); row.status = status;
        this.$bus.$emit('toast', { type: 'success', msg: `${row.name} marked ${status}.` }); }
      catch (e) {} finally { this.$set(this.acting, row.id, false); }
    },
    async openResume(r) {
      try {
        const { data: blob } = await api.get(`/company/applications/${r.id}/resume`, { responseType: 'blob' });
        const url = URL.createObjectURL(blob);
        window.open(url);
      } catch (e) {
        if (e.response && e.response.status === 404) {
          this.$bus.$emit('toast', { type: 'warning', msg: 'No resume available for this applicant.' });
        } else {
          this.$bus.$emit('toast', { type: 'danger', msg: 'Failed to open resume.' });
        }
      }
    },
  },
  template: `
    <div data-screen-label="Drive Applications">
      <div class="page-head">
        <div class="ttl">
          <div class="cell-sub mb-1"><router-link to="/company/dashboard">Dashboard</router-link> › {{ companyName || '…' }} › Applicants</div>
          <h1>{{ driveTitle || 'Applicants' }}</h1>
        </div>
        <button class="btn btn-ghost" @click="load"><i class="bi bi-arrow-clockwise me-1"></i> Refresh</button>
      </div>

      <div class="sheet">
        <div v-if="loading" class="state-wrap"><div class="spinner-eh"></div></div>
        <div v-else-if="error" class="state-wrap"><i class="bi bi-exclamation-triangle ic"></i><h3>Couldn't load applicants</h3><p>{{ error }}</p><button class="btn btn-ghost btn-sm" @click="load">Retry</button></div>
        <div v-else-if="!rows.length" class="state-wrap"><i class="bi bi-people ic"></i><h3>No applicants yet</h3><p>Applications will appear here once students apply.</p></div>

        <template v-else>
          <div style="padding:18px 24px" class="section-title">{{ rows.length }} Total Applicants</div>
          <table class="tbl">
            <thead><tr><th>Student Name &amp; ID</th><th>Branch</th><th>CGPA</th><th>Resume</th><th>Status</th><th class="text-end">Action</th></tr></thead>
            <tbody>
              <tr v-for="r in rows" :key="r.id">
                <td>
                  <div class="d-flex align-items-center gap-3">
                    <div class="row-ava round soft">{{ initials(r.name) }}</div>
                    <div><div class="cell-strong">{{ r.name }}</div><div class="cell-sub">{{ r.roll || '—' }}</div></div>
                  </div>
                </td>
                <td>{{ r.branch }}</td>
                <td class="cell-strong">{{ (r.cgpa ?? 0).toFixed(1) }}</td>
                <td><a href="javascript:void(0)" @click="openResume(r)" class="d-inline-flex align-items-center gap-1"><i class="bi bi-file-earmark-text"></i> View</a></td>
                <td>
                  <span class="pill" :class="'tone-' + tone(r.status)"><span class="pdot"></span>{{ r.status }}</span>
                  <div v-if="r.status === 'selected'" style="margin-top:6px">
                    <router-link :to="'/company/applications/' + r.id + '/offer-letter'" style="font-size:13px">View Offer Letter</router-link>
                  </div>
                </td>
                <td class="text-end" style="position:relative">
                  <button class="btn btn-xs btn-ghost" :disabled="acting[r.id]" @click="menu = (menu === r.id ? null : r.id)"><i class="bi bi-three-dots-vertical"></i></button>
                  <div v-if="menu === r.id" class="sheet" style="position:absolute;right:18px;top:42px;z-index:20;min-width:170px;box-shadow:0 8px 24px rgba(15,30,54,.14);text-align:left">
                    <div style="padding:6px 0">
                      <a v-for="opt in options(r.status)" :key="opt" class="navlink" style="color:var(--color-text-main);padding:8px 16px;border-radius:0" @click="setStatus(r, opt)">
                        Mark {{ opt }}
                      </a>
                    </div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </template>
      </div>
      <p class="text-center cell-sub mt-4">© 2026 EduHire Portal. Institutional Data Environment.</p>
    </div>
  `,
};
