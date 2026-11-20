import React, { useEffect, useState } from "react";
import { Link, Navigate, Route, Routes, useNavigate, useParams } from "react-router-dom";
import {
  Activity, BarChart3, BookOpen, ChevronRight, GraduationCap, History,
  LayoutDashboard, LogOut, Menu, Moon, ShieldCheck, Sun, Target,
  TrendingUp, UserRound, Users, X, BrainCircuit, Settings, ClipboardList,
  CalendarDays, ShieldAlert, Bell, Bot, MessageSquare, CheckCircle2, Plus,
} from "lucide-react";
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Legend,
  Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { jsPDF } from "jspdf";
import api, { getApiErrorMessage, reportApiError } from "./api";

function useAuth() {
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(
        localStorage.getItem("edupredict_user") ||
        sessionStorage.getItem("edupredict_user")
      );
    }
    catch { return null; }
  });
  const login = (token, nextUser, remember = true) => {
    localStorage.removeItem("edupredict_token");
    localStorage.removeItem("edupredict_user");
    sessionStorage.removeItem("edupredict_token");
    sessionStorage.removeItem("edupredict_user");
    const storage = remember ? localStorage : sessionStorage;
    storage.setItem("edupredict_token", token);
    storage.setItem("edupredict_user", JSON.stringify(nextUser));
    setUser(nextUser);
  };
  const logout = () => {
    localStorage.removeItem("edupredict_token");
    localStorage.removeItem("edupredict_user");
    sessionStorage.removeItem("edupredict_token");
    sessionStorage.removeItem("edupredict_user");
    setUser(null);
  };
  return { user, login, logout };
}

function ThemeToggle() {
  const [theme, setTheme] = useState(() => localStorage.getItem("edupredict_theme") || "dark");
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("edupredict_theme", theme);
  }, [theme]);
  return (
    <button className="icon-button" aria-label="Toggle theme" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
      {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
    </button>
  );
}

function ApiNotifications() {
  const [message, setMessage] = useState("");
  useEffect(() => {
    let timer;
    const show = (event) => {
      setMessage(event.detail);
      window.clearTimeout(timer);
      timer = window.setTimeout(() => setMessage(""), 6000);
    };
    window.addEventListener("edupredict:api-error", show);
    return () => {
      window.removeEventListener("edupredict:api-error", show);
      window.clearTimeout(timer);
    };
  }, []);
  return message ? <div className="api-notification" role="alert">{message}</div> : null;
}

function PublicNav() {
  const [open, setOpen] = useState(false);
  return (
    <nav className="public-nav">
      <Link className="brand" to="/"><span className="brand-mark"><GraduationCap /></span><span>EduPredict</span></Link>
      <button className="icon-button mobile-menu" onClick={() => setOpen(!open)}>{open ? <X /> : <Menu />}</button>
      <div className={open ? "public-links open" : "public-links"}>
        <a href="#home">Home</a><a href="#features">Features</a><a href="#how">How It Works</a>
        <a href="#about">About</a><a href="#contact">Contact</a>
        <ThemeToggle />
        <Link className="button ghost" to="/login">Login</Link>
        <Link className="button primary" to="/register">Get Started</Link>
      </div>
    </nav>
  );
}

function Landing() {
  return (
    <div className="landing">
      <PublicNav />
      <header className="hero" id="home">
        <div className="hero-copy">
          <div className="eyebrow"><BrainCircuit size={16} /> AI-powered academic insights</div>
          <h1>Predict Your Academic Future with AI</h1>
          <p>Transform academic data into meaningful insights, discover your strengths and make smarter decisions about your educational journey.</p>
          <div className="hero-actions">
            <Link className="button primary large" to="/register">Get Started <ChevronRight size={18} /></Link>
            <a className="button ghost large" href="#features">Explore Features</a>
          </div>
        </div>
        <div className="hero-visual">
          <div className="orb orb-one" /><div className="orb orb-two" />
          <div className="analytics-card">
            <div className="card-heading"><span>Performance forecast</span><span className="live-dot">Live</span></div>
            <div className="forecast"><span>82</span><small>/100</small></div>
            <div className="mini-bars">{[52,64,58,76,69,84,82].map((v,i) => <i key={i} style={{height:`${v}%`}} />)}</div>
            <div className="forecast-footer"><TrendingUp size={17} /> 8.4% predicted improvement</div>
          </div>
        </div>
      </header>
      <section className="section" id="features">
        <div className="section-heading"><span>Platform capabilities</span><h2>Everything needed to understand academic progress</h2></div>
        <div className="feature-grid">
          {[
            [BrainCircuit,"AI Prediction","Actual regression-based academic score predictions."],
            [BarChart3,"Academic Analytics","Interactive trends across subjects and assessments."],
            [Activity,"Performance Visualization","Clear charts for study, attendance and examination data."],
            [Target,"Personalized Recommendations","Transparent, rule-based actions matched to student inputs."],
            [ShieldCheck,"Risk Identification","Identify areas that may need timely academic support."],
            [TrendingUp,"Progress Tracking","Compare predictions over time and monitor improvement."],
          ].map(([Icon,title,text]) => <article className="feature-card" key={title}><Icon /><h3>{title}</h3><p>{text}</p></article>)}
        </div>
      </section>
      <section className="section how" id="how">
        <div className="section-heading"><span>How it works</span><h2>From academic data to clear next steps</h2></div>
        <div className="steps">
          {["Enter academic information","AI analyses performance","Generate predictions","Receive recommendations"].map((title,i)=><div className="step" key={title}><b>0{i+1}</b><h3>{title}</h3></div>)}
        </div>
      </section>
      <section className="section split" id="about">
        <div><span className="eyebrow">About EduPredict</span><h2>Designed for informed, responsible academic decisions</h2></div>
        <p>EduPredict combines a transparent machine learning workflow with practical academic analytics. Predictions are decision-support insights, not guaranteed examination outcomes.</p>
      </section>
      <footer id="contact"><div className="brand"><span className="brand-mark"><GraduationCap /></span><span>EduPredict</span></div><p>Questions or institutional enquiries: support@edupredict.local</p><span>© 2026 EduPredict</span></footer>
    </div>
  );
}

function AuthPage({ mode, auth }) {
  const navigate = useNavigate();
  const [form, setForm] = useState({ full_name:"", email:"", password:"", confirm_password:"", institution_name:"", department:"", course:"", semester:"", academic_year:"", admin_username:"", admin_password:"", remember:true });
  const [error,setError] = useState(""); const [loading,setLoading] = useState(false);
  const set = e => setForm({...form,[e.target.name]:e.target.type==="checkbox"?e.target.checked:e.target.value});
  const requestReset = async () => {
    if (!form.email) {
      setError("Enter your email address before requesting a password reset.");
      return;
    }
    try {
      await api.post("/api/auth/password-reset/request", { email: form.email });
      setError("");
    } catch (err) {
      setError(err.response?.data?.detail || "Password reset is currently unavailable.");
    }
  };
  const submit = async e => {
    e.preventDefault(); setLoading(true); setError("");
    try {
      if (mode === "admin") {
        const res = await api.post("/api/admin/login",{username:form.admin_username,password:form.admin_password});
        auth.login(res.data.access_token,res.data.user); navigate("/admin");
      } else if (mode === "register") {
        if (form.password !== form.confirm_password) throw new Error("Passwords do not match");
        const res = await api.post("/api/auth/register",form);
        auth.login(res.data.access_token,res.data.user); navigate("/dashboard");
      } else {
        const res = await api.post("/api/auth/login",{email:form.email,password:form.password});
        auth.login(res.data.access_token,res.data.user,form.remember); navigate(res.data.user.role==="admin"?"/admin":res.data.user.role==="teacher"?"/teacher":res.data.user.role==="institution_admin"?"/institution":"/dashboard");
      }
    } catch(err) { setError(getApiErrorMessage(err)); }
    finally { setLoading(false); }
  };
  return (
    <div className="auth-page"><Link className="brand auth-brand" to="/"><span className="brand-mark"><GraduationCap /></span><span>EduPredict</span></Link>
      <div className="auth-card">
        <div className="auth-heading"><span>{mode==="admin"?"Admin access":mode==="register"?"Create account":"Welcome back"}</span><h1>{mode==="admin"?"Administrator login":mode==="register"?"Start your academic journey":"Sign in to EduPredict"}</h1></div>
        {error && <div className="alert">{error}</div>}
        <form onSubmit={submit}>
          {mode==="register" && <><label>Full Name<input name="full_name" value={form.full_name} onChange={set} required /></label><div className="form-grid">
            <label>Institution Name<input name="institution_name" value={form.institution_name} onChange={set}/></label>
            <label>Department<input name="department" value={form.department} onChange={set}/></label>
            <label>Course<input name="course" value={form.course} onChange={set}/></label>
            <label>Semester<select name="semester" value={form.semester} onChange={set}><option value="">Select</option><option>1</option><option>2</option><option>3</option><option>4</option><option>5</option><option>6</option><option>7</option><option>8</option></select></label>
            <label>Academic Year<input name="academic_year" value={form.academic_year} onChange={set} placeholder="2025-2026"/></label>
          </div></>}
          {mode==="admin" ? <><label>Username<input name="admin_username" value={form.admin_username} onChange={set} required /></label><label>Password<input type="password" name="admin_password" value={form.admin_password} onChange={set} required /></label></> :
          <><label>Email Address<input type="email" name="email" value={form.email} onChange={set} required /></label><label>Password<input type="password" name="password" value={form.password} onChange={set} required /></label></>}
          {mode==="register" && <><label>Confirm Password<input type="password" name="confirm_password" value={form.confirm_password} onChange={set} required /></label></>}
          {mode==="login" && <div className="form-options"><label className="checkbox"><input type="checkbox" name="remember" checked={form.remember} onChange={set}/> Remember me</label><button type="button" className="text-button" onClick={requestReset}>Forgot password</button></div>}
          <button className="button primary full" disabled={loading}>{loading?"Please wait...":mode==="register"?"Create Account":mode==="admin"?"Sign in as Administrator":"Sign In"}</button>
        </form>
        {mode==="login" && <p className="auth-switch">New to EduPredict? <Link to="/register">Create an account</Link></p>}
        {mode==="register" && <p className="auth-switch">Already registered? <Link to="/login">Sign in</Link></p>}
        {mode==="admin" && <p className="auth-switch"><Link to="/login">Student login</Link></p>}
      </div>
    </div>
  );
}

