// Axios instance — auto-attaches Bearer token, handles 401/403 globally.
const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  res => res,
  err => {
    const status = err.response?.status
    if (status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      localStorage.removeItem('role')
      window.location.hash = '#/login'
    } else if (status === 403) {
      alert(err.response?.data?.error || 'Access denied')
    }
    return Promise.reject(err)
  }
)

export default api
