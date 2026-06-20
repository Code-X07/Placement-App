/* ===========================================================================
   mock.js — the ONLY place mock logic lives.
   api.js imports { mockAdapter } and installs it as the axios adapter when
   USE_MOCK is true. To ship against the real Flask API: set USE_MOCK = false
   in api.js. Nothing else changes.

   Seeded from the spec's sample data and tuned to exercise the states the
   build brief cares about:
     • a PENDING (unapproved) company  -> recruiting@apexanalytics.example.com
     • CSV export pending -> done -> failed  (alternates on each export)
     • EMPTY lists  (pending company has no drives; admin search w/ no match)
     • a drive that is BOTH ineligible AND already-applied (Quant Researcher)
   =========================================================================== */

const DELAY = 380; // ms — lets loading spinners actually show

/* ---------- seed data ---------------------------------------------------- */
const users = [
  { id:'u_admin', email:'admin@ppa.com',                       password:'admin123', role:'admin',   is_active:true },
  { id:'u_tech',  email:'hr@technova.example.com',             password:'company',  role:'company', is_active:true },
  { id:'u_apex',  email:'recruiting@apexanalytics.example.com',password:'company',  role:'company', is_active:true },
  { id:'u_glob',  email:'campus@globalfinance.example.com',    password:'company',  role:'company', is_active:true },
  { id:'u_syn',   email:'hello@synergymktg.example.com',       password:'company',  role:'company', is_active:false },
  { id:'u_quant', email:'hr@quantcorp.example.com',            password:'company',  role:'company', is_active:true },
  { id:'u_brand', email:'jobs@brandspark.example.com',         password:'company',  role:'company', is_active:true },
  { id:'u_alex',  email:'alex@university.edu',                 password:'student',  role:'student', is_active:true },
];

const companies = [
  { id:'cp_tech',  user_id:'u_tech',  company_name:'TechNova Solutions',  hr_contact:'hr@technova.example.com',          website:'technova.example.com',     address:'456 Innovation Drive, Tech Hub, Mumbai', approval_status:'approved' },
  { id:'cp_glob',  user_id:'u_glob',  company_name:'Global Finance Corp', hr_contact:'campus@globalfinance.example.com', website:'globalfinance.example.com', address:'789 Finance Tower, Business District, New Delhi', approval_status:'approved' },
  { id:'cp_syn',   user_id:'u_syn',   company_name:'Synergy Marketing',   hr_contact:'hello@synergymktg.example.com',    website:'synergymktg.example.com',   address:'321 Marketing Plaza, Creative Zone, Bangalore', approval_status:'rejected' },
  { id:'cp_apex',  user_id:'u_apex',  company_name:'Apex Analytics',      hr_contact:'recruiting@apexanalytics.example.com', website:'apex.example.com',     address:'1200 Innovation Way, Tech Park, San Francisco', approval_status:'pending'  },
  { id:'cp_quant', user_id:'u_quant', company_name:'QuantCorp',           hr_contact:'hr@quantcorp.example.com',         website:'quantcorp.example.com',     address:'555 Quantum Street, Financial District, Chicago', approval_status:'pending'  },
  { id:'cp_brand', user_id:'u_brand', company_name:'BrandSpark',          hr_contact:'jobs@brandspark.example.com',      website:'brandspark.example.com',    address:'789 Brand Avenue, Creative Hub, Los Angeles', approval_status:'rejected' },
];

const students = [
  { id:'sp_alex',  user_id:'u_alex', roll:'2021CS045', name:'Alex Johnson',     email:'alex@university.edu',        phone:'5551234567', branch:'Computer Science',     year:2025, cgpa:8.7, resume_path:'/uploads/resumes/alex_johnson.pdf' },
  { id:'sp_jane',  user_id:'u_j1',   roll:'2021CS012', name:'Jane Smith',       email:'jane.smith@university.edu',  phone:'5550000001', branch:'Computer Science',     year:2025, cgpa:9.2, resume_path:'/uploads/resumes/jane.pdf', is_active:true },
  { id:'sp_mike',  user_id:'u_j2',   roll:'2021EE112', name:'Michael Ramirez',  email:'m.ramirez@university.edu',   phone:'5550000002', branch:'Electrical Engineering',year:2025, cgpa:8.6, resume_path:'', is_active:true },
  { id:'sp_sara',  user_id:'u_j3',   roll:'2021ME089', name:'Sarah Lee',        email:'sarah.l@university.edu',     phone:'5550000003', branch:'Mechanical Engineering',year:2024, cgpa:9.1, resume_path:'', is_active:true },
  { id:'sp_dave',  user_id:'u_j4',   roll:'2020CE014', name:'David Thompson',   email:'d.thompson@alumni.edu',      phone:'5550000004', branch:'Civil Engineering',    year:2023, cgpa:6.9, resume_path:'', is_active:false },
];