function AppShell({ auth, admin=false, children }) {
  const navigate = useNavigate(); const [open,setOpen]=useState(false);
  const logout=()=>{auth.logout();navigate("/");};
  const role=auth.user?.role;
  const items = admin ? [
    ["/admin",LayoutDashboard,"Overview"],["/admin/users",Users,"Students"],["/admin/teaching",GraduationCap,"Teaching Staff"],["/admin/predictions",History,"Predictions"],["/admin/models",BrainCircuit,"ML Models"],["/admin/analytics",BarChart3,"Analytics"],["/admin/audit",ClipboardList,"Audit Log"],["/admin/settings",Settings,"Settings"]
  ] : role==="teacher" ? [
    ["/teacher",LayoutDashboard,"Teacher Overview"],["/teacher/students",Users,"Assigned Students"],["/profile",UserRound,"My Profile"]
  ] : role==="institution_admin" ? [
    ["/institution",BarChart3,"Institution Analytics"],["/profile",UserRound,"My Profile"]
  ] : [
    ["/dashboard",LayoutDashboard,"Overview"],["/predict",Target,"Predict Performance"],["/simulate",Activity,"What-if Simulator"],["/risk",ShieldAlert,"Risk Assessment"],["/study-plan",CalendarDays,"Study Planner"],["/activities",ClipboardList,"Activity Tracker"],["/goals",CheckCircle2,"Study Goals"],["/assistant",Bot,"AI Assistant"],["/notifications",Bell,"Notifications"],["/predictions",History,"My Predictions"],["/analytics",BarChart3,"Academic Analytics"],["/recommendations",Activity,"Recommendations"],["/profile",UserRound,"My Profile"]
  ];
  return (
    <div className="app-shell">
      <aside className={open?"sidebar open":"sidebar"}>
        <Link className="brand sidebar-brand" to={admin?"/admin":"/dashboard"}><span className="brand-mark"><GraduationCap/></span><span>EduPredict</span></Link>
        <nav>{items.map(([path,Icon,label])=><Link to={path} key={path} onClick={()=>setOpen(false)}><Icon size={18}/><span>{label}</span></Link>)}</nav>
        <button className="logout" onClick={logout}><LogOut size={18}/><span>Logout</span></button>
      </aside>
      {open && <button className="sidebar-backdrop" aria-label="Close menu" onClick={()=>setOpen(false)}/>}
      <main className="main-area">
        <header className="topbar"><button className="icon-button mobile-menu" onClick={()=>setOpen(true)}><Menu/></button><div><small>{admin?"Administration":"Student workspace"}</small><strong>{auth.user?.full_name}</strong></div><ThemeToggle/><button className="avatar" onClick={()=>navigate(admin?"/admin":"/profile")}>{auth.user?.full_name?.slice(0,1)||"U"}</button></header>
        <div className="content">{children}</div>
      </main>
    </div>
  );
}

function StatCards({items}) {
  return <div className="stat-grid">{items.map(([Icon,label,value],i)=><article className="stat-card" key={label}><div className="stat-icon"><Icon/></div><div><span>{label}</span><strong>{value ?? "—"}</strong></div></article>)}</div>
}

