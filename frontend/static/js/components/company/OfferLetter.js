/* ===========================================================================
   OfferLetter.js — GET /api/company/applications/:id/offer-letter.
   Generated on-the-fly only when application status = selected (else 400).
   Download + Print. Brief §7 PRESERVE: clean letter-of-intent layout.
   =========================================================================== */
import api from '../../api.js';

export default {
  name: 'OfferLetter',
  data() { return { loading: true, error: '', letter: null }; },
  computed: { id() { return this.$route.params.id; } },
  async created() { await this.load(); },
  methods: {
    async load() {
      this.loading = true; this.error = '';
      try { const { data } = await api.get(`/company/applications/${this.id}/offer-letter`); this.letter = data; }
      catch (e) { this.error = (e.response && e.response.data && e.response.data.error) || 'Offer letter unavailable.'; }
      finally { this.loading = false; }
    },
    print() { window.print(); },
    download() {
      const l = this.letter;
      const text = `LETTER OF INTENT\n\nDear ${l.student_name},\n\n${l.intro}\n\n${l.body}\n\nPosition: ${l.position}\nDepartment: ${l.department}\nCTC: ${l.ctc}\nJoining Date: ${l.joining_date}\nLocation: ${l.location}\n\n${l.company.name}`;
      const a = document.createElement('a');
      a.href = 'data:text/plain;charset=utf-8,' + encodeURIComponent(text);
      a.download = 'offer_letter.txt'; a.click();
    },
    initial(n) { return (n || '?')[0].toUpperCase(); },
  },
  template: `
    <div data-screen-label="Offer Letter" style="max-width:920px">
      <div class="page-head">
        <div class="ttl d-flex align-items-center gap-3">
          <button class="btn btn-ghost btn-sm" @click="$router.back()"><i class="bi bi-arrow-left"></i></button>
          <div><h1 style="font-size:24px">Offer Letter Preview</h1><p class="page-sub" v-if="letter">{{ letter.student_name }} — {{ letter.company.name }}</p></div>
        </div>
        <div v-if="letter" class="d-flex gap-2">
          <button class="btn btn-ghost" @click="download"><i class="bi bi-download me-1"></i> Download</button>
          <button class="btn btn-action" @click="print"><i class="bi bi-printer me-1"></i> Print</button>
        </div>
      </div>

      <div v-if="loading" class="state-wrap"><div class="spinner-eh"></div></div>
      <div v-else-if="error" class="card-soft state-wrap"><i class="bi bi-file-earmark-x ic"></i><h3>Offer letter unavailable</h3><p>{{ error }}</p></div>

      <div v-else class="card-soft" style="padding:48px 56px">
        <div class="d-flex justify-content-between align-items-start">
          <div class="d-flex align-items-center gap-3">
            <div class="row-ava" style="width:52px;height:52px;font-size:20px">{{ initial(letter.company.name) }}</div>
            <div>
              <h2 style="margin:0">{{ letter.company.name }}</h2>
              <div class="cell-sub" v-for="line in letter.company.address" :key="line">{{ line }}</div>
            </div>
          </div>
          <div class="text-end"><div class="cell-strong">Date</div><div class="cell-sub">{{ letter.date }}</div></div>
        </div>

        <hr class="divider" style="margin:28px 0">
        <h2 style="text-align:center;letter-spacing:.06em">LETTER OF INTENT</h2>
        <div style="width:64px;height:3px;background:var(--color-action);margin:10px auto 28px;border-radius:2px"></div>

        <p>Dear <strong>{{ letter.student_name }}</strong>,</p>
        <p>{{ letter.intro }}</p>
        <p>{{ letter.body }}</p>

        <div class="card-soft" style="background:var(--color-bg-surface);margin-top:28px;padding:28px 32px">
          <h3 style="margin:0 0 18px">Offer Details</h3>
          <div class="row g-3">
            <div class="col-5 cell-sub">Position:</div>      <div class="col-7 cell-strong">{{ letter.position }}</div>
            <div class="col-5 cell-sub">Department:</div>    <div class="col-7 cell-strong">{{ letter.department }}</div>
            <div class="col-5 cell-sub">Cost to Company:</div><div class="col-7 cell-strong" style="color:var(--color-action)">{{ letter.ctc }}</div>
            <div class="col-5 cell-sub">Joining Date:</div>  <div class="col-7 cell-strong">{{ letter.joining_date }}</div>
            <div class="col-5 cell-sub">Location:</div>      <div class="col-7 cell-strong">{{ letter.location }}</div>
          </div>
        </div>
      </div>
    </div>
  `,
};
