/* ===========================================================================
   router.js — hash-mode routes + role navigation guards (spec §6).
   =========================================================================== */
import store from './store.js';

import LoginForm    from './components/shared/LoginForm.js';
import RegisterForm from './components/shared/RegisterForm.js';

import AdminDashboard from './components/admin/AdminDashboard.js';
import CompanyList    from './components/admin/CompanyList.js';
import AdminDriveList from './components/admin/DriveList.js';
import StudentList    from './components/admin/StudentList.js';
import SearchResults  from './components/admin/SearchResults.js';

import CompanyDashboard  from './components/company/CompanyDashboard.js';
import DriveCreate       from './components/company/DriveCreate.js';
import DriveApplications from './components/company/DriveApplications.js';
import OfferLetter       from './components/company/OfferLetter.js';

import StudentDashboard   from './components/student/StudentDashboard.js';
import StudentProfile     from './components/student/StudentProfile.js';
import StudentDriveList   from './components/student/DriveList.js';
import ApplicationHistory from './components/student/ApplicationHistory.js';

Vue.use(VueRouter);

const ROLES = ['admin', 'company', 'student'];

const routes = [
  { path: '/', redirect: () => { const r = store.state.role; return ROLES.includes(r) ? `/${r}/dashboard` : '/login'; } },

  { path: '/login',    component: LoginForm,    meta: { auth: true } },
  { path: '/register', component: RegisterForm, meta: { auth: true } },

  // admin
  { path: '/admin',            redirect: '/admin/dashboard' },
  { path: '/admin/dashboard',  component: AdminDashboard, meta: { role: 'admin' } },
  { path: '/admin/companies',  component: CompanyList,    meta: { role: 'admin' } },
  { path: '/admin/drives',     component: AdminDriveList, meta: { role: 'admin' } },
  { path: '/admin/students',   component: StudentList,    meta: { role: 'admin' } },
  { path: '/admin/search',     component: SearchResults,  meta: { role: 'admin' } },

  // company
  { path: '/company',                          redirect: '/company/dashboard' },
  { path: '/company/dashboard',                component: CompanyDashboard,  meta: { role: 'company' } },
  { path: '/company/drives/new', component: DriveCreate, meta: { role: 'company' },
    beforeEnter: (to, from, next) => {
      const u = store.state.user;
      if (!u || u.approval_status !== 'approved') return next('/company/dashboard');
      next();
    } },
  { path: '/company/drives/:id/applications',  component: DriveApplications, meta: { role: 'company' } },
  { path: '/company/applications/:id/offer-letter', component: OfferLetter,  meta: { role: 'company' } },

  // student
  { path: '/student',             redirect: '/student/dashboard' },
  { path: '/student/dashboard',   component: StudentDashboard,   meta: { role: 'student' } },
  { path: '/student/profile',     component: StudentProfile,     meta: { role: 'student' } },
  { path: '/student/drives',      component: StudentDriveList,   meta: { role: 'student' } },
  { path: '/student/applications',component: ApplicationHistory, meta: { role: 'student' } },

  { path: '*', redirect: '/' },
];

const router = new VueRouter({ mode: 'hash', routes });

router.beforeEach((to, from, next) => {
  const loggedIn = store.getters.isLoggedIn && ROLES.includes(store.state.role);
  const role = store.state.role;

  // auth pages bounce already-logged-in users to their dashboard
  if (to.meta.auth) {
    if (loggedIn) return next(`/${role}/dashboard`);
    return next();
  }
  // role-gated areas
  if (to.meta.role) {
    if (!loggedIn) return next('/login');
    if (role !== to.meta.role) return next(`/${role}/dashboard`);
  }
  next();
});

export default router;
