import store from './store.js'
import LoginForm    from './components/shared/LoginForm.js'
import RegisterForm from './components/shared/RegisterForm.js'

// Admin components
import AdminDashboard from './components/admin/AdminDashboard.js'
import CompanyList    from './components/admin/CompanyList.js'
import DriveListAdmin from './components/admin/DriveList.js'
import StudentList    from './components/admin/StudentList.js'
import SearchResults  from './components/admin/SearchResults.js'

// Company components
import CompanyDashboard  from './components/company/CompanyDashboard.js'
import DriveCreate       from './components/company/DriveCreate.js'
import DriveApplications from './components/company/DriveApplications.js'
import OfferLetter       from './components/company/OfferLetter.js'

// Student components
import StudentDashboard    from './components/student/StudentDashboard.js'
import StudentProfile      from './components/student/StudentProfile.js'
import DriveListStudent    from './components/student/DriveList.js'
import ApplicationHistory  from './components/student/ApplicationHistory.js'

Vue.use(VueRouter)

const routes = [
  { path: '/',        redirect: '/login' },
  { path: '/login',    component: LoginForm,    meta: { public: true } },
  { path: '/register', component: RegisterForm, meta: { public: true } },

  // Admin
  { path: '/admin/dashboard',  component: AdminDashboard, meta: { role: 'admin' } },
  { path: '/admin/companies',  component: CompanyList,    meta: { role: 'admin' } },
  { path: '/admin/drives',     component: DriveListAdmin, meta: { role: 'admin' } },
  { path: '/admin/students',   component: StudentList,    meta: { role: 'admin' } },
  { path: '/admin/search',     component: SearchResults,  meta: { role: 'admin' } },

  // Company
  { path: '/company/dashboard',              component: CompanyDashboard,  meta: { role: 'company' } },
  { path: '/company/drives/new',             component: DriveCreate,       meta: { role: 'company' } },
  { path: '/company/drives/:id/applications',component: DriveApplications, meta: { role: 'company' } },
  { path: '/company/applications/:id/offer-letter', component: OfferLetter, meta: { role: 'company' } },

  // Student
  { path: '/student/dashboard',    component: StudentDashboard,   meta: { role: 'student' } },
  { path: '/student/profile',      component: StudentProfile,     meta: { role: 'student' } },
  { path: '/student/drives',       component: DriveListStudent,   meta: { role: 'student' } },
  { path: '/student/applications', component: ApplicationHistory, meta: { role: 'student' } },
]

const router = new VueRouter({ mode: 'hash', routes })

router.beforeEach((to, from, next) => {
  const loggedIn = store.getters.isLoggedIn
  const role     = store.state.role

  if (to.meta.public) {
    // Redirect already-logged-in users to their dashboard
    if (loggedIn) return next(`/${role}/dashboard`)
    return next()
  }

  if (!loggedIn) return next('/login')

  if (to.meta.role && to.meta.role !== role) {
    return next(`/${role}/dashboard`)
  }

  next()
})

export default router
