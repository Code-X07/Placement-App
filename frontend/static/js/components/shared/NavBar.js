export default {
  name: 'NavBar',
  computed: {
    role() { return this.$store.state.role },
  },
  methods: {
    logout() {
      this.$store.dispatch('logout')
      this.$router.push('/login')
    },
  },
  template: `
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
      <div class="container-fluid">
        <span class="navbar-brand">PPA</span>
        <div class="navbar-nav me-auto">
          <template v-if="role === 'admin'">
            <router-link class="nav-link" to="/admin/dashboard">Dashboard</router-link>
            <router-link class="nav-link" to="/admin/companies">Companies</router-link>
            <router-link class="nav-link" to="/admin/drives">Drives</router-link>
            <router-link class="nav-link" to="/admin/students">Students</router-link>
            <router-link class="nav-link" to="/admin/search">Search</router-link>
          </template>
          <template v-if="role === 'company'">
            <router-link class="nav-link" to="/company/dashboard">Dashboard</router-link>
            <router-link class="nav-link" to="/company/drives/new">Post Drive</router-link>
          </template>
          <template v-if="role === 'student'">
            <router-link class="nav-link" to="/student/dashboard">Dashboard</router-link>
            <router-link class="nav-link" to="/student/drives">Browse Drives</router-link>
            <router-link class="nav-link" to="/student/profile">Profile</router-link>
            <router-link class="nav-link" to="/student/applications">My Applications</router-link>
          </template>
        </div>
        <button class="btn btn-outline-light btn-sm" @click="logout">Logout</button>
      </div>
    </nav>
  `,
}
