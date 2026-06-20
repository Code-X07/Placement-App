/* ===========================================================================
   LoginForm.js — POST /api/auth/login. Prototype skin + 4 data states.
   =========================================================================== */
export default {
  name: 'LoginForm',
  data() {
    return { email: '', password: '', show: false, remember: false, loading: false, error: '' };
  },
  methods: {
    valid() {
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(this.email)) { this.error = 'Enter a valid email address.'; return false; }
      if (!this.password) { this.error = 'Enter your password.'; return false; }
      return true;
    },
    async submit() {
      this.error = '';
      if (!this.valid()) return;
      this.loading = true;
      try {
        const { role } = await this.$store.dispatch('login', { email: this.email, password: this.password });
        this.$bus.$emit('toast', { type: 'success', msg: 'Welcome back!' });
        this.$router.push('/' + role + '/dashboard');
      } catch (e) {
        this.error = (e.response && e.response.data && e.response.data.error) || 'Login failed.';
      } finally {
        this.loading = false;
      }
    },
  },
  template: `
    <div class="auth-wrap">
      <div class="auth-card">
        <h1>EduHire Portal</h1>
        <p class="sub">Sign in to your account</p>

        <div v-if="error" class="alert alert-danger py-2 px-3" style="border-radius:8px;font-size:14px">{{ error }}</div>

        <form @submit.prevent="submit">
          <div class="mb-3">
            <label class="form-label">Email Address</label>
            <input v-model="email" type="email" class="form-control" placeholder="Enter your email" autocomplete="username">
          </div>

          <div class="mb-2">
            <label class="form-label">Password</label>
            <div class="input-ic">
              <input :type="show ? 'text' : 'password'" v-model="password" class="form-control" style="padding-left:12px" placeholder="Enter your password" autocomplete="current-password">
              <i class="bi eye" :class="show ? 'bi-eye' : 'bi-eye-slash'" @click="show = !show"></i>
            </div>
          </div>

          <div class="d-flex justify-content-between align-items-center mb-3">
            <label class="d-flex align-items-center gap-2 mb-0" style="font-size:14px;color:var(--color-text-muted)">
              <input type="checkbox" v-model="remember"> Remember me
            </label>
            <a href="#" @click.prevent>Forgot password?</a>
          </div>

          <button class="btn btn-action w-100" :disabled="loading">
            <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>{{ loading ? 'Signing in…' : 'Login' }}
          </button>
        </form>

        <p class="text-center mt-4 mb-0" style="font-size:14px;color:var(--color-text-muted)">
          Don't have an account? <router-link to="/register">Register</router-link>
        </p>
        <p class="text-center mt-2 mb-0" style="font-size:12.5px;color:var(--color-text-muted)">
          Demo: admin@ppa.com · hr@technova.example.com · recruiting@apexanalytics.example.com · alex@university.edu
        </p>
      </div>
    </div>
  `,
};
