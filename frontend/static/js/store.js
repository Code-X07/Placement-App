/* ===========================================================================
   store.js — Vuex auth store only (spec §6).
   =========================================================================== */
import api from './api.js';

Vue.use(Vuex);

// Defensive read of persisted auth. A corrupted/legacy localStorage value —
// including the literal strings "undefined"/"null" that result from storing a
// non-JSON value — must never make isLoggedIn falsely true or throw at module
// load. Any malformed piece wipes the whole auth triple (logged-out state).
function cleanStr(key) {
  const raw = localStorage.getItem(key);
  if (!raw || raw === 'undefined' || raw === 'null') return null;
  return raw;
}
function readAuth() {
  const token = cleanStr('ppa_token');
  const role = cleanStr('ppa_role');
  let user = null;
  const rawUser = localStorage.getItem('ppa_user');
  if (rawUser && rawUser !== 'undefined' && rawUser !== 'null') {
    try { user = JSON.parse(rawUser); } catch (e) { user = null; }
  }
  // require a coherent triple; otherwise treat as logged out and purge
  if (!token || !role || !user) {
    localStorage.removeItem('ppa_token');
    localStorage.removeItem('ppa_user');
    localStorage.removeItem('ppa_role');
    return { token: null, user: null, role: null };
  }
  return { token, user, role };
}

const persisted = readAuth();

const store = new Vuex.Store({
  state: {
    token: persisted.token,
    user:  persisted.user,
    role:  persisted.role,
  },
  mutations: {
    SET_AUTH(state, { token, user, role }) {
      state.token = token; state.user = user; state.role = role;
      localStorage.setItem('ppa_token', token);
      localStorage.setItem('ppa_user', JSON.stringify(user));
      localStorage.setItem('ppa_role', role);
    },
    CLEAR_AUTH(state) {
      state.token = null; state.user = null; state.role = null;
      localStorage.removeItem('ppa_token');
      localStorage.removeItem('ppa_user');
      localStorage.removeItem('ppa_role');
    },
  },
  actions: {
    async login({ commit }, credentials) {
      const { data } = await api.post('/auth/login', credentials);
      commit('SET_AUTH', data);
      return data;
    },
    async register({ commit }, payload) {
      const { data } = await api.post('/auth/register', payload);
      commit('SET_AUTH', data);
      return data;
    },
    logout({ commit }) { commit('CLEAR_AUTH'); },
  },
  getters: {
    isLoggedIn: (s) => !!s.token,
    isAdmin:    (s) => s.role === 'admin',
    isCompany:  (s) => s.role === 'company',
    isStudent:  (s) => s.role === 'student',
  },
});

export default store;
