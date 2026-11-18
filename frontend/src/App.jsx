import React, { useEffect, useState } from "react";
import { Link, Navigate, Route, Routes, useNavigate, useParams } from "react-router-dom";
import {
  Activity, BarChart3, BookOpen, ChevronRight, GraduationCap, History,
  LayoutDashboard, LogOut, Menu, Moon, ShieldCheck, Sun, Target,
  TrendingUp, UserRound, Users, X, BrainCircuit, Settings, ClipboardList,
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
        auth.login(res.data.access_token,res.data.user,form.remember); navigate(res.data.user.role==="admin"?"/admin":"/dashboard");
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
  const items = admin ? [
    ["/admin",LayoutDashboard,"Overview"],["/admin/users",Users,"Students"],["/admin/predictions",History,"Predictions"],["/admin/models",BrainCircuit,"ML Models"],["/admin/analytics",BarChart3,"Analytics"],["/admin/audit",ClipboardList,"Audit Log"],["/admin/settings",Settings,"Settings"]
  ] : [
    ["/dashboard",LayoutDashboard,"Overview"],["/predict",Target,"Predict Performance"],["/predictions",History,"My Predictions"],["/analytics",BarChart3,"Academic Analytics"],["/recommendations",Activity,"Recommendations"],["/profile",UserRound,"My Profile"]
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
  useEffect(()=>{api.get(`/api/predictions/${id}`).then(r=>setP(r.data)).catch(reportApiError)},[id]);
  const downloadReport=()=>{
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
    const reportBlob=pdf.output("blob");
    const reportUrl=URL.createObjectURL(reportBlob);
    const downloadLink=document.createElement("a");
    downloadLink.href=reportUrl;
    downloadLink.download=`edupredict-prediction-${p.id}.pdf`;
    document.body.appendChild(downloadLink);
    downloadLink.click();
    downloadLink.remove();
    window.setTimeout(()=>URL.revokeObjectURL(reportUrl),1000);
  };
  if(!p)return <div className="loading-page"><span className="spinner"/>Loading result...</div>;
  return <><div className="page-heading"><div><span>Result</span><h1>Prediction #{p.id}</h1></div><div className="page-actions"><button className="button ghost" onClick={downloadReport}>Download Report</button><Link className="button ghost" to="/predict">Predict Again</Link><Link className="button primary" to="/predictions">View history</Link></div></div>
    <div className="result-grid"><article className="score-card"><span>Predicted academic score</span><div className="score-ring" style={{"--score":`${p.predicted_score*3.6}deg`}}><b>{p.predicted_score}</b><small>/100</small></div><span className="badge">{p.performance_category}</span><p>Model estimate · {p.model_version}</p></article>
    <article className="panel"><div className="panel-heading"><div><span>Assessment information</span><h3>{p.subject}</h3></div></div><div className="detail-grid">{Object.entries(p.input_data).filter(([k])=>k!=="subject"&&k!=="semester").map(([k,v])=><div key={k}><span>{k.replaceAll("_"," ")}</span><strong>{typeof v==="boolean"?v?"Yes":"No":v}</strong></div>)}</div></article></div>
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
  return <><div className="page-heading"><div><span>Management</span><h1>Students</h1></div></div><div className="filters"><input placeholder="Search name or email" value={search} onChange={e=>setSearch(e.target.value)}/></div><article className="panel"><div className="table-wrap"><table><thead><tr><th>Student</th><th>Email</th><th>Institution</th><th>Status</th><th>Action</th></tr></thead><tbody>{users.map(u=><tr key={u.id}><td><strong>{u.full_name}</strong></td><td>{u.email}</td><td>{u.institution_name||"—"}</td><td><span className={`badge ${u.active?"success":"danger"}`}>{u.active?"Active":"Inactive"}</span></td><td><button className="text-button" onClick={()=>toggle(u)}>{u.active?"Deactivate":"Activate"}</button><button className="text-button danger" onClick={()=>remove(u)}>Delete</button></td></tr>)}</tbody></table></div></article></>;
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
  return <><div className="page-heading"><div><span>Machine learning</span><h1>Model management</h1></div></div><StatCards items={[[BrainCircuit,"Model version",model.version],[BookOpen,"Training rows",model.training_rows],[Activity,"Test rows",model.test_rows],[Target,"R-squared",model.metrics.r2.toFixed(3)]]}/><div className="chart-grid"><article className="panel"><h3>Evaluation metrics</h3><div className="metric-grid"><div><span>MAE</span><strong>{model.metrics.mae.toFixed(2)}</strong></div><div><span>RMSE</span><strong>{model.metrics.rmse.toFixed(2)}</strong></div><div><span>MSE</span><strong>{model.metrics.mse.toFixed(2)}</strong></div><div><span>R²</span><strong>{model.metrics.r2.toFixed(3)}</strong></div></div></article><article className="panel"><h3>Dataset information</h3><p>{model.dataset}</p><p className="muted">A synthetic demonstration dataset is used because no repository dataset was available.</p></article></div></>;
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
    <Route path="/login" element={auth.user?(<Navigate to={auth.user.role==="admin"?"/admin":"/dashboard"} replace/>):<AuthPage mode="login" auth={auth}/>}/>
    <Route path="/register" element={auth.user?<Navigate to="/dashboard" replace/>:<AuthPage mode="register" auth={auth}/>}/>
    <Route path="/admin/login" element={auth.user?(<Navigate to={auth.user.role==="admin"?"/admin":"/dashboard"} replace/>):<AuthPage mode="admin" auth={auth}/>}/>
    <Route path="/dashboard" element={<Protected auth={auth}><Dashboard/></Protected>}/>
    <Route path="/predict" element={<Protected auth={auth}><PredictionForm/></Protected>}/>
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
