import api from '../../api.js'

export default {
  name: 'RegisterForm',
  data() {
    return {
      role: 'student', email: '', password: '',
      name: '', company_name: '', error: ''
    }
  },
  methods: {
    async submit() {
      this.error = ''
      if (this.password.length < 6) {
        this.error = 'Password must be at least 6 characters'
        return
      }
      const payload = { role: this.role, email: this.email, password: this.password }
      if (this.role === 'student') payload.name = this.name
      else payload.company_name = this.company_name
      try {
        const { data } = await api.post('/auth/register', payload)
        this.$store.commit('SET_AUTH', { token: data.token, user: data.user, role: data.role })
        this.$router.push(`/${data.role}/dashboard`)
      } catch (err) {
        this.error = err.response?.data?.error || 'Registration failed'
      }
    },
  },
  template: `
    <div class="row justify-content-center mt-5">
      <div class="col-md-5">
        <div class="card p-4">
          <h4 class="mb-3">Create Account</h4>
          <div v-if="error" class="alert alert-danger">{{ error }}</div>
          <form @submit.prevent="submit">
            <div class="mb-3">
              <label class="form-label">I am a</label>
              <select v-model="role" class="form-select">
                <option value="student">Student</option>
                <option value="company">Company / Recruiter</option>
              </select>
            </div>
            <div class="mb-3">
              <label class="form-label">Email</label>
              <input v-model="email" type="email" class="form-control" required />
            </div>
            <div class="mb-3">
              <label class="form-label">Password</label>
              <input v-model="password" type="password" class="form-control"
                     minlength="6" required />
            </div>
            <div v-if="role === 'student'" class="mb-3">
              <label class="form-label">Full Name</label>
              <input v-model="name" type="text" class="form-control" required />
            </div>
            <div v-if="role === 'company'" class="mb-3">
              <label class="form-label">Company Name</label>
              <input v-model="company_name" type="text" class="form-control" required />
            </div>
            <button type="submit" class="btn btn-success w-100">Register</button>
          </form>
          <p class="mt-3 text-center">
            Have an account? <router-link to="/login">Login</router-link>
          </p>
        </div>
      </div>
    </div>
  `,
}