// future deadlines so "deadline passed" never blocks apply during review
const drives = [
  { id:'d_se',    company_id:'cp_tech',  title:'Software Engineer (Frontend)', description:'Build and own customer-facing web experiences with our product team.', ctc:12.5, location:'Bangalore',         department:'Engineering', eligibility_cgpa:7.0, eligibility_branch:['Computer Science','Information Technology'], application_deadline:'2026-10-15', status:'approved', created_at:'2026-08-01' },
  { id:'d_ds',    company_id:'cp_tech',  title:'Data Science Intern',          description:'Work alongside our ML team on real recommendation problems.',           ctc:8.0,  location:'Boston (On-site)',   department:'Data Science', eligibility_cgpa:7.5, eligibility_branch:['Computer Science'],                         application_deadline:'2026-11-01', status:'approved', created_at:'2026-08-04' },
  { id:'d_pm',    company_id:'cp_tech',  title:'Product Manager',              description:'Own discovery-to-delivery for a core product surface.',                  ctc:18.0, location:'Hybrid',             department:'Product', eligibility_cgpa:8.0, eligibility_branch:[],                                            application_deadline:'2026-12-01', status:'pending',  created_at:'2026-08-09' },
  { id:'d_da',    company_id:'cp_quant', title:'Data Analyst Internship',      description:'Analytics rotation across trading and risk desks.',                      ctc:9.0,  location:'Mumbai',             department:'Analytics', eligibility_cgpa:7.0, eligibility_branch:['Computer Science','Information Technology'], application_deadline:'2026-09-30', status:'approved', created_at:'2026-07-21' },
  { id:'d_qr',    company_id:'cp_glob',  title:'Quant Researcher',             description:'Research and prototype systematic trading signals.',                     ctc:20.0, location:'Gurgaon',            department:'Research', eligibility_cgpa:9.0, eligibility_branch:['Computer Science'],                         application_deadline:'2026-10-20', status:'approved', created_at:'2026-07-30' },
  { id:'d_be',    company_id:'cp_quant', title:'Backend Developer',            description:'Scale low-latency services for our analytics platform.',                 ctc:11.0, location:'Pune',               department:'Engineering', eligibility_cgpa:7.0, eligibility_branch:['Computer Science','Information Technology'], application_deadline:'2026-11-10', status:'approved', created_at:'2026-08-12' },
  { id:'d_ma',    company_id:'cp_brand', title:'Marketing Associate Intake',   description:'Campaign and brand operations track.',                                  ctc:6.0,  location:'Pune',               department:'Marketing', eligibility_cgpa:6.0, eligibility_branch:['Marketing'],                                 application_deadline:'2026-09-25', status:'rejected', created_at:'2026-07-15' },
  { id:'d_ci',    company_id:'cp_apex',  title:'Cloud Infrastructure Engineer',description:'Own IaC and reliability for our data platform.',                         ctc:14.0, location:'Chennai, Remote',    department:'Infrastructure', eligibility_cgpa:7.0, eligibility_branch:['Computer Science','Information Technology'], application_deadline:'2026-11-05', status:'pending',  created_at:'2026-08-15' },
];

// Alex's applications. Mix of statuses; one to an ineligible drive (d_qr).
const applications = [
  { id:'a1', student_id:'sp_alex', drive_id:'d_se', applied_at:'2026-08-20', status:'selected'   },
  { id:'a2', student_id:'sp_alex', drive_id:'d_ds', applied_at:'2026-08-22', status:'applied'    },
  { id:'a3', student_id:'sp_alex', drive_id:'d_da', applied_at:'2026-08-18', status:'shortlisted'},
  { id:'a4', student_id:'sp_alex', drive_id:'d_qr', applied_at:'2026-08-25', status:'applied'    }, // ineligible (cgpa 8.7 < 9.0) AND already applied
];

