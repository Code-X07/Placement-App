import api from '../../api.js'

export default {
  name: 'LoginForm',
  data() {
    return { email: '', password: '', error: '' }
  },
  methods: {
    async submit() {
      this.error = ''
      try {
        const role = await this.$store.dispatch('login', {
          email: this.email, password: this.password
        })
        this.$router.push(`/${role}/dashboard`)
      } catch (err) {
        this.error = err.response?.data?.error || 'Login failed'
      }
    },
  },
  template: `
    <div class="row justify-content-center mt-5">
      <div class="col-md-4">
        <div class="card p-4">
          <h4 class="mb-3">Sign In</h4>
          <div v-if="error" class="alert alert-danger">{{ error }}</div>
          <form @submit.prevent="submit">
            <div class="mb-3">
              <label class="form-label">Email</label>
              <input v-model="email" type="email" class="form-control" required />
            </div>
            <div class="mb-3">
              <label class="form-label">Password</label>
              <input v-model="password" type="password" class="form-control" required />
            </div>
            <button type="submit" class="btn btn-primary w-100">Login</button>
          </form>
          <p class="mt-3 text-center">
            No account? <router-link to="/register">Register</router-link>
          </p>
        </div>
      </div>
    </div>
  `,
}
