import React, { useEffect, useMemo, useState } from "react";
import { Activity, Award, BookOpen, BriefcaseBusiness, CalendarDays, CheckCircle2, Compass, GraduationCap, Lightbulb, RefreshCw, ShieldAlert, Sparkles, Target } from "lucide-react";
import api, { getApiErrorMessage } from "./api";
import "./growth.css";

const todayLocal = () => {
  const now = new Date();
  return [now.getFullYear(), String(now.getMonth() + 1).padStart(2, "0"), String(now.getDate()).padStart(2, "0")].join("-");
};

function Section({ icon: Icon, eyebrow, title, children }) {
  return <section className="panel growth-section"><div className="growth-section-heading"><div className="growth-icon"><Icon size={19}/></div><div><span>{eyebrow}</span><h2>{title}</h2></div></div>{children}</section>;
}

function ResultMessage({ error, notice }) {
  if (error) return <div className="alert" role="alert">{error}</div>;
  if (notice) return <div className="growth-notice" role="status">{notice}</div>;
  return null;
}

export default function AcademicGrowthHub() {
  const [twin, setTwin] = useState(null);
  const [recovery, setRecovery] = useState(null);
  const [loadingTwin, setLoadingTwin] = useState(true);
  const [twinError, setTwinError] = useState("");
  const [recoveryError, setRecoveryError] = useState("");

  const [exam, setExam] = useState({ subject: "", exam_date: "", hours_per_day: 2, topics: "" });
  const [examResult, setExamResult] = useState(null);
  const [examError, setExamError] = useState("");
  const [examLoading, setExamLoading] = useState(false);

  const [question, setQuestion] = useState({ subject: "", topic: "", difficulty: "medium", count: 5 });
  const [questionResult, setQuestionResult] = useState(null);
  const [questionError, setQuestionError] = useState("");
  const [questionLoading, setQuestionLoading] = useState(false);

  const [career, setCareer] = useState({ target_role: "AI/ML Engineer", skills: "", projects_count: 1, internship_experience: false, portfolio_ready: false });
  const [careerResult, setCareerResult] = useState(null);
  const [careerError, setCareerError] = useState("");
  const [careerLoading, setCareerLoading] = useState(false);

  const [scholarship, setScholarship] = useState({ academic_percentage: 75, course_area: "", annual_income_band: "undisclosed", state: "" });
  const [scholarshipResult, setScholarshipResult] = useState(null);
  const [scholarshipError, setScholarshipError] = useState("");
  const [scholarshipLoading, setScholarshipLoading] = useState(false);

  const loadSnapshot = async () => {
    setLoadingTwin(true);
    setTwinError("");
    try {
      const [snapshot, plan] = await Promise.all([
        api.get("/api/student/digital-twin"),
        api.get("/api/student/recovery-plan"),
      ]);
      setTwin(snapshot.data);
      setRecovery(plan.data);
      setRecoveryError("");
    } catch (error) {
      setTwinError(getApiErrorMessage(error));
    } finally {
      setLoadingTwin(false);
    }
  };

  useEffect(() => { loadSnapshot(); }, []);

  const submitExam = async (event) => {
    event.preventDefault(); setExamLoading(true); setExamError(""); setExamResult(null);
    try {
      const response = await api.post("/api/student/exam-preparation", {
        ...exam,
        hours_per_day: Number(exam.hours_per_day),
        topics: exam.topics.split(",").map((item) => item.trim()).filter(Boolean),
      });
      setExamResult(response.data);
    } catch (error) { setExamError(getApiErrorMessage(error)); }
    finally { setExamLoading(false); }
  };

  const submitQuestions = async (event) => {
    event.preventDefault(); setQuestionLoading(true); setQuestionError(""); setQuestionResult(null);
    try {
      const response = await api.post("/api/student/question-generator", { ...question, count: Number(question.count) });
      setQuestionResult(response.data);
    } catch (error) { setQuestionError(getApiErrorMessage(error)); }
    finally { setQuestionLoading(false); }
  };

  const submitCareer = async (event) => {
    event.preventDefault(); setCareerLoading(true); setCareerError(""); setCareerResult(null);
    try {
      const response = await api.post("/api/student/career-readiness", {
        ...career,
        skills: career.skills.split(",").map((item) => item.trim()).filter(Boolean),
        projects_count: Number(career.projects_count),
      });
      setCareerResult(response.data);
    } catch (error) { setCareerError(getApiErrorMessage(error)); }
    finally { setCareerLoading(false); }
  };

  const submitScholarship = async (event) => {
    event.preventDefault(); setScholarshipLoading(true); setScholarshipError(""); setScholarshipResult(null);
    try {
      const response = await api.post("/api/student/scholarship-matches", {
        ...scholarship, academic_percentage: Number(scholarship.academic_percentage),
      });
      setScholarshipResult(response.data);
    } catch (error) { setScholarshipError(getApiErrorMessage(error)); }
    finally { setScholarshipLoading(false); }
  };

  const timeline = useMemo(() => twin?.timeline || [], [twin]);

  return <>
    <div className="page-heading growth-page-heading">
      <div><span>Personal intelligence workspace</span><h1>AI Growth Lab</h1><p className="muted">A practical workspace for understanding progress, recovering from setbacks and planning your next academic and career steps.</p></div>
      <button className="button ghost" onClick={loadSnapshot} disabled={loadingTwin}><RefreshCw size={16}/> Refresh twin</button>
    </div>

    <Section icon={Activity} eyebrow="Your academic digital twin" title="Student Digital Twin">
      {loadingTwin ? <p className="muted">Loading your saved academic snapshot…</p> : twinError ? <ResultMessage error={twinError}/> : <>
        <div className="growth-metric-grid">
          <div><span>Latest model estimate</span><strong>{twin.latest_assessment ? `${twin.latest_assessment.model_estimate.toFixed(1)} / 100` : "Not available"}</strong><small>{twin.latest_assessment?.subject || "Create your first assessment"}</small></div>
          <div><span>Recent estimate change</span><strong>{twin.recent_estimate_change === null ? "—" : `${twin.recent_estimate_change > 0 ? "+" : ""}${twin.recent_estimate_change}`}</strong><small>Compared with previous saved estimate</small></div>
          <div><span>Study hours recorded</span><strong>{twin.activity_last_30_days.study_hours}</strong><small>Last 30 days · manually logged</small></div>
          <div><span>Goal completion</span><strong>{twin.goal_progress.completion_percentage === null ? "—" : `${twin.goal_progress.completion_percentage}%`}</strong><small>{twin.goal_progress.completed} of {twin.goal_progress.total} goals completed</small></div>
        </div>
        {twin.status === "insufficient_data" && <div className="growth-notice">Your twin will become more informative after you save a prediction and record study activities.</div>}
        {twin.latest_assessment && <div className="growth-detail"><strong>Current profile</strong><p>{twin.student.course || "Course not set"} · {twin.student.department || "Department not set"} · Semester {twin.student.semester || "not set"}</p><p className="muted">Model {twin.latest_assessment.model_version} · {twin.latest_assessment.performance_category}</p></div>}
        {timeline.length > 0 && <div className="table-wrap"><table><thead><tr><th>Date</th><th>Subject</th><th>Model estimate</th><th>Version</th></tr></thead><tbody>{timeline.map(item => <tr key={item.prediction_id}><td>{item.date}</td><td>{item.subject}</td><td>{item.model_estimate.toFixed(1)}</td><td>{item.model_version}</td></tr>)}</tbody></table></div>}
        <ul className="growth-disclaimers">{twin.limitations.map(item => <li key={item}>{item}</li>)}</ul>
      </>}
    </Section>

    <Section icon={ShieldAlert} eyebrow="Actionable improvement" title="Performance Recovery Mode">
      {recoveryError && <ResultMessage error={recoveryError}/>}
      {recovery?.status === "insufficient_data" ? <p className="muted">{recovery.message}</p> : recovery?.weeks && <><p className="muted">A four-week action checklist based on your latest saved assessment. Review and adapt it with your teacher where helpful.</p><div className="growth-week-grid">{recovery.weeks.map(week => <article className="growth-week" key={week.week}><span>WEEK {week.week}</span><h3>{week.focus}</h3>{week.tasks.map(task => <div className="growth-task" key={task.area}><strong>{task.title}</strong><p>{task.action}</p></div>)}</article>)}</div><small className="muted">{recovery.disclaimer}</small></>}
    </Section>

    <Section icon={CalendarDays} eyebrow="Exam countdown" title="Smart Exam Preparation">
      <form className="growth-form" onSubmit={submitExam}>
        <label>Subject<input value={exam.subject} onChange={e=>setExam({...exam,subject:e.target.value})} required minLength={2} maxLength={100} placeholder="e.g. Database Management Systems"/></label>
        <label>Exam date<input type="date" min={todayLocal()} value={exam.exam_date} onChange={e=>setExam({...exam,exam_date:e.target.value})} required/></label>
        <label>Study hours per day<input type="number" min="0.5" max="12" step="0.5" value={exam.hours_per_day} onChange={e=>setExam({...exam,hours_per_day:e.target.value})}/></label>
        <label className="growth-wide">Topics (comma-separated)<textarea rows={3} value={exam.topics} onChange={e=>setExam({...exam,topics:e.target.value})} required placeholder="Normalization, SQL joins, transactions…"/></label>
        <button className="button primary" disabled={examLoading}>{examLoading?"Building plan…":"Generate exam plan"}</button>
      </form>
      <ResultMessage error={examError}/>
      {examResult && <div className="growth-result"><h3>{examResult.subject} · {examResult.days_until_exam} days</h3><div className="growth-schedule">{examResult.schedule.map(day=><article key={day.date}><span>{day.date} · Day {day.day}</span><strong>{day.topic}</strong><p>{day.mode}</p><small>{day.task} · {day.planned_hours} hours</small></article>)}</div><p className="muted">{examResult.disclaimer}</p></div>}
    </Section>

    <Section icon={BookOpen} eyebrow="Active recall" title="AI Question Generator">
      <form className="growth-form" onSubmit={submitQuestions}>
        <label>Subject<input value={question.subject} onChange={e=>setQuestion({...question,subject:e.target.value})} required minLength={2}/></label>
        <label>Topic<input value={question.topic} onChange={e=>setQuestion({...question,topic:e.target.value})} required minLength={2}/></label>
        <label>Difficulty<select value={question.difficulty} onChange={e=>setQuestion({...question,difficulty:e.target.value})}><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select></label>
        <label>Number of prompts<input type="number" min="1" max="10" value={question.count} onChange={e=>setQuestion({...question,count:e.target.value})}/></label>
        <button className="button primary" disabled={questionLoading}>{questionLoading?"Generating…":"Generate practice questions"}</button>
      </form>
      <ResultMessage error={questionError}/>
      {questionResult && <div className="growth-result"><ol className="growth-question-list">{questionResult.questions.map(item=><li key={item.number}><span>{item.type}</span><strong>{item.question}</strong><small>{item.self_check}</small></li>)}</ol><p className="muted">{questionResult.notice}</p></div>}
    </Section>

    <Section icon={BriefcaseBusiness} eyebrow="Skills and pathways" title="Career Readiness Predictor">
      <form className="growth-form" onSubmit={submitCareer}>
        <label>Target role<select value={career.target_role} onChange={e=>setCareer({...career,target_role:e.target.value})}>{["Software Developer","Data Analyst","AI/ML Engineer","Cybersecurity Analyst","Cloud Engineer"].map(role=><option key={role}>{role}</option>)}</select></label>
        <label>Projects completed<input type="number" min="0" max="100" value={career.projects_count} onChange={e=>setCareer({...career,projects_count:e.target.value})}/></label>
        <label className="growth-wide">Skills you have (comma-separated)<textarea rows={3} value={career.skills} onChange={e=>setCareer({...career,skills:e.target.value})} placeholder="Python, SQL, machine learning, Git…"/></label>
        <label className="growth-check"><input type="checkbox" checked={career.internship_experience} onChange={e=>setCareer({...career,internship_experience:e.target.checked})}/> Internship experience</label>
        <label className="growth-check"><input type="checkbox" checked={career.portfolio_ready} onChange={e=>setCareer({...career,portfolio_ready:e.target.checked})}/> Portfolio ready</label>
        <button className="button primary" disabled={careerLoading}>{careerLoading?"Checking skills…":"Assess role readiness"}</button>
      </form>
      <ResultMessage error={careerError}/>
      {careerResult && <div className="growth-result"><div className="growth-readiness"><strong>{careerResult.skill_coverage_percentage}%</strong><span>Illustrative skill-map coverage · {careerResult.target_role}</span></div><div className="growth-chip-list">{careerResult.matched_skills.map(skill=><span className="growth-chip matched" key={skill}>✓ {skill}</span>)}{careerResult.suggested_skill_gaps.map(skill=><span className="growth-chip gap" key={skill}>Learn: {skill}</span>)}</div><h3>Suggested next steps</h3><ul>{careerResult.next_steps.map(item=><li key={item}>{item}</li>)}</ul><p className="muted">{careerResult.interpretation}</p></div>}
    </Section>

    <Section icon={Award} eyebrow="Financial support discovery" title="Scholarship Recommendation Engine">
      <form className="growth-form" onSubmit={submitScholarship}>
        <label>Academic percentage<input type="number" min="0" max="100" step="0.1" value={scholarship.academic_percentage} onChange={e=>setScholarship({...scholarship,academic_percentage:e.target.value})}/></label>
        <label>Course area<input value={scholarship.course_area} onChange={e=>setScholarship({...scholarship,course_area:e.target.value})} required placeholder="e.g. Information Science"/></label>
        <label>Annual family income band<select value={scholarship.annual_income_band} onChange={e=>setScholarship({...scholarship,annual_income_band:e.target.value})}><option value="undisclosed">Prefer not to say</option><option value="lower">Lower income band</option><option value="middle">Middle income band</option><option value="higher">Higher income band</option></select></label>
        <label>State / domicile (optional)<input value={scholarship.state} onChange={e=>setScholarship({...scholarship,state:e.target.value})} placeholder="e.g. Karnataka"/></label>
        <button className="button primary" disabled={scholarshipLoading}>{scholarshipLoading?"Finding pathways…":"Find potential pathways"}</button>
      </form>
      <ResultMessage error={scholarshipError}/>
      {scholarshipResult && <div className="growth-result"><div className="growth-opportunity-list">{scholarshipResult.potential_pathways.map(item=><article key={item.pathway}><span className="badge">{item.match}</span><strong>{item.pathway}</strong><p>{item.reason}</p><small>{item.verify}</small></article>)}</div><h3>Application preparation</h3><ul>{scholarshipResult.next_steps.map(item=><li key={item}>{item}</li>)}</ul><p className="muted">{scholarshipResult.disclaimer}</p></div>}
    </Section>
  </>;
}
