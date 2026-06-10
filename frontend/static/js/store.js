import api from './api.js'

Vue.use(Vuex)

const store = new Vuex.Store({
  state: {
    token: localStorage.getItem('token') || null,
    user:  (() => { try { return JSON.parse(localStorage.getItem('user') || 'null') } catch { return null } })(),
    role:  localStorage.getItem('role') || null,
  },
  mutations: {
    SET_AUTH(state, { token, user, role }) {
      state.token = token
      state.user  = user
      state.role  = role
      localStorage.setItem('token', token)
      localStorage.setItem('user', JSON.stringify(user))
      localStorage.setItem('role', role)
    },
    CLEAR_AUTH(state) {
      state.token = null
      state.user  = null
      state.role  = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      localStorage.removeItem('role')
    },
  },
  actions: {
    async login({ commit }, credentials) {
      const { data } = await api.post('/auth/login', credentials)
      commit('SET_AUTH', { token: data.token, user: data.user, role: data.role })
      return data.role
    },
    logout({ commit }) {
      commit('CLEAR_AUTH')
    },
  },
  getters: {
    isLoggedIn:  s => !!s.token,
    isAdmin:     s => s.role === 'admin',
    isCompany:   s => s.role === 'company',
    isStudent:   s => s.role === 'student',
  },
})

export default store
