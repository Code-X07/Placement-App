/* ===========================================================================
   SearchResults.js (admin) — GET /api/admin/search?q=&type=
   No prototype image existed; built from spec §5 (brief §6.4):
   search input + student|company type toggle + adaptive results table +
   explicit empty state. Reads ?q from the top-bar search.
   =========================================================================== */
import api from '../../api.js';

const TONES = { pending: 'amber', approved: 'green', rejected: 'red' };

export default {
  name: 'SearchResults',
  data() {
    return { q: this.$route.query.q || '', type: 'student', loading: false, searched: false, error: '', results: [] };
  },
  watch: {
    '$route.query.q'(v) { this.q = v || ''; this.run(); },
  },
  created() { if (this.q) this.run(); },
  methods: {
    async run() {
      if (!this.q.trim()) { this.results = []; this.searched = false; return; }
      this.loading = true; this.error = ''; this.searched = true;
      try {
        const { data } = await api.get('/admin/search', { params: { q: this.q, type: this.type } });
        this.results = data.results;
      } catch (e) { this.error = (e.response && e.response.data && e.response.data.error) || 'Search failed.'; }
      finally { this.loading = false; }
    },
    setType(t) { this.type = t; if (this.q.trim()) this.run(); },
    tone(s) { return TONES[s] || 'grey'; },
    initials(n) { return (n || 'U').split(/\s+/).slice(0, 2).map(x => x[0]).join('').toUpperCase(); },
  },
  template: `
    <div data-screen-label="Admin Search">
      <div class="page-head">
        <div class="ttl"><h1>Search</h1><p class="page-sub">Look up students and companies across the institute.</p></div>
      </div>

      <div class="card-soft mb-3">
        <div class="d-flex gap-3 flex-wrap align-items-center">
          <div class="input-ic flex-grow-1" style="min-width:240px">
            <i class="bi bi-search"></i>
            <input v-model="q" @keyup.enter="run" class="form-control" placeholder="Search by name, email or ID…">
          </div>
          <div class="seg mb-0" style="width:240px">
            <button type="button" :class="{ on: type==='student' }" @click="setType('student')">Students</button>
            <button type="button" :class="{ on: type==='company' }" @click="setType('company')">Companies</button>
          </div>
          <button class="btn btn-action" @click="run">Search</button>
        </div>
      </div>

      <div class="sheet">
        <div v-if="loading" class="state-wrap"><div class="spinner-eh"></div></div>
        <div v-else-if="error" class="state-wrap"><i class="bi bi-exclamation-triangle ic"></i><h3>Search failed</h3><p>{{ error }}</p></div>
        <div v-else-if="!searched" class="state-wrap"><i class="bi bi-search ic"></i><h3>Start a search</h3><p>Enter a query above to find {{ type === 'company' ? 'companies' : 'students' }}.</p></div>
        <div v-else-if="!results.length" class="state-wrap"><i class="bi bi-inbox ic"></i><h3>No results</h3><p>Nothing matched “{{ q }}”. Try a different term or type.</p></div>

        <table v-else class="tbl">
          <thead>
            <tr v-if="type === 'company'"><th>Company Name</th><th>Email</th><th>Approval Status</th></tr>
            <tr v-else><th>Name</th><th>Email</th><th>Branch</th></tr>
          </thead>
          <tbody>
            <tr v-for="r in results" :key="r.id">
              <td>
                <div class="d-flex align-items-center gap-3">
                  <div class="row-ava" :class="type === 'student' ? 'round soft' : ''">{{ initials(r.name) }}</div>
                  <span class="cell-strong">{{ r.name }}</span>
                </div>
              </td>
              <td class="text-muted-2">{{ r.email }}</td>
              <td v-if="type === 'company'"><span class="pill" :class="'tone-' + tone(r.status)"><span class="pdot"></span>{{ r.status }}</span></td>
              <td v-else>{{ r.branch }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `,
};