function Dashboard() {
  const [data,setData]=useState(null); const [trends,setTrends]=useState([]); const [subjects,setSubjects]=useState([]);
  useEffect(()=>{Promise.all([api.get("/api/student/dashboard"),api.get("/api/analytics/trends"),api.get("/api/analytics/subjects")]).then(([d,t,s])=>{setData(d.data);setTrends(t.data);setSubjects(s.data)}).catch(reportApiError)},[]);
  if(!data) return <div className="loading-page"><span className="spinner"/>Loading dashboard...</div>;
  return <>
    <div className="page-heading"><div><span>Overview</span><h1>Welcome back, {data.welcome_name}</h1></div><Link className="button primary" to="/predict">New prediction</Link></div>
    <StatCards items={[
      [BookOpen,"Total assessments",data.total_assessments],[Target,"Latest predicted score",data.latest_predicted_score?[`${data.latest_predicted_score}%`]:null],[Activity,"Performance level",data.academic_performance_level],[TrendingUp,"Attendance",data.attendance_percentage?`${data.attendance_percentage}%`:"—"],[TrendingUp,"Improvement trend",data.improvement_trend]
    ]}/>
    {data.total_assessments===0 ? <div className="empty-state"><div className="empty-icon"><BrainCircuit/></div><h2>Create your first prediction</h2><p>Enter your academic information to receive a transparent model estimate and personalized improvement recommendations.</p><Link className="button primary" to="/predict">Create prediction</Link></div> :
    <><div className="chart-grid"><article className="panel"><div className="panel-heading"><div><span>Progress</span><h3>Academic performance trend</h3></div></div><ResponsiveContainer width="100%" height={260}><AreaChart data={trends}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="date"/><YAxis domain={[0,100]}/><Tooltip/><Area type="monotone" dataKey="score" stroke="#7566F1" fill="#7566F1" fillOpacity={.18}/></AreaChart></ResponsiveContainer></article>
    <article className="panel"><div className="panel-heading"><div><span>Subjects</span><h3>Subject-wise performance</h3></div></div><ResponsiveContainer width="100%" height={260}><BarChart data={subjects}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="subject"/><YAxis domain={[0,100]}/><Tooltip/><Bar dataKey="score" fill="#7566F1" radius={[6,6,0,0]}/></BarChart></ResponsiveContainer></article></div>
    <article className="panel"><div className="panel-heading"><div><span>Recent activity</span><h3>Prediction history</h3></div><Link className="text-link" to="/predictions">View all</Link></div><div className="table-wrap"><table><thead><tr><th>ID</th><th>Date</th><th>Subject</th><th>Score</th><th>Category</th></tr></thead><tbody>{data.recent_predictions.map(p=><tr key={p.id}><td>#{p.id}</td><td>{new Date(p.created_at).toLocaleDateString()}</td><td>{p.subject}</td><td><strong>{p.predicted_score}%</strong></td><td><span className="badge">{p.performance_category}</span></td></tr>)}</tbody></table></div></article></>}
  </>;
}

function PredictionForm() {
  const navigate=useNavigate();
  const [form,setForm]=useState({subject:"",semester:"",study_hours:4,previous_marks:70,attendance:85,assignment_scores:75,class_participation:70,homework_completion:80,sleep_hours:7,extracurricular:false,internet_access:true,family_support:true});
  const [loading,setLoading]=useState(false),[error,setError]=useState("");
  const set=e=>setForm({...form,[e.target.name]:e.target.type==="checkbox"?e.target.checked:e.target.type==="number"?Number(e.target.value):e.target.value});
  const submit=async e=>{e.preventDefault();setLoading(true);setError("");try{const res=await api.post("/api/predictions/predict",form);navigate(`/predictions/${res.data.id}`)}catch(err){setError(getApiErrorMessage(err))}finally{setLoading(false)}};
  const numberFields=[
    ["study_hours","Study Hours Per Day",0,16,0.5],["previous_marks","Previous Examination Marks",0,100,1],["attendance","Attendance Percentage",0,100,1],["assignment_scores","Assignment Scores",0,100,1],["class_participation","Class Participation",0,100,1],["homework_completion","Homework Completion",0,100,1],["sleep_hours","Sleep Hours",0,16,0.5]
  ];
  return <><div className="page-heading"><div><span>Prediction</span><h1>Predict academic performance</h1></div></div>
    <article className="panel prediction-panel">{error&&<div className="alert">{error}</div>}<form onSubmit={submit}>
      <div className="form-grid"><label>Subject<input name="subject" value={form.subject} onChange={set} placeholder="e.g. Mathematics" required/></label><label>Semester<select name="semester" value={form.semester} onChange={set} required><option value="">Select semester</option>{[1,2,3,4,5,6,7,8].map(v=> <option key={v} value={String(v)}>{v}</option>)}</select></label></div>
      <div className="input-grid">{numberFields.map(([name,label,min,max,step])=><label key={name}>{label}<input type="number" name={name} value={form[name]} onChange={set} min={min} max={max} step={step}/></label>)}</div>
      <div className="toggle-grid"><label className="checkbox"><input type="checkbox" name="extracurricular" checked={form.extracurricular} onChange={set}/> Extracurricular activities</label><label className="checkbox"><input type="checkbox" name="internet_access" checked={form.internet_access} onChange={set}/> Internet access</label><label className="checkbox"><input type="checkbox" name="family_support" checked={form.family_support} onChange={set}/> Family educational support</label></div>
      <button className="button primary full" disabled={loading}>{loading?"Generating prediction...":"Generate Prediction"}</button>
    </form></article></>;
}

function WhatIfSimulator() {
  const defaults={subject:"Mathematics",semester:"1",study_hours:4,previous_marks:70,attendance:85,assignment_scores:75,class_participation:70,homework_completion:80,sleep_hours:7,extracurricular:false,internet_access:true,family_support:true};
  const [baseline,setBaseline]=useState(defaults);
  const [scenario,setScenario]=useState({...defaults,study_hours:6,attendance:90,assignment_scores:82});
  const [result,setResult]=useState(null);
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState("");
  const fields=[
    ["study_hours","Study hours per day",0,16,0.5],
    ["previous_marks","Previous marks",0,100,1],
    ["attendance","Attendance (%)",0,100,1],
    ["assignment_scores","Assignment scores",0,100,1],
    ["class_participation","Class participation",0,100,1],
    ["homework_completion","Homework completion",0,100,1],
    ["sleep_hours","Sleep hours",0,16,0.5],
  ];
  const update=(setter,key,value)=>setter(current=>({...current,[key]:value}));
  const submit=async()=>{
    setLoading(true);setError("");setResult(null);
    try{
      const response=await api.post("/api/predictions/simulate",{
        baseline:{...baseline,subject:baseline.subject.trim(),semester:String(baseline.semester)},
        scenario:{...scenario,subject:baseline.subject.trim(),semester:String(baseline.semester)},
      });
      setResult(response.data);
    }catch(err){setError(getApiErrorMessage(err))}
    finally{setLoading(false)}
  };
  const renderFields=(values,setter,label)=><article className="panel simulator-card">
    <h3>{label}</h3>
    {fields.map(([key,title,min,max,step])=><label className="simulator-field" key={key}>{title}<input type="number" min={min} max={max} step={step} value={values[key]} onChange={e=>update(setter,key,Number(e.target.value))}/></label>)}
    <div className="toggle-grid">
      {["extracurricular","internet_access","family_support"].map(key=><label className="checkbox" key={key}><input type="checkbox" checked={values[key]} onChange={e=>update(setter,key,e.target.checked)}/>{key.replaceAll("_"," ")}</label>)}
    </div>
  </article>;
  return <>
    <div className="page-heading"><div><span>Scenario planning</span><h1>What-if performance simulator</h1></div></div>
    <article className="panel"><div className="form-grid">
      <label>Subject<input value={baseline.subject} onChange={e=>{setBaseline(v=>({...v,subject:e.target.value}));setScenario(v=>({...v,subject:e.target.value}))}} required/></label>
      <label>Semester<select value={baseline.semester} onChange={e=>{setBaseline(v=>({...v,semester:e.target.value}));setScenario(v=>({...v,semester:e.target.value}))}}>{[1,2,3,4,5,6,7,8].map(v=><option key={v} value={String(v)}>{v}</option>)}</select></label>
    </div></article>
    <div className="simulator-grid">{renderFields(baseline,setBaseline,"Current baseline")}{renderFields(scenario,setScenario,"Proposed scenario")}</div>
    {error&&<div className="alert">{error}</div>}
    <button className="button primary" disabled={loading||!baseline.subject.trim()} onClick={submit}>{loading?"Comparing scenarios...":"Compare scenarios"}</button>
    {result&&<article className="panel simulator-result"><span className="eyebrow">Same deployed model · {result.model_version}</span><div className="simulator-result-grid">
      <div><span>Current estimate</span><strong>{result.baseline_score.toFixed(1)}</strong></div>
      <div><span>Scenario estimate</span><strong>{result.scenario_score.toFixed(1)}</strong></div>
      <div><span>Estimated difference</span><strong className={result.change>=0?"positive":"negative"}>{result.change>0?"+":""}{result.change.toFixed(1)}</strong></div>
    </div><p className="muted">{result.disclaimer}</p><p className="muted">Dataset: {result.dataset}. {result.is_synthetic_demo?"Demonstration data only; this is not validated evidence about real student outcomes.":""}</p></article>}
  </>;
}

function PredictionHistory() {
  const navigate=useNavigate();const [data,setData]=useState({items:[],total:0});
  const [search,setSearch]=useState("");const [category,setCategory]=useState("");
  const [page,setPage]=useState(1);
  useEffect(()=>{api.get("/api/predictions/history",{params:{search:search||undefined,category:category||undefined,page,page_size:10}}).then(r=>setData(r.data)).catch(reportApiError)},[search,category,page]);
  useEffect(()=>setPage(1),[search,category]);
  const remove=async(id)=>{if(!window.confirm("Delete this prediction?"))return;try{await api.delete(`/api/predictions/${id}`);setData({...data,items:data.items.filter(p=>p.id!==id),total:data.total-1})}catch(err){reportApiError(err)}};
  return <><div className="page-heading"><div><span>History</span><h1>My predictions</h1></div></div>
    <div className="filters"><input placeholder="Search subject" value={search} onChange={e=>setSearch(e.target.value)}/><select value={category} onChange={e=>setCategory(e.target.value)}><option value="">All categories</option><option>Excellent</option><option>Good</option><option>Average</option><option>Needs Improvement</option></select></div>
    {data.items.length===0?<div className="empty-state"><History/><h2>No predictions found</h2><p>Create an assessment to begin your prediction history.</p><Link className="button primary" to="/predict">Predict performance</Link></div>:<article className="panel"><div className="table-wrap"><table><thead><tr><th>ID</th><th>Date</th><th>Subject</th><th>Score</th><th>Category</th><th>Actions</th></tr></thead><tbody>{data.items.map(p=><tr key={p.id}><td>#{p.id}</td><td>{new Date(p.created_at).toLocaleDateString()}</td><td>{p.subject}</td><td><strong>{p.predicted_score}%</strong></td><td><span className="badge">{p.performance_category}</span></td><td><button className="text-button" onClick={()=>navigate(`/predictions/${p.id}`)}>View</button><button className="text-button danger" onClick={()=>remove(p.id)}>Delete</button></td></tr>)}</tbody></table></div><div className="pagination"><button className="button ghost" disabled={page<=1} onClick={()=>setPage(page-1)}>Previous</button><span>Page {page} of {Math.max(1,Math.ceil(data.total/10))}</span><button className="button ghost" disabled={page>=Math.ceil(data.total/10)} onClick={()=>setPage(page+1)}>Next</button></div></article>}
  </>;
}

function PredictionDetail() {
  const {id}=useParams();
  const [p,setP]=useState(null);
  const [explanation,setExplanation]=useState(null);
  const [explanationError,setExplanationError]=useState("");
  useEffect(()=>{api.get(`/api/predictions/${id}`).then(r=>setP(r.data)).catch(reportApiError)},[id]);
  useEffect(()=>{
    setExplanation(null);
    setExplanationError("");
    api.get(`/api/predictions/${id}/explanation`)
      .then(r=>setExplanation(r.data))
      .catch(err=>setExplanationError(getApiErrorMessage(err)));
  },[id]);
  const downloadReport=async()=>{
    if(!p)return;
    const pdf=new jsPDF({orientation:"portrait",unit:"mm",format:"a4"});
    const pageWidth=pdf.internal.pageSize.getWidth();
    const pageHeight=pdf.internal.pageSize.getHeight();
    const margin=17;
    const contentWidth=pageWidth-margin*2;
    let y=18;
    pdf.setProperties({
      title:`EduPredict Prediction Report - ${p.subject}`,
      subject:"Academic performance prediction",
      author:"EduPredict",
    });
    pdf.setFillColor(17,24,43);
    pdf.roundedRect(margin,y,contentWidth,31,3,3,"F");
    pdf.setTextColor(248,250,252);
    pdf.setFont("helvetica","bold");
    pdf.setFontSize(18);
    pdf.text("EduPredict",margin+7,y+11);
    pdf.setFont("helvetica","normal");
    pdf.setFontSize(9);
    pdf.text("ACADEMIC PERFORMANCE FORECAST",margin+7,y+20);
    pdf.text(`Report #${p.id}`,pageWidth-margin-7,y+11,{align:"right"});
    y+=40;

    const ensureSpace=(height)=>{
      if(y+height>pageHeight-20){
        pdf.addPage();
        y=19;
      }
    };
    const addSection=(title)=>{
      ensureSpace(13);
      pdf.setTextColor(81,69,205);
      pdf.setFont("helvetica","bold");
      pdf.setFontSize(12);
      pdf.text(title,margin,y);
      y+=4;
      pdf.setDrawColor(226,230,239);
      pdf.line(margin,y,pageWidth-margin,y);
      y+=6;
    };
    const addRow=(label,value)=>{
      const wrapped=pdf.splitTextToSize(String(value),contentWidth-47);
      const rowHeight=Math.max(6,wrapped.length*4.5);
      ensureSpace(rowHeight+3);
      pdf.setFontSize(9);
      pdf.setTextColor(101,113,138);
      pdf.setFont("helvetica","bold");
      pdf.text(label,margin,y);
      pdf.setTextColor(23,32,51);
      pdf.setFont("helvetica","normal");
      pdf.text(wrapped,margin+47,y);
      y+=rowHeight+3;
    };
    const addRecommendation=(recommendation)=>{
      const actionLines=pdf.splitTextToSize(recommendation.action,contentWidth-8);
      const benefitLines=pdf.splitTextToSize(`Benefit: ${recommendation.benefit}`,contentWidth-8);
      const blockHeight=8+actionLines.length*4.5+benefitLines.length*4.5+6;
      ensureSpace(blockHeight);
      pdf.setDrawColor(226,230,239);
      pdf.setFillColor(255,255,255);
      pdf.roundedRect(margin,y,contentWidth,blockHeight-2,2,2,"FD");
      pdf.setFont("helvetica","bold");
      pdf.setFontSize(10);
      pdf.setTextColor(23,32,51);
      pdf.text(`${recommendation.area}  |  ${recommendation.priority} priority`,margin+4,y+6);
      pdf.setFont("helvetica","normal");
      pdf.setFontSize(9);
      pdf.text(actionLines,margin+4,y+12);
      pdf.setTextColor(101,113,138);
      pdf.text(benefitLines,margin+4,y+12+actionLines.length*4.5);
      y+=blockHeight+3;
    };

    pdf.setFillColor(245,246,250);
    pdf.roundedRect(margin,y,contentWidth,33,3,3,"F");
    pdf.setTextColor(101,113,138);
    pdf.setFont("helvetica","normal");
    pdf.setFontSize(9);
    pdf.text("PREDICTED SCORE",margin+6,y+9);
    pdf.setTextColor(81,69,205);
    pdf.setFont("helvetica","bold");
    pdf.setFontSize(25);
    pdf.text(`${p.predicted_score}/100`,margin+6,y+23);
    pdf.setTextColor(23,32,51);
    pdf.setFontSize(12);
    pdf.text(p.performance_category,pageWidth-margin-6,y+18,{align:"right"});
    pdf.setFont("helvetica","normal");
    pdf.setFontSize(8);
    pdf.setTextColor(101,113,138);
    pdf.text("Model estimate - not an actual examination result",pageWidth-margin-6,y+25,{align:"right"});
    y+=41;

    addSection("Assessment details");
    addRow("Subject",p.subject);
    addRow("Semester",p.semester);
    addRow("Prediction date",new Date(p.created_at).toLocaleString());
    addRow("Model version",p.model_version);

    addSection("Student inputs");
    Object.entries(p.input_data).forEach(([key,value])=>{
      if(key==="subject"||key==="semester")return;
      const label=key.replaceAll("_"," ").replace(/\b\w/g,char=>char.toUpperCase());
      addRow(label,typeof value==="boolean"?(value?"Yes":"No"):value);
    });

    addSection("Personalized recommendations");
    p.recommendations.forEach(addRecommendation);

    const totalPages=pdf.getNumberOfPages();
    for(let page=1;page<=totalPages;page++){
      pdf.setPage(page);
      pdf.setDrawColor(226,230,239);
      pdf.line(margin,pageHeight-14,pageWidth-margin,pageHeight-14);
      pdf.setFont("helvetica","normal");
      pdf.setFontSize(8);
      pdf.setTextColor(101,113,138);
      pdf.text("EduPredict - Academic decision support",margin,pageHeight-8);
      pdf.text(`Page ${page} of ${totalPages}`,pageWidth-margin,pageHeight-8,{align:"right"});
    }
    const filename=`edupredict-prediction-${p.id}.pdf`;
    const reportBlob=pdf.output("blob");
    const reportFile=new File([reportBlob],filename,{type:"application/pdf"});

    // Prefer the native share/save sheet on mobile browsers that support PDF file sharing.
    // This avoids relying on a synthetic anchor click for a Blob URL, which is unreliable
    // in some mobile and embedded browsers.
    if(navigator.share && navigator.canShare?.({files:[reportFile]})){
      try{
        await navigator.share({
          files:[reportFile],
          title:`EduPredict Prediction Report - ${p.subject}`,
          text:`Academic performance prediction report #${p.id}`,
        });
        return;
      }catch(shareError){
        if(shareError?.name==="AbortError")return;
        console.warn("Native PDF sharing failed; falling back to jsPDF save.",shareError);
      }
    }

    // jsPDF's save helper handles browser-specific download behavior better than
    // a manually-created Blob URL and an immediately-revoked download anchor.
    pdf.save(filename);
  };
  const maxImpact=explanation?Math.max(...explanation.contributions.map(item=>Math.abs(item.contribution)),0.01):1;
  if(!p)return <div className="loading-page"><span className="spinner"/>Loading result...</div>;
  return <><div className="page-heading"><div><span>Result</span><h1>Prediction #{p.id}</h1></div><div className="page-actions"><button className="button ghost" onClick={downloadReport}>Download Report</button><Link className="button ghost" to="/predict">Predict Again</Link><Link className="button primary" to="/predictions">View history</Link></div></div>
    <div className="result-grid"><article className="score-card"><span>Predicted academic score</span><div className="score-ring" style={{"--score":`${p.predicted_score*3.6}deg`}}><b>{p.predicted_score}</b><small>/100</small></div><span className="badge">{p.performance_category}</span><p>Model estimate · {p.model_version}</p></article>
    <article className="panel"><div className="panel-heading"><div><span>Assessment information</span><h3>{p.subject}</h3></div></div><div className="detail-grid">{Object.entries(p.input_data).filter(([k])=>k!=="subject"&&k!=="semester").map(([k,v])=><div key={k}><span>{k.replaceAll("_"," ")}</span><strong>{typeof v==="boolean"?v?"Yes":"No":v}</strong></div>)}</div></article></div>
    {explanation?<article className="panel explanation-panel">
      <div className="panel-heading"><div><span>Explainable AI</span><h3>What influenced this estimate?</h3></div><span className="badge">Ridge model</span></div>
      <p className="muted explanation-note">Feature contributions show how this model's inputs move its estimate relative to the training-data baseline. They are not causal effects.</p>
      <div className="explanation-baseline"><span>Model baseline</span><strong>{explanation.baseline_score.toFixed(1)}</strong><span>Estimated output: {explanation.predicted_score.toFixed(1)} / 100</span></div>
      <div className="contribution-list">{explanation.contributions.map(item=><div className="contribution-row" key={item.feature}>
        <div className="contribution-heading"><span>{item.feature.replaceAll("_"," ")}</span><strong className={item.direction}>{item.contribution>0?"+":""}{item.contribution.toFixed(2)}</strong></div>
        <div className="contribution-track"><div className={`contribution-fill ${item.direction}`} style={{width:`${Math.max(2,Math.abs(item.contribution)/maxImpact*100)}%`}}/></div>
      </div>)}</div>
      <p className="muted explanation-note">Dataset: {explanation.dataset}. {explanation.disclaimer}</p>
    </article>:explanationError?<article className="panel"><h3>Prediction explanation unavailable</h3><p className="muted">{explanationError}</p></article>:null}
    <article className="panel"><div className="panel-heading"><div><span>Next steps</span><h3>Personalized recommendations</h3></div></div><div className="recommendation-list">{p.recommendations.map((r,i)=><div className="recommendation" key={i}><span className={`priority ${r.priority.toLowerCase()}`}>{r.priority}</span><div><b>{r.area}</b><p>{r.action}</p><small>{r.benefit}</small></div></div>)}</div></article>
  </>;
}

function Analytics() {
  const [trends,setTrends]=useState([]),[subjects,setSubjects]=useState([]);
  useEffect(()=>{Promise.all([api.get("/api/analytics/trends"),api.get("/api/analytics/subjects")]).then(([t,s])=>{setTrends(t.data);setSubjects(s.data)}).catch(reportApiError)},[]);
  return <><div className="page-heading"><div><span>Insights</span><h1>Academic analytics</h1></div></div><div className="chart-grid"><article className="panel"><h3>Study hours versus performance</h3><ResponsiveContainer width="100%" height={300}><BarChart data={trends}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="study_hours"/><YAxis/><Tooltip/><Legend/><Bar dataKey="score" fill="#7566F1" name="Predicted score"/></BarChart></ResponsiveContainer></article><article className="panel"><h3>Attendance and performance</h3><ResponsiveContainer width="100%" height={300}><AreaChart data={trends}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="attendance"/><YAxis/><Tooltip/><Area dataKey="score" stroke="#A78BFA" fill="#A78BFA" fillOpacity={.2}/></AreaChart></ResponsiveContainer></article></div><article className="panel"><h3>Subject comparison</h3><ResponsiveContainer width="100%" height={280}><BarChart data={subjects}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="subject"/><YAxis domain={[0,100]}/><Tooltip/><Bar dataKey="score" fill="#7566F1"/></BarChart></ResponsiveContainer></article></>;
}

function Recommendations() {
  const [items,setItems]=useState([]),[loading,setLoading]=useState(true);
  useEffect(()=>{
    api.get("/api/recommendations")
      .then(r=>setItems(r.data))
      .catch(reportApiError)
      .finally(()=>setLoading(false));
  },[]);
  return <><div className="page-heading"><div><span>Personal growth</span><h1>Learning recommendations</h1></div></div>{loading?<div className="loading-page">Loading...</div>:items.length===0?<div className="empty-state"><Target/><h2>No recommendations yet</h2><p>Your first prediction will generate a personalized improvement plan.</p><Link className="button primary" to="/predict">Create prediction</Link></div>:<div className="recommendation-list panel">{items.map((r,i)=><div className="recommendation" key={i}><span className={`priority ${r.priority.toLowerCase()}`}>{r.priority}</span><div><b>{r.area}</b><p>{r.action}</p><small>{r.benefit}</small></div><span className="status">{r.status}</span></div>)}</div>}</>;
}

function AcademicRiskPage() {
  const [data,setData]=useState(null);
  useEffect(()=>api.get("/api/student/risk-assessment").then(r=>setData(r.data)).catch(reportApiError),[]);
  if(!data)return <div className="loading-page">Assessing your saved academic inputs...</div>;
  if(data.status!=="assessed")return <div className="empty-state"><ShieldAlert/><h2>More information needed</h2><p>{data.actions?.[0]}</p><Link className="button primary" to="/predict">Create assessment</Link></div>;
  return <><div className="page-heading"><div><span>Student support insights</span><h1>Academic risk assessment</h1></div><span className={`badge ${data.risk_level==="high"?"danger":data.risk_level==="moderate"?"warning":"success"}`}>{data.risk_level} support priority</span></div>
    <article className="panel"><div className="risk-summary"><div><span>Support points</span><strong>{data.risk_points}</strong><small>Rule-based indicators, not probability</small></div><div><span>Latest model estimate</span><strong>{data.latest_model_estimate?.toFixed(1)}/100</strong><small>{data.subject} · Semester {data.semester}</small></div><div><span>Recent estimate change</span><strong>{data.recent_estimate_change===null?"—":`${data.recent_estimate_change>0?"+":""}${data.recent_estimate_change}`}</strong><small>Compared with previous saved estimate</small></div></div></article>
    <article className="panel"><h3>Areas that may need support</h3>{data.factors.length?<div className="risk-factor-list">{data.factors.map(item=><div className="risk-factor" key={item.factor}><span className={`badge ${item.severity==="high"?"danger":"warning"}`}>{item.severity}</span><div><strong>{item.factor.replaceAll("_"," ")}</strong><p>{item.observation}</p><small>{item.suggested_action}</small></div></div>)}</div>:<p className="muted">No configured support indicators were triggered by the latest saved inputs.</p>}</article>
    <article className="panel"><h3>Suggested next steps</h3><ul className="action-list">{data.actions.map((item,i)=><li key={i}>{item}</li>)}</ul></article>
    <p className="muted">{data.disclaimer}</p>
  </>;
}

function StudyPlannerPage() {
  const [hours,setHours]=useState(2),[subject,setSubject]=useState("");
  const [plan,setPlan]=useState(null),[error,setError]=useState(""),[loading,setLoading]=useState(false);
  const generate=async e=>{e.preventDefault();setLoading(true);setError("");try{const r=await api.post("/api/student/study-plan",{available_hours_per_day:Number(hours),focus_subject:subject||null});setPlan(r.data)}catch(err){setError(getApiErrorMessage(err))}finally{setLoading(false)}};
  return <><div className="page-heading"><div><span>Personalized learning</span><h1>Weekly study planner</h1></div></div><article className="panel"><form className="form-grid" onSubmit={generate}><label>Focus subject<input value={subject} onChange={e=>setSubject(e.target.value)} placeholder="Use latest assessment subject if blank"/></label><label>Available study hours per day<input type="number" min="0.5" max="8" step="0.5" value={hours} onChange={e=>setHours(e.target.value)}/></label><button className="button primary" disabled={loading}>{loading?"Generating...":"Generate 7-day plan"}</button></form>{error&&<div className="alert">{error}</div>}</article>
    {plan&&<><div className="planner-grid">{plan.days.map(day=><article className="panel planner-day" key={day.day}><div className="planner-day-head"><div><span>{day.date}</span><h3>{day.day}</h3></div><span className="badge">{day.estimated_hours} hrs</span></div><strong>{day.subject}</strong><ul>{day.activities.map((task,i)=><li key={i}>{task}</li>)}</ul></article>)}</div><p className="muted">{plan.disclaimer}</p></>}
  </>;
}

function AcademicActivityPage() {
  const today=new Date().toISOString().slice(0,10);
  const [summary,setSummary]=useState(null),[items,setItems]=useState([]),[loading,setLoading]=useState(true),[error,setError]=useState("");
  const [form,setForm]=useState({activity_type:"study_session",subject:"",value:1,occurred_on:today,notes:""});
  const load=()=>Promise.all([api.get("/api/student/activities/summary"),api.get("/api/student/activities")]).then(([a,b])=>{setSummary(a.data);setItems(b.data)}).catch(err=>setError(getApiErrorMessage(err))).finally(()=>setLoading(false));
  useEffect(()=>{load()},[]);
  const submit=async e=>{e.preventDefault();setError("");try{await api.post("/api/student/activities",{...form,value:Number(form.value)});setForm(v=>({...v,value:v.activity_type==="attendance"?1:1,notes:""}));load()}catch(err){setError(getApiErrorMessage(err))}};
  const remove=async item=>{try{await api.delete(`/api/student/activities/${item.id}`);load()}catch(err){setError(getApiErrorMessage(err))}};
  return <><div className="page-heading"><div><span>Personal academic record</span><h1>Study & activity tracker</h1></div></div>
    {summary&&<><StatCards items={[[BookOpen,"Study hours · last 7 days",summary.study_hours_last_7_days],[Users,"Classes recorded",summary.attendance_classes_recorded],[Target,"Recorded attendance",summary.recorded_attendance_percentage===null?"—":`${summary.recorded_attendance_percentage}%`],[ClipboardList,"Average assignment score",summary.average_assignment_score===null?"—":summary.average_assignment_score]]}/><p className="muted">{summary.disclaimer}</p></>}
    <article className="panel"><h3>Record an activity</h3>{error&&<div className="alert">{error}</div>}<form className="form-grid" onSubmit={submit}>
      <label>Activity type<select value={form.activity_type} onChange={e=>setForm({...form,activity_type:e.target.value,value:1})}><option value="study_session">Study session (hours)</option><option value="attendance">Class attendance</option><option value="assignment">Assignment score (%)</option></select></label>
      <label>Subject<input value={form.subject} onChange={e=>setForm({...form,subject:e.target.value})} required minLength={2}/></label>
      <label>{form.activity_type==="study_session"?"Hours studied":form.activity_type==="attendance"?"Attendance status":"Assignment score (%)"}
        {form.activity_type==="attendance"?<select value={form.value} onChange={e=>setForm({...form,value:Number(e.target.value)})}><option value={1}>Present</option><option value={0}>Absent</option></select>:<input type="number" min="0" max={form.activity_type==="study_session"?16:100} step="0.5" value={form.value} onChange={e=>setForm({...form,value:e.target.value})} required/>}
      </label>
      <label>Date<input type="date" value={form.occurred_on} onChange={e=>setForm({...form,occurred_on:e.target.value})} required/></label>
      <label>Notes (optional)<input value={form.notes} onChange={e=>setForm({...form,notes:e.target.value})} maxLength={1000}/></label>
      <button className="button primary">Save activity</button>
    </form></article>
    <article className="panel"><h3>Recent recorded activities</h3>{loading?<p>Loading activity history...</p>:items.length===0?<p className="muted">No activity recorded yet. Add a study session, attendance entry or assignment score above.</p>:<div className="table-wrap"><table><thead><tr><th>Date</th><th>Type</th><th>Subject</th><th>Value</th><th>Notes</th><th/></tr></thead><tbody>{items.map(item=><tr key={item.id}><td>{item.occurred_on}</td><td>{item.activity_type.replace("_"," ")}</td><td>{item.subject}</td><td>{item.activity_type==="attendance"?(item.value===1?"Present":"Absent"):item.activity_type==="study_session"?`${item.value} hrs`:`${item.value}%`}</td><td>{item.notes||"—"}</td><td><button className="text-button danger" onClick={()=>remove(item)}>Delete</button></td></tr>)}</tbody></table></div>}</article>
  </>;
}

function StudyGoalsPage() {
  const [goals,setGoals]=useState([]),[form,setForm]=useState({title:"",subject:"",target_date:"",description:""}),[loading,setLoading]=useState(true),[error,setError]=useState("");
  const load=()=>api.get("/api/student/goals").then(r=>setGoals(r.data)).catch(e=>setError(getApiErrorMessage(e))).finally(()=>setLoading(false));
  useEffect(()=>{load()},[]);
  const create=async e=>{e.preventDefault();setError("");try{await api.post("/api/student/goals",{...form,target_date:form.target_date?new Date(`${form.target_date}T00:00:00`).toISOString():null});setForm({title:"",subject:"",target_date:"",description:""});load()}catch(err){setError(getApiErrorMessage(err))}};
  const update=async(g,status)=>{try{await api.patch(`/api/student/goals/${g.id}`,{status});load()}catch(err){setError(getApiErrorMessage(err))}};
  const remove=async g=>{if(!window.confirm(`Delete the goal "${g.title}"?`))return;try{await api.delete(`/api/student/goals/${g.id}`);load()}catch(err){setError(getApiErrorMessage(err))}};
  return <><div className="page-heading"><div><span>Personal accountability</span><h1>Study goals</h1></div></div><article className="panel"><h3>Create a study goal</h3>{error&&<div className="alert">{error}</div>}<form onSubmit={create} className="form-grid"><label>Goal title<input value={form.title} onChange={e=>setForm({...form,title:e.target.value})} minLength={3} required/></label><label>Subject<input value={form.subject} onChange={e=>setForm({...form,subject:e.target.value})}/></label><label>Target date<input type="date" value={form.target_date} onChange={e=>setForm({...form,target_date:e.target.value})}/></label><label>Description<input value={form.description} onChange={e=>setForm({...form,description:e.target.value})}/></label><button className="button primary">Add goal</button></form></article>
    <article className="panel"><h3>Your goals</h3>{loading?<p>Loading goals...</p>:goals.length===0?<p className="muted">No goals yet. Create your first study goal above.</p>:<div className="goal-list">{goals.map(g=><div className="goal-item" key={g.id}><div><strong>{g.title}</strong><p>{g.subject||"General"} · {g.target_date||"No target date"}</p>{g.description&&<small>{g.description}</small>}</div><span className={`badge ${g.status==="completed"?"success":"warning"}`}>{g.status.replace("_"," ")}</span><div className="page-actions">{g.status!=="completed"&&<button className="button ghost" onClick={()=>update(g,"completed")}>Complete</button>}<button className="text-button danger" onClick={()=>remove(g)}>Delete</button></div></div>)}</div>}</article>
  </>;
}

function AcademicAssistantPage() {
  const [question,setQuestion]=useState("How can I improve my study routine?");
  const [messages,setMessages]=useState([]),[loading,setLoading]=useState(false),[error,setError]=useState("");
  const ask=async e=>{e.preventDefault();if(!question.trim())return;const q=question.trim();setMessages(items=>[...items,{role:"student",text:q}]);setQuestion("");setLoading(true);setError("");try{const r=await api.post("/api/assistant/chat",{question:q});setMessages(items=>[...items,{role:"assistant",text:r.data.answer,provider:r.data.provider}])}catch(err){setError(getApiErrorMessage(err))}finally{setLoading(false)}};
  return <><div className="page-heading"><div><span>Academic guidance</span><h1>EduPredict assistant</h1></div></div><article className="panel assistant-panel"><div className="assistant-intro"><Bot/><div><strong>Academic support assistant</strong><p className="muted">Ask about your saved assessment, attendance, study routine or improvement areas.</p></div></div><div className="assistant-messages" aria-live="polite">{messages.length===0?<div className="empty-state"><MessageSquare/><p>Start by asking a question about your academic progress.</p></div>:messages.map((m,i)=><div className={`assistant-message ${m.role}`} key={i}><span>{m.role==="student"?"You":"EduPredict"}</span><p>{m.text}</p>{m.provider&&<small>{m.provider==="configured_llm"?"AI provider":"Built-in contextual assistant"}</small>}</div>)}{loading&&<p className="muted">Preparing an answer...</p>}</div>{error&&<div className="alert">{error}</div>}<form className="assistant-form" onSubmit={ask}><textarea value={question} onChange={e=>setQuestion(e.target.value)} maxLength={1200} rows={2} placeholder="Ask an academic question..."/><button className="button primary" disabled={loading||!question.trim()}>Send</button></form></article></>;
}

function StudentNotificationsPage() {
  const [items,setItems]=useState([]),[loading,setLoading]=useState(true);
  useEffect(()=>api.get("/api/student/notifications").then(r=>setItems(r.data)).catch(reportApiError).finally(()=>setLoading(false)),[]);
  return <><div className="page-heading"><div><span>Updates</span><h1>Notifications</h1></div></div><article className="panel">{loading?<p>Loading notifications...</p>:items.length===0?<div className="empty-state"><Bell/><h3>You're all caught up</h3><p>New academic support reminders and goal due dates will appear here.</p></div>:<div className="notification-list">{items.map(item=><Link to={item.action} className="notification-item" key={item.id}><span className={`badge ${item.severity==="high"?"danger":item.severity==="moderate"?"warning":"success"}`}>{item.severity}</span><div><strong>{item.title}</strong><p>{item.message}</p></div><ChevronRight/></Link>)}</div>}</article></>;
}

function TeacherPortalPage() {
  const [data,setData]=useState(null),[students,setStudents]=useState([]),[note,setNote]=useState({student_id:"",note:""}),[message,setMessage]=useState("");
  const load=()=>Promise.all([api.get("/api/teacher/dashboard"),api.get("/api/teacher/students")]).then(([d,s])=>{setData(d.data);setStudents(s.data)}).catch(reportApiError);
  useEffect(()=>{load()},[]);
  const saveNote=async e=>{e.preventDefault();setMessage("");try{await api.post("/api/teacher/interventions",{student_id:Number(note.student_id),note:note.note});setNote({student_id:"",note:""});setMessage("Intervention note saved.");}catch(err){setMessage(getApiErrorMessage(err))}};
  if(!data)return <div className="loading-page">Loading teacher workspace...</div>;
  return <><div className="page-heading"><div><span>Teaching workspace · {data.institution}</span><h1>Teacher overview</h1></div></div><StatCards items={[[Users,"Assigned students",data.assigned_students],[ShieldAlert,"Students needing support",students.filter(s=>["high","moderate"].includes(s.support_level)).length]]}/><article className="panel"><h3>Assigned students</h3>{students.length?<div className="table-wrap"><table><thead><tr><th>Student</th><th>Course</th><th>Semester</th><th>Latest model estimate</th><th>Support level</th></tr></thead><tbody>{students.map(st=><tr key={st.id}><td>{st.full_name}</td><td>{st.course||"—"}</td><td>{st.semester||"—"}</td><td>{st.latest_model_estimate??"—"}</td><td>{st.support_level||"Not assessed"}</td></tr>)}</tbody></table></div>:<p className="muted">No students have been assigned to you yet. Ask the system administrator to assign students from the same institution.</p>}</article><article className="panel"><h3>Record an intervention note</h3><form onSubmit={saveNote} className="form-grid"><label>Assigned student<select value={note.student_id} onChange={e=>setNote({...note,student_id:e.target.value})} required><option value="">Select student</option>{students.map(st=><option key={st.id} value={st.id}>{st.full_name} · #{st.id}</option>)}</select></label><label>Private support note<textarea rows={3} value={note.note} onChange={e=>setNote({...note,note:e.target.value})} minLength={3} required/></label><button className="button primary" disabled={!students.length}>Save note</button></form>{message&&<p className="muted">{message}</p>}</article></>;
}

function InstitutionPortalPage() {
  const [data,setData]=useState(null);
  useEffect(()=>api.get("/api/institution/analytics").then(r=>setData(r.data)).catch(reportApiError),[]);
  if(!data)return <div className="loading-page">Loading institution analytics...</div>;
  return <><div className="page-heading"><div><span>Institution workspace</span><h1>{data.institution}</h1></div></div><StatCards items={[[Users,"Students",data.student_count],[History,"Saved assessments",data.prediction_count],[BarChart3,"Average model estimate",data.average_model_estimate===null?"—":`${data.average_model_estimate}%`]]}/><article className="panel"><p>{data.notice}</p></article></>;
}

function AdminTeachingPage() {
  const [teacher,setTeacher]=useState({full_name:"",email:"",password:"",institution_name:"",department:""});
  const [assignment,setAssignment]=useState({teacher_id:"",student_id:""});
  const [institutionAdmin,setInstitutionAdmin]=useState({full_name:"",email:"",password:"",institution_name:"",department:""});
  const [message,setMessage]=useState("");
  const [staff,setStaff]=useState([]);
  const loadStaff=()=>api.get("/api/admin/teaching-staff").then(r=>setStaff(r.data)).catch(reportApiError);
  useEffect(()=>{loadStaff()},[]);
  const submitTeacher=async e=>{e.preventDefault();setMessage("");try{const r=await api.post("/api/admin/teachers",teacher);setMessage(`Teacher account created. ID: ${r.data.id}`);setTeacher({full_name:"",email:"",password:"",institution_name:"",department:""});loadStaff()}catch(err){setMessage(getApiErrorMessage(err))}};
  const submitInstitution=async e=>{e.preventDefault();setMessage("");try{const r=await api.post("/api/admin/institution-admins",institutionAdmin);setMessage(`Institution administrator created. ID: ${r.data.id}`);setInstitutionAdmin({full_name:"",email:"",password:"",institution_name:"",department:""});loadStaff()}catch(err){setMessage(getApiErrorMessage(err))}};
  const submitAssignment=async e=>{e.preventDefault();setMessage("");try{const r=await api.post(`/api/admin/teachers/${assignment.teacher_id}/assignments`,{student_id:Number(assignment.student_id)});setMessage(r.data.already_assigned?"Student was already assigned.":"Student assigned successfully.")}catch(err){setMessage(getApiErrorMessage(err))}};
  const fields=(value,setter)=><div className="form-grid"><label>Full name<input value={value.full_name} onChange={e=>setter({...value,full_name:e.target.value})} required/></label><label>Email<input type="email" value={value.email} onChange={e=>setter({...value,email:e.target.value})} required/></label><label>Temporary password (12+ characters)<input type="password" minLength={12} value={value.password} onChange={e=>setter({...value,password:e.target.value})} required/></label><label>Institution<input value={value.institution_name} onChange={e=>setter({...value,institution_name:e.target.value})} required/></label><label>Department<input value={value.department} onChange={e=>setter({...value,department:e.target.value})}/></label></div>;
  return <><div className="page-heading"><div><span>Staff and access</span><h1>Teaching & institution accounts</h1></div></div>{message&&<div className="alert">{message}</div>}<div className="chart-grid"><article className="panel"><h3>Create teacher account</h3><form onSubmit={submitTeacher}>{fields(teacher,setTeacher)}<button className="button primary">Create teacher</button></form></article><article className="panel"><h3>Create institution administrator</h3><form onSubmit={submitInstitution}>{fields(institutionAdmin,setInstitutionAdmin)}<button className="button primary">Create institution admin</button></form></article></div><article className="panel"><h3>Existing teaching staff</h3>{staff.length?<div className="table-wrap"><table><thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Role</th><th>Institution</th><th>Status</th></tr></thead><tbody>{staff.map(person=><tr key={person.id}><td>#{person.id}</td><td>{person.full_name}</td><td>{person.email}</td><td>{person.role.replace("_"," ")}</td><td>{person.institution_name||"—"}</td><td>{person.active?"Active":"Inactive"}</td></tr>)}</tbody></table></div>:<p className="muted">No teaching staff accounts created yet.</p>}</article><article className="panel"><h3>Assign a student to a teacher</h3><p className="muted">Use the numeric account IDs. The backend verifies that both accounts belong to the same institution.</p><form onSubmit={submitAssignment} className="form-grid"><label>Teacher account ID<input type="number" min="1" value={assignment.teacher_id} onChange={e=>setAssignment({...assignment,teacher_id:e.target.value})} required/></label><label>Student account ID<input type="number" min="1" value={assignment.student_id} onChange={e=>setAssignment({...assignment,student_id:e.target.value})} required/></label><button className="button primary">Assign student</button></form></article></>;
}

function Profile() {
  const [profile,setProfile]=useState(null),[saved,setSaved]=useState(false);
  useEffect(()=>api.get("/api/student/profile").then(r=>setProfile(r.data)).catch(reportApiError) ,[]);
  const submit=async e=>{e.preventDefault();try{await api.put("/api/student/profile",profile);setSaved(true);setTimeout(()=>setSaved(false),2000)}catch(err){reportApiError(err)}};
  if(!profile)return <div className="loading-page">Loading profile...</div>;
  const set=e=>setProfile({...profile,[e.target.name]:e.target.value});
  return <><div className="page-heading"><div><span>Account</span><h1>My profile</h1></div></div><article className="panel profile-panel">{saved&&<div className="toast">Profile updated</div>}<form onSubmit={submit}><div className="form-grid"><label>Full Name<input name="full_name" value={profile.full_name||""} onChange={set}/></label><label>Email Address<input value={profile.email||""} disabled/></label><label>Student ID<input name="student_id" value={profile.student_id||""} onChange={set}/></label><label>Institution<input name="institution_name" value={profile.institution_name||""} onChange={set}/></label><label>Department<input name="department" value={profile.department||""} onChange={set}/></label><label>Course<input name="course" value={profile.course||""} onChange={set}/></label><label>Semester<input name="semester" value={profile.semester||""} onChange={set}/></label><label>Academic Year<input name="academic_year" value={profile.academic_year||""} onChange={set}/></label></div><button className="button primary">Save changes</button></form></article></>;
}

function AdminOverview() {
  const [data,setData]=useState(null);
  useEffect(()=>api.get("/api/admin/dashboard").then(r=>setData(r.data)).catch(reportApiError),[]);
  if(!data)return <div className="loading-page">Loading administration...</div>;
  return <><div className="page-heading"><div><span>Control center</span><h1>Administrator overview</h1></div></div><StatCards items={[[Users,"Registered students",data.total_students],[History,"Total predictions",data.total_predictions],[ShieldCheck,"Active users",data.active_users],[Target,"Average predicted score",`${data.average_score}%`]]}/>
    <div className="chart-grid"><article className="panel"><h3>Performance category distribution</h3><ResponsiveContainer width="100%" height={300}><PieChart><Pie data={data.category_distribution} dataKey="value" nameKey="name" innerRadius={65} outerRadius={110} paddingAngle={4} fill="#7566F1"/><Tooltip/><Legend/></PieChart></ResponsiveContainer></article><article className="panel admin-note"><ShieldCheck/><h3>Role-based protection</h3><p>Administrator API endpoints require a valid administrator token and server-side role authorization.</p></article></div>
    <div className="chart-grid"><article className="panel"><h3>Recent student registrations</h3>{data.recent_student_registrations?.length?<div className="table-wrap"><table><tbody>{data.recent_student_registrations.map(u=><tr key={u.id}><td><strong>{u.full_name}</strong></td><td>{u.email}</td><td>{new Date(u.created_at).toLocaleDateString()}</td></tr>)}</tbody></table></div>:<p className="muted">No registrations yet.</p>}</article><article className="panel"><h3>Recent prediction activity</h3>{data.recent_prediction_activities?.length?<div className="table-wrap"><table><tbody>{data.recent_prediction_activities.map(p=><tr key={p.id}><td>{p.student_name}</td><td>{p.subject}</td><td><strong>{p.predicted_score}%</strong></td></tr>)}</tbody></table></div>:<p className="muted">No predictions yet.</p>}</article></div></>;
}

function AdminUsers() {
  const [users,setUsers]=useState([]),[search,setSearch]=useState("");
  useEffect(()=>api.get("/api/admin/users",{params:{search:search||undefined}}).then(r=>setUsers(r.data)).catch(reportApiError),[search]);
  const toggle=async u=>{try{const r=await api.patch(`/api/admin/users/${u.id}/active`,null,{params:{active:!u.active}});setUsers(users.map(x=>x.id===u.id?{...x,active:r.data.active}:x))}catch(err){reportApiError(err)}};
  const remove=async u=>{if(!window.confirm(`Permanently delete ${u.full_name}?`))return;try{await api.delete(`/api/admin/users/${u.id}`);setUsers(users.filter(x=>x.id!==u.id))}catch(err){reportApiError(err)}};
  return <><div className="page-heading"><div><span>Management</span><h1>Students</h1></div></div><div className="filters"><input placeholder="Search name or email" value={search} onChange={e=>setSearch(e.target.value)}/></div><article className="panel"><div className="table-wrap"><table><thead><tr><th>ID</th><th>Student</th><th>Email</th><th>Institution</th><th>Status</th><th>Action</th></tr></thead><tbody>{users.map(u=><tr key={u.id}><td>#{u.id}</td><td><strong>{u.full_name}</strong></td><td>{u.email}</td><td>{u.institution_name||"—"}</td><td><span className={`badge ${u.active?"success":"danger"}`}>{u.active?"Active":"Inactive"}</span></td><td><button className="text-button" onClick={()=>toggle(u)}>{u.active?"Deactivate":"Activate"}</button><button className="text-button danger" onClick={()=>remove(u)}>Delete</button></td></tr>)}</tbody></table></div></article></>;
}

function AdminPredictions() {
  const [items,setItems]=useState([]);
  useEffect(()=>api.get("/api/admin/predictions").then(r=>setItems(r.data)).catch(reportApiError),[]);
  const exportCsv=()=>{
    const rows=[["ID","Student","Subject","Score","Category","Date"],...items.map(p=>[p.id,p.student_name,p.subject,p.predicted_score,p.performance_category,p.created_at])];
    const csv=rows.map(row=>row.map(value=>`"${String(value).replaceAll('"','""')}"`).join(",")).join("\n");
    const url=URL.createObjectURL(new Blob([csv],{type:"text/csv;charset=utf-8"}));
    const link=document.createElement("a");link.href=url;link.download="edupredict-predictions.csv";link.click();URL.revokeObjectURL(url);
  };
  return <><div className="page-heading"><div><span>Records</span><h1>Prediction management</h1></div><button className="button ghost" onClick={exportCsv}>Export CSV</button></div><article className="panel"><div className="table-wrap"><table><thead><tr><th>ID</th><th>Student</th><th>Subject</th><th>Score</th><th>Category</th><th>Date</th></tr></thead><tbody>{items.map(p=><tr key={p.id}><td>#{p.id}</td><td>{p.student_name}</td><td>{p.subject}</td><td><strong>{p.predicted_score}%</strong></td><td><span className="badge">{p.performance_category}</span></td><td>{new Date(p.created_at).toLocaleDateString()}</td></tr>)}</tbody></table></div></article></>;
}

function AdminModels() {
  const [model,setModel]=useState(null);
  useEffect(()=>api.get("/api/admin/models").then(r=>setModel(r.data)).catch(reportApiError),[]);
  if(!model)return <div className="loading-page">Loading model information...</div>;
  return <><div className="page-heading"><div><span>Machine learning</span><h1>Model management</h1></div></div><StatCards items={[[BrainCircuit,"Model version",model.version],[BookOpen,"Training rows",model.training_rows],[Activity,"Test rows",model.test_rows],[Target,"R-squared",model.metrics.r2.toFixed(3)]]}/><div className="chart-grid"><article className="panel"><h3>Evaluation metrics</h3><div className="metric-grid"><div><span>MAE</span><strong>{model.metrics.mae.toFixed(2)}</strong></div><div><span>RMSE</span><strong>{model.metrics.rmse.toFixed(2)}</strong></div><div><span>MSE</span><strong>{model.metrics.mse.toFixed(2)}</strong></div><div><span>R²</span><strong>{model.metrics.r2.toFixed(3)}</strong></div></div></article><article className="panel"><h3>Dataset and model provenance</h3><p><strong>{model.model_type||"Regression model"}</strong> · {model.version}</p><p>{model.dataset}</p><p className="muted">{model.evaluation_note||"Review the model methodology before interpreting evaluation metrics."}</p><p className="muted">Candidate dataset: {model.candidate_training_configured?"Configured on backend":"Not configured"} · Live model is not replaced by candidate training.</p><code>{model.candidate_training_command}</code><span className={`badge ${model.is_synthetic_demo?"danger":"success"}`}>{model.is_synthetic_demo?"Synthetic demonstration data":"Configured dataset"}</span></article></div></>;
}

function AdminAnalytics() {
  const [data,setData]=useState(null);
  useEffect(()=>api.get("/api/admin/analytics").then(r=>setData(r.data)).catch(reportApiError),[]);
  if(!data)return <div className="loading-page">Loading analytics...</div>;
  return <><div className="page-heading"><div><span>Institutional insights</span><h1>Analytics</h1></div></div><article className="panel"><h3>Subject-wise performance</h3><ResponsiveContainer width="100%" height={320}><BarChart data={data.subject_performance}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="subject"/><YAxis domain={[0,100]}/><Tooltip/><Bar dataKey="score" fill="#7566F1"/></BarChart></ResponsiveContainer></article></>;
}

function AdminAudit() {
  const [logs,setLogs]=useState([]);
  useEffect(()=>api.get("/api/admin/audit-logs").then(r=>setLogs(r.data)).catch(reportApiError),[]);
  return <><div className="page-heading"><div><span>Security</span><h1>Audit log</h1></div></div><article className="panel"><div className="table-wrap"><table><thead><tr><th>Time</th><th>Actor</th><th>Action</th><th>Details</th></tr></thead><tbody>{logs.map(log=><tr key={log.id}><td>{new Date(log.created_at).toLocaleString()}</td><td>{log.actor_id||"—"}</td><td><strong>{log.action}</strong></td><td>{log.details||"—"}</td></tr>)}</tbody></table></div></article></>;
}

function AdminSettings() {
  const [settings,setSettings]=useState(null);
  const [password,setPassword]=useState({current_password:"",new_password:""});
  const [status,setStatus]=useState("");
  useEffect(()=>api.get("/api/admin/settings").then(r=>setSettings(r.data)).catch(reportApiError),[]);
  const changePassword=async e=>{
    e.preventDefault();setStatus("");
    try{await api.post("/api/admin/change-password",password);setStatus("Administrator password updated.");setPassword({current_password:"",new_password:""})}
    catch(err){setStatus(getApiErrorMessage(err));}
  };
  if(!settings)return <div className="loading-page">Loading settings...</div>;
  return <><div className="page-heading"><div><span>Administration</span><h1>Settings</h1></div></div><div className="chart-grid"><article className="panel"><h3>Application configuration</h3><div className="detail-grid"><div><span>Application</span><strong>{settings.application_name}</strong></div><div><span>Database</span><strong>{settings.database_configured?"Configured":"Local default"}</strong></div><div><span>Email provider</span><strong>{settings.email_reset_provider_configured?"Configured":"Not configured"}</strong></div><div><span>Admin username</span><strong>{settings.default_admin_username}</strong></div></div></article><article className="panel"><h3>Change administrator password</h3><form onSubmit={changePassword}><label>Current password<input type="password" value={password.current_password} onChange={e=>setPassword({...password,current_password:e.target.value})} required/></label><label>New password<input type="password" value={password.new_password} onChange={e=>setPassword({...password,new_password:e.target.value})} minLength={12} required/></label>{status&&<div className="alert">{status}</div>}<button className="button primary">Update password</button></form></article></div></>;
}

function Protected({auth,admin=false,children}) {
  if(!auth.user)return <Navigate to="/login" replace/>;
  if(admin&&auth.user.role!=="admin")return <Navigate to="/dashboard" replace/>;
  return <AppShell auth={auth} admin={admin}>{children}</AppShell>;
}

export default function App() {
  const auth=useAuth();
  return <>
    <ApiNotifications/>
    <Routes>
    <Route path="/" element={<Landing/>}/>
    <Route path="/login" element={auth.user?(<Navigate to={auth.user.role==="admin"?"/admin":auth.user.role==="teacher"?"/teacher":auth.user.role==="institution_admin"?"/institution":"/dashboard"} replace/>):<AuthPage mode="login" auth={auth}/>}/>
    <Route path="/register" element={auth.user?<Navigate to="/dashboard" replace/>:<AuthPage mode="register" auth={auth}/>}/>
    <Route path="/admin/login" element={auth.user?(<Navigate to={auth.user.role==="admin"?"/admin":"/dashboard"} replace/>):<AuthPage mode="admin" auth={auth}/>}/>
    <Route path="/dashboard" element={<Protected auth={auth}><Dashboard/></Protected>}/>
    <Route path="/predict" element={<Protected auth={auth}><PredictionForm/></Protected>}/>
    <Route path="/simulate" element={<Protected auth={auth}><WhatIfSimulator/></Protected>}/>
    <Route path="/risk" element={<Protected auth={auth} roles={["student"]}><AcademicRiskPage/></Protected>}/>
    <Route path="/study-plan" element={<Protected auth={auth} roles={["student"]}><StudyPlannerPage/></Protected>}/>
    <Route path="/activities" element={<Protected auth={auth} roles={["student"]}><AcademicActivityPage/></Protected>}/>
    <Route path="/goals" element={<Protected auth={auth} roles={["student"]}><StudyGoalsPage/></Protected>}/>
    <Route path="/assistant" element={<Protected auth={auth} roles={["student"]}><AcademicAssistantPage/></Protected>}/>
    <Route path="/notifications" element={<Protected auth={auth} roles={["student"]}><StudentNotificationsPage/></Protected>}/>
    <Route path="/teacher" element={<Protected auth={auth} roles={["teacher"]}><TeacherPortalPage/></Protected>}/>
    <Route path="/teacher/students" element={<Protected auth={auth} roles={["teacher"]}><TeacherPortalPage/></Protected>}/>
    <Route path="/institution" element={<Protected auth={auth} roles={["institution_admin"]}><InstitutionPortalPage/></Protected>}/>
    <Route path="/admin/teaching" element={<Protected auth={auth} admin><AdminTeachingPage/></Protected>}/>
    <Route path="/predictions" element={<Protected auth={auth}><PredictionHistory/></Protected>}/>
    <Route path="/predictions/:id" element={<Protected auth={auth}><PredictionDetail/></Protected>}/>
    <Route path="/analytics" element={<Protected auth={auth}><Analytics/></Protected>}/>
    <Route path="/recommendations" element={<Protected auth={auth}><Recommendations/></Protected>}/>
    <Route path="/profile" element={<Protected auth={auth}><Profile/></Protected>}/>
    <Route path="/admin" element={<Protected auth={auth} admin><AdminOverview/></Protected>}/>
    <Route path="/admin/users" element={<Protected auth={auth} admin><AdminUsers/></Protected>}/>
    <Route path="/admin/predictions" element={<Protected auth={auth} admin><AdminPredictions/></Protected>}/>
    <Route path="/admin/models" element={<Protected auth={auth} admin><AdminModels/></Protected>}/>
    <Route path="/admin/analytics" element={<Protected auth={auth} admin><AdminAnalytics/></Protected>}/>
    <Route path="/admin/audit" element={<Protected auth={auth} admin><AdminAudit/></Protected>}/>
    <Route path="/admin/settings" element={<Protected auth={auth} admin><AdminSettings/></Protected>}/>
    <Route path="*" element={<Navigate to="/" replace/>}/>
    </Routes>
  </>;
}
