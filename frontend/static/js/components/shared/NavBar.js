/* ===========================================================================
   NavBar.js — role-aware LEFT sidebar (prototype skin, spec §6.1 contents).
   Same styling for all roles; only the identity + nav items + CTA change.
   =========================================================================== */
export default {
  name: 'NavBar',
  computed: {
    role()  { return this.$store.state.role; },
    user()  { return this.$store.state.user || {}; },
    name()  {
      if (this.role === 'company') return this.user.company_name || 'Company';
      return this.user.name || this.user.email || 'User';
    },
    roleLabel() {
      if (this.role === 'admin')   return 'Admin Console';
      if (this.role === 'company') return 'Company Workspace';
      if (this.role === 'student') return this.user.branch || 'Student';
      return '';
    },
    initials() {
      return (this.name || 'U').split(/[\s@.]+/).filter(Boolean).slice(0, 2).map(x => x[0]).join('').toUpperCase();
    },
    links() {
      if (this.role === 'admin') return [
        { to: '/admin/dashboard', icon: 'grid-1x2',     label: 'Dashboard' },
        { to: '/admin/companies', icon: 'building',     label: 'Companies' },
        { to: '/admin/drives',    icon: 'briefcase',    label: 'Drives' },
        { to: '/admin/students',  icon: 'people',       label: 'Students' },
        { to: '/admin/search',    icon: 'search',       label: 'Search' },
      ];
      if (this.role === 'company') return [
        { to: '/company/dashboard',  icon: 'grid-1x2',  label: 'Dashboard' },
        { to: '/company/drives/new', icon: 'plus-square', label: 'Post Drive' },
      ];
      if (this.role === 'student') return [
        { to: '/student/dashboard',    icon: 'grid-1x2',     label: 'Dashboard' },
        { to: '/student/drives',       icon: 'briefcase',    label: 'Browse Drives' },
        { to: '/student/profile',      icon: 'person',       label: 'Profile' },
        { to: '/student/applications', icon: 'file-earmark-text', label: 'My Applications' },
      ];
      return [];
    },
    showPostCta() { return this.role === 'company' && this.user.approval_status === 'approved'; },
  },
  methods: {
    logout() {
      this.$store.commit('CLEAR_AUTH');
      this.$router.push('/login');
    },
  },
  template: `
    <nav class="sidebar">
      <div class="identity">
        <div class="ava">{{ initials }}</div>
        <div>
          <div class="nm">{{ name }}</div>
          <div class="rl">{{ roleLabel }}</div>
        </div>
      </div>

      <button v-if="showPostCta" class="cta" @click="$router.push('/company/drives/new')">
        <i class="bi bi-plus-lg"></i><span>Post New Job</span>
      </button>

      <router-link v-for="l in links" :key="l.to" :to="l.to" class="navlink">
        <i :class="'bi bi-' + l.icon"></i><span>{{ l.label }}</span>
      </router-link>

      <div class="navspace"></div>
      <div class="navfoot">
        <a class="navlink" @click="logout"><i class="bi bi-box-arrow-right"></i><span>Logout</span></a>
      </div>
    </nav>
  `,
};
