/* ===========================================================================
   main.js — root Vue instance: top bar + role sidebar + router-view + toasts.
   The shell layout lives here (no extra file added beyond spec §6).
   =========================================================================== */
import store from './store.js';
import router from './router.js';
import api, { bus } from './api.js';
import NavBar from './components/shared/NavBar.js';

Vue.prototype.$bus = bus;
Vue.prototype.$api = api;

bus.$on('auth-expired', () => {
  store.commit('CLEAR_AUTH');
  if (router.currentRoute.path !== '/login') router.push('/login');
});

new Vue({
  router,
  store,
  components: { NavBar },
  data: { toasts: [], searchQ: '' },
  computed: {
    loggedIn() { return this.$store.getters.isLoggedIn; },
    isAdmin()  { return this.$store.getters.isAdmin; },
    user()     { return this.$store.state.user || {}; },
    showShell() { return this.loggedIn && !this.$route.meta.auth; },
    initials() {
      const n = this.user.name || this.user.company_name || this.user.email || '';
      return n.split(/[\s@.]+/).filter(Boolean).slice(0, 2).map(x => x[0]).join('').toUpperCase() || 'U';
    },
  },
  created() {
    bus.$on('toast', (t) => {
      const id = Date.now() + Math.random();
      this.toasts.push({ id, type: t.type || 'info', msg: t.msg });
      setTimeout(() => { this.toasts = this.toasts.filter(x => x.id !== id); }, 4200);
    });
  },
  methods: {
    runSearch() {
      const q = this.searchQ.trim();
      if (q) this.$router.push('/admin/search?q=' + encodeURIComponent(q));
    },
  },
  template: `
    <div>
      <template v-if="showShell">
        <header class="topbar">
          <div class="brand">EduHire Portal</div>
          <div v-if="isAdmin" class="topsearch">
            <i class="bi bi-search"></i>
            <input v-model="searchQ" @keyup.enter="runSearch" placeholder="Search students or companies…">
          </div>
        </header>
        <div class="layout">
          <nav-bar></nav-bar>
          <main class="main"><router-view></router-view></main>
        </div>
      </template>

      <template v-else>
        <router-view></router-view>
      </template>

      <div class="toast-stack">
        <div v-for="t in toasts" :key="t.id" class="toast-eh" :class="t.type">{{ t.msg }}</div>
      </div>
    </div>
  `,
}).$mount('#app');
