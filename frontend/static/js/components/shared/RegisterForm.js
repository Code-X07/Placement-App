/* ===========================================================================
   RegisterForm.js — POST /api/auth/register. Student | Company only (admin
   excluded, spec §5). Password min 6 (brief §7 correction).
   =========================================================================== */
export default {
  name: 'RegisterForm',
  data() {
    return { role: 'student', name: '', email: '', password: '', loading: false, error: '' };
  },
  methods: {
    valid() {
      if (!this.name.trim()) { this.error = 'Enter your full name.'; return false; }
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(this.email)) { this.error = 'Enter a valid email address.'; return false; }
      if (this.password.length < 6) { this.error = 'Password must be at least 6 characters.'; return false; }
      return true;
    },
    async submit() {
      this.error = '';
      if (!this.valid()) return;
      this.loading = true;
      try {
        const { role } = await this.$store.dispatch('register', {
          role: this.role, name: this.name, email: this.email, password: this.password,
        });
        this.$bus.$emit('toast', { type: 'success', msg: 'Account created.' });
        this.$router.push('/' + role + '/dashboard');
      } catch (e) {
        this.error = (e.response && e.response.data && e.response.data.error) || 'Registration failed.';
      } finally {
        this.loading = false;
      }
    },
  },
  template: `
    <div class="auth-wrap">
      <div class="auth-card">
        <h1>EduHire Portal</h1>
        <p class="sub">Create your account to get started.</p>

        <div v-if="error" class="alert alert-danger py-2 px-3" style="border-radius:8px;font-size:14px">{{ error }}</div>

        <label class="form-label">I am a…</label>
        <div class="seg">
          <button type="button" :class="{ on: role === 'student' }" @click="role = 'student'">Student</button>
          <button type="button" :class="{ on: role === 'company' }" @click="role = 'company'">Company</button>
        </div>

        <form @submit.prevent="submit">
          <div class="mb-3">
            <label class="form-label">{{ role === 'company' ? 'Company Name' : 'Full Name' }}</label>
            <div class="input-ic">
              <i class="bi" :class="role === 'company' ? 'bi-building' : 'bi-person'"></i>
              <input v-model="name" class="form-control" :placeholder="role === 'company' ? 'Enter company name' : 'Enter your full name'">
            </div>
          </div>

          <div class="mb-3">
            <label class="form-label">Email Address</label>
            <div class="input-ic">
              <i class="bi bi-envelope"></i>
              <input v-model="email" type="email" class="form-control" placeholder="you@university.edu">
            </div>
          </div>

          <div class="mb-2">
            <label class="form-label">Password</label>
            <div class="input-ic">
              <i class="bi bi-lock"></i>
              <input v-model="password" type="password" class="form-control" placeholder="••••••••">
            </div>
            <div class="form-hint">Must be at least 6 characters long.</div>
          </div>

          <button class="btn btn-action w-100 mt-2" :disabled="loading">
            <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>{{ loading ? 'Creating…' : 'Create Account' }}
          </button>
        </form>

        <p class="text-center mt-4 mb-0" style="font-size:14px;color:var(--color-text-muted)">
          Already have an account? <router-link to="/login">Login</router-link>
        </p>
      </div>
    </div>
  `,
};
