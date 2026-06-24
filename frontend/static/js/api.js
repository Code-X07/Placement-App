/* ===========================================================================
   api.js — single axios wrapper for every API call.
   Flip USE_MOCK to false to ship against the real Flask API. That is the only
   change required; all mock logic lives in mock.js.
   =========================================================================== */
import { mockAdapter } from './mock.js';

const USE_MOCK = false;  // <-- set to false to hit the real /api/* backend

// lightweight event bus for toasts + auth-expired (avoids store/router cycles)
export const bus = new Vue();

const api = axios.create({ baseURL: '/api', headers: { 'Content-Type': 'application/json' } });

if (USE_MOCK) api.defaults.adapter = mockAdapter;

/* attach Bearer token to every request */
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('ppa_token');
  if (token) config.headers.Authorization = 'Bearer ' + token;
  return config;
});

/* centralised error handling per brief §8 */
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const res = err.response;
    if (!res) {
      bus.$emit('toast', { type: 'danger', msg: 'Network error — could not reach the server.' });
      return Promise.reject(err);
    }
    const data = res.data || {};
    if (res.status === 401 || res.status === 422) {
      bus.$emit('auth-expired');                       // main.js clears auth + routes to /login
    } else if (res.status === 403) {
      bus.$emit('toast', { type: 'danger', msg: data.error || 'Access denied' });
    } else if (res.status >= 500) {
      bus.$emit('toast', { type: 'danger', msg: 'Something went wrong' });
    } else {
      bus.$emit('toast', { type: 'danger', msg: data.error || 'Request failed' });
    }
    return Promise.reject(err);
  }
);

export default api;