// Applicants shown to the company for drive d_se (Software Engineer Frontend)
const driveApplicants = {
  d_se: [
    { id:'ap1', name:'Jane Doe',       roll:'STU-2021-0042', branch:'Computer Science',     cgpa:9.2, resume_path:'/uploads/resumes/jane_doe.pdf',   status:'selected'    },
    { id:'ap2', name:'Alex Smith',     roll:'STU-2021-0128', branch:'Information Technology',cgpa:8.8, resume_path:'/uploads/resumes/alex_smith.pdf', status:'shortlisted' },
    { id:'ap3', name:'Michael Johnson',roll:'STU-2021-0305', branch:'Computer Science',     cgpa:8.5, resume_path:'/uploads/resumes/mjohnson.pdf',   status:'applied'     },
    { id:'ap4', name:'Sarah Williams', roll:'STU-2021-0411', branch:'Electronics',          cgpa:7.4, resume_path:'/uploads/resumes/swilliams.pdf', status:'rejected'    },
  ],
};

/* ---------- helpers ------------------------------------------------------ */
const clone = (x) => JSON.parse(JSON.stringify(x));
const companyById = (id) => companies.find(c => c.id === id);
const driveById   = (id) => drives.find(d => d.id === id);

function tokenUser(config) {
  let auth = null;
  try {
    const h = config.headers || {};
    auth = h.Authorization || h.authorization || (h.get && h.get('Authorization'));
  } catch (e) { auth = null; }
  if (!auth) return null;
  const id = String(auth).replace('Bearer mock.', '').replace('Bearer ', '');
  return users.find(u => u.id === id) || null;
}

function userPayload(u) {
  const base = { id:u.id, email:u.email, role:u.role, is_active:u.is_active };
  if (u.role === 'admin')   return { ...base, name:'Administrator' };
  if (u.role === 'company') { const c = companies.find(c => c.user_id === u.id); return { ...base, company_name:c.company_name, approval_status:c.approval_status, company_id:c.id }; }
  if (u.role === 'student') { const s = students.find(s => s.user_id === u.id); return { ...base, name:s.name, branch:s.branch, cgpa:s.cgpa, student_id:s.id }; }
  return base;
}

const ok   = (data) => ({ status:200, statusText:'OK', data, headers:{}, config:{} });
const fail = (status, error, code) => ({ status, statusText:'ERR', data:{ error, code:code||'ERR' }, headers:{}, config:{} });

/* ---------- export job lifecycle (alternating done/failed) --------------- */
let exportSeq = 0;     // unique-id generator (shared)
let exportCount = 0;   // dedicated parity counter so done/failed alternates deterministically
const exportJobs = {};
function buildCsv(studentId) {
  const rows = applications.filter(a => a.student_id === studentId).map(a => {
    const d = driveById(a.drive_id); const c = companyById(d.company_id);
    return [c.company_name, d.title, a.status, a.applied_at];
  });
  const csv = 'Company,Drive Title,Application Status,Date\n' +
    rows.map(r => r.map(x => `"${x}"`).join(',')).join('\n');
  return 'data:text/csv;base64,' + btoa(unescape(encodeURIComponent(csv)));
}

/* ---------- route handlers ----------------------------------------------- */
function route(method, path, params, body, user) {
  // -------- AUTH --------
  if (method === 'post' && path === '/auth/login') {
    const u = users.find(x => x.email.toLowerCase() === (body.email||'').toLowerCase() && x.password === body.password);
    if (!u) return fail(401, 'Invalid email or password', 'BAD_CREDENTIALS');
    if (!u.is_active) return fail(403, 'This account has been deactivated', 'INACTIVE');
    return ok({ token:'mock.' + u.id, user:userPayload(u), role:u.role });
  }
  if (method === 'post' && path === '/auth/register') {
    if (body.role === 'admin') return fail(400, 'Admin accounts cannot be self-registered', 'ROLE_FORBIDDEN');
    if (users.some(x => x.email.toLowerCase() === (body.email||'').toLowerCase())) return fail(409, 'An account with this email already exists', 'DUPLICATE_EMAIL');
    const id = 'u_new_' + (++exportSeq);
    const nu = { id, email:body.email, password:body.password, role:body.role, is_active:true };
    users.push(nu);
    if (body.role === 'company') companies.push({ id:'cp_new_'+id, user_id:id, company_name:body.name||'New Company', hr_contact:body.email, website:'', address:body.address||'', approval_status:'pending' });
    if (body.role === 'student') students.push({ id:'sp_new_'+id, user_id:id, roll:'NEW', name:body.name||'New Student', email:body.email, phone:'', branch:'Computer Science', year:2026, cgpa:0, resume_path:'' });
    return ok({ token:'mock.' + id, user:userPayload(nu), role:nu.role });
  }
  if (method === 'get' && path === '/me') {
    if (!user) return fail(401, 'Token missing or expired', 'NO_TOKEN');
    return ok(userPayload(user));
  }

  // everything below requires auth
  if (!user) return fail(401, 'Token missing or expired', 'NO_TOKEN');

  // -------- ADMIN --------
  if (path.startsWith('/admin')) {
    if (user.role !== 'admin') return fail(403, 'Access denied', 'WRONG_ROLE');

    if (method === 'get' && path === '/admin/dashboard')
      return ok({ students:2450, companies:128, drives:45, applications:3120 });

    if (method === 'get' && path === '/admin/companies') {
      let list = companies.map(c => ({ id:c.id, company_name:c.company_name, hr_contact:c.hr_contact, website:c.website, approval_status:c.approval_status }));
      if (params.approval_status && params.approval_status !== 'all') list = list.filter(c => c.approval_status === params.approval_status);
      return ok(clone(list));
    }
    let m;
    if (method === 'put' && (m = path.match(/^\/admin\/companies\/(\w+)\/(approve|reject|blacklist)$/))) {
      const c = companyById(m[1]); if (!c) return fail(404, 'Company not found');
      if (m[2] === 'approve') c.approval_status = 'approved';
      if (m[2] === 'reject')  c.approval_status = 'rejected';
      if (m[2] === 'blacklist'){ c.approval_status = 'rejected'; const cu = users.find(u=>u.id===c.user_id); if(cu) cu.is_active=false; }
      return ok({ id:c.id, approval_status:c.approval_status });
    }
    if (method === 'get' && path === '/admin/drives') {
      return ok(drives.map(d => { const c = companyById(d.company_id); return { id:d.id, title:d.title, company_name:c.company_name, application_deadline:d.application_deadline, status:d.status }; }));
    }
    if (method === 'put' && (m = path.match(/^\/admin\/drives\/(\w+)\/(approve|reject)$/))) {
      const d = driveById(m[1]); if (!d) return fail(404, 'Drive not found');
      d.status = m[2] === 'approve' ? 'approved' : 'rejected';
      return ok({ id:d.id, status:d.status });
    }
    if (method === 'get' && path === '/admin/students') {
      return ok(students.map(s => ({ id:s.id, roll:s.roll, name:s.name, email:s.email, branch:s.branch, cgpa:s.cgpa, is_active:s.is_active !== false })));
    }
    if (method === 'put' && (m = path.match(/^\/admin\/students\/(\w+)\/deactivate$/))) {
      const s = students.find(s => s.id === m[1]); if (!s) return fail(404, 'Student not found');
      s.is_active = false; return ok({ id:s.id, is_active:false });
    }
    if (method === 'get' && path === '/admin/search') {
      const q = (params.q || '').trim().toLowerCase();
      const type = params.type === 'company' ? 'company' : 'student';
      if (!q) return ok({ type, results:[] });
      let results;
      if (type === 'company') results = companies.filter(c => c.company_name.toLowerCase().includes(q) || c.hr_contact.toLowerCase().includes(q))
        .map(c => ({ id:c.id, name:c.company_name, email:c.hr_contact, status:c.approval_status }));
      else results = students.filter(s => s.name.toLowerCase().includes(q) || s.email.toLowerCase().includes(q) || s.roll.toLowerCase().includes(q))
        .map(s => ({ id:s.id, name:s.name, email:s.email, branch:s.branch }));
      return ok({ type, results:clone(results) });
    }
  }

  // -------- COMPANY --------
  if (path.startsWith('/company')) {
    if (user.role !== 'company') return fail(403, 'Access denied', 'WRONG_ROLE');
    const c = companies.find(c => c.user_id === user.id);

    if (method === 'get' && path === '/company/dashboard') {
      const myDrives = drives.filter(d => d.company_id === c.id).map(d => ({
        id:d.id, title:d.title, status:d.status, application_deadline:d.application_deadline,
        location:d.location, applicant_count:(driveApplicants[d.id]||[]).length || (d.id==='d_se'?428:d.id==='d_ds'?856:0),
      }));
      const total = myDrives.reduce((s,d)=>s+d.applicant_count,0);
      return ok({ company_name:c.company_name, approval_status:c.approval_status, website:c.website,
        active_drives: myDrives.filter(d=>d.status==='approved').length, total_applicants: total, drives:myDrives });
    }
    if (c.approval_status !== 'approved') return fail(403, 'Your company account is awaiting admin approval', 'NOT_APPROVED');

    if (method === 'post' && path === '/company/drives') {
      const id = 'd_new_' + (++exportSeq);
      drives.push({ id, company_id:c.id, status:'pending', created_at:'2026-09-01', ...body, eligibility_branch: body.eligibility_branch||[] });
      return ok({ id, status:'pending' });
    }
    let m;
    if (method === 'get' && (m = path.match(/^\/company\/drives\/(\w+)\/applications$/))) {
      const d = driveById(m[1]); if (!d || d.company_id !== c.id) return fail(404, 'Drive not found');
      return ok({ drive_title:d.title, company_name:c.company_name, applicants:clone(driveApplicants[d.id] || []) });
    }
    if (method === 'put' && (m = path.match(/^\/company\/applications\/(\w+)\/status$/))) {
      for (const k in driveApplicants) { const a = driveApplicants[k].find(a => a.id === m[1]); if (a) { a.status = body.status; return ok({ id:a.id, status:a.status }); } }
      return fail(404, 'Application not found');
    }
    if (method === 'get' && (m = path.match(/^\/company\/applications\/(\w+)\/offer-letter$/))) {
      let app=null; for (const k in driveApplicants){ const a=driveApplicants[k].find(a=>a.id===m[1]); if(a){app=a;break;} }
      if (!app) return fail(404, 'Application not found');
      if (app.status !== 'selected') return fail(400, 'Offer letter is only available for selected applicants', 'NOT_SELECTED');
      return ok({
        company:{ name:c.company_name, address:['1200 Innovation Way, Tech Park','San Francisco, CA 94107'] },
        date:'October 24, 2026', student_name:app.name,
        position:'Senior Software Engineer', department:'Platform Engineering',
        ctc:'$120,000 / annum', location:'San Francisco, CA (Hybrid)',
        intro:`Following our recent discussions, we are delighted to offer you the position of Senior Software Engineer at ${c.company_name}. We were highly impressed with your academic record, technical acumen, and approach to problem-solving.`,
        body:'In this role, you will be part of our core platform engineering team, responsible for developing scalable backend microservices and contributing to our next-generation cloud infrastructure. We believe your skills will be a valuable asset to our growing engineering department.',
      });
    }
    if (method === 'get' && (m = path.match(/^\/company\/applications\/(\w+)\/resume$/))) {
      let app=null; for (const k in driveApplicants){ const a=driveApplicants[k].find(a=>a.id===m[1]); if(a){app=a;break;} }
      if (!app) return fail(404, 'No resume available');
      // Return a minimal PDF blob (data-URI placeholder)
      const pdfData = 'JVBERi0xLjQKJeLjz9MNCjEgMCBvYmo8PC9UeXBlL0NhdGFsb2cvUGFnZXM+Pj5lbmRvYjI='; // tiny PDF data-URI
      const binaryStr = atob(pdfData);
      const bytes = new Uint8Array(binaryStr.length);
      for (let i = 0; i < binaryStr.length; i++) bytes[i] = binaryStr.charCodeAt(i);
      const blob = new Blob([bytes], { type: 'application/pdf' });
      return { status:200, statusText:'OK', data:blob, headers:{ 'content-type':'application/pdf' }, config:{} };
    }
  }

  // -------- STUDENT --------
  if (path.startsWith('/student')) {
    if (user.role !== 'student') return fail(403, 'Access denied', 'WRONG_ROLE');
    const sp = students.find(s => s.user_id === user.id);

    const eligState = (d) => {
      const reasons = [];
      const applied = applications.some(a => a.student_id === sp.id && a.drive_id === d.id);
      if (applied) reasons.push('Already applied');
      if (d.eligibility_cgpa && sp.cgpa < d.eligibility_cgpa) reasons.push(`Requires CGPA ≥ ${d.eligibility_cgpa.toFixed(1)}`);
      if (Array.isArray(d.eligibility_branch) && d.eligibility_branch.length && !d.eligibility_branch.includes(sp.branch)) reasons.push('Branch not eligible');
      return { applied, eligible: reasons.filter(r=>r!=='Already applied').length===0, reasons };
    };

    if (method === 'get' && path === '/student/dashboard') {
      const my = applications.filter(a => a.student_id === sp.id);
      const counts = { applied:my.filter(a=>a.status==='applied').length, shortlisted:my.filter(a=>a.status==='shortlisted').length, selected:my.filter(a=>a.status==='selected').length, rejected:my.filter(a=>a.status==='rejected').length };
      const recommended = drives.filter(d => d.status==='approved').slice(0,3).map(d => { const c=companyById(d.company_id); return { id:d.id, title:d.title, company_name:c.company_name, ctc:d.ctc, location:d.location, application_deadline:d.application_deadline }; });
      return ok({ name:sp.name, branch:sp.branch, counts, recommended });
    }
    if (method === 'put' && path === '/student/profile') {
      Object.assign(sp, { name:body.name, phone:body.phone, branch:body.branch, year:body.year, cgpa:body.cgpa });
      return ok({ ...sp, email:user.email });
    }
    if (method === 'get' && path === '/student/profile') return ok({ ...sp, email:user.email });
    if (method === 'post' && path === '/student/profile/resume') {
      sp.resume_path = '/uploads/resumes/' + (body.filename || 'resume.pdf');
      return ok({ resume_path:sp.resume_path, filename:body.filename });
    }
    if (method === 'get' && path === '/student/drives') {
      const list = drives.filter(d => d.status === 'approved').map(d => { const c=companyById(d.company_id); const e=eligState(d);
        return { id:d.id, title:d.title, company_name:c.company_name, ctc:d.ctc, location:d.location, application_deadline:d.application_deadline,
          eligibility_cgpa:d.eligibility_cgpa, eligibility_branch:d.eligibility_branch, applied:e.applied, eligible:e.eligible, reasons:e.reasons }; });
      return ok(clone(list));
    }
    let m;
    if (method === 'post' && (m = path.match(/^\/student\/drives\/(\w+)\/apply$/))) {
      const d = driveById(m[1]); if (!d || d.status !== 'approved') return fail(400, 'This drive is not open for applications', 'NOT_OPEN');
      const e = eligState(d);
      if (e.applied) return fail(409, 'You have already applied to this drive', 'DUPLICATE');
      if (!e.eligible) return fail(400, e.reasons.join('; ') || 'You are not eligible for this drive', 'INELIGIBLE');
      applications.push({ id:'a_'+(++exportSeq), student_id:sp.id, drive_id:d.id, applied_at:'2026-09-01', status:'applied' });
      return ok({ ok:true });
    }
    if (method === 'get' && path === '/student/applications') {
      return ok(applications.filter(a => a.student_id === sp.id).map(a => { const d=driveById(a.drive_id); const c=companyById(d.company_id);
        return { id:a.id, company_name:c.company_name, location:d.location, role:d.title, applied_at:a.applied_at, status:a.status }; }));
    }
    if (method === 'post' && path === '/student/export') {
      exportSeq++; exportCount++;
      const jobId = 'job_' + exportSeq;
      // alternate: 1st export succeeds, 2nd fails, ... -> reviewer sees both states
      exportJobs[jobId] = { id:jobId, polls:0, willSucceed:(exportCount % 2 === 1), student:sp.id };
      return ok({ job_id:jobId, status:'pending' });
    }
    if (method === 'get' && (m = path.match(/^\/student\/export\/(\w+)$/))) {
      const j = exportJobs[m[1]]; if (!j) return fail(404, 'Export job not found');
      j.polls++;
      if (j.polls < 2) return ok({ job_id:j.id, status:'pending' });
      if (j.willSucceed) return ok({ job_id:j.id, status:'done', file_path:buildCsv(j.student), filename:'my_applications.csv' });
      return ok({ job_id:j.id, status:'failed', error:'Export worker failed to generate the file. Please retry.' });
    }
  }

  return fail(404, 'Not found: ' + method.toUpperCase() + ' ' + path, 'NO_ROUTE');
}

/* ---------- the adapter axios calls -------------------------------------- */
export function mockAdapter(config) {
  return new Promise((resolve) => {
    const method = (config.method || 'get').toLowerCase();
    let path = (config.url || '').split('?')[0];
    path = path.replace(/^.*\/api/, '');          // tolerate baseURL combined or not
    if (!path.startsWith('/')) path = '/' + path;
    const params = config.params || {};
    let body = {};
    try { body = config.data ? (typeof config.data === 'string' ? JSON.parse(config.data) : config.data) : {}; } catch (e) { body = {}; }
    const user = tokenUser(config);

    setTimeout(() => {
      let r;
      try { r = route(method, path, params, body, user); }
      catch (e) { r = fail(500, 'Mock error: ' + e.message, 'MOCK_CRASH'); }
      resolve({ ...r, config, request:{} });   // axios rejects when status >= 400 (default validateStatus)
    }, DELAY);
  });
}
