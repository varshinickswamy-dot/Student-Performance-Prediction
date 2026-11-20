import React, { useState } from "react";
import { AlertCircle, BrainCircuit, LoaderCircle, Sparkles } from "lucide-react";
import api, { getApiErrorMessage } from "./api";

const initial = {
  attendance_pct: 85, study_hours_per_week: 18, sleep_hours: 7,
  previous_sgpa: 8, backlogs: 0, internal_test_1: 38,
  internal_test_2: 40, assignment_score: 18,
  extracurricular: false, internet_access: true,
};

const fields = [
  ["attendance_pct", "Attendance (%)", 0, 100, 1],
  ["study_hours_per_week", "Study hours per week", 0, 60, 1],
  ["sleep_hours", "Sleep hours per day", 0, 24, 0.5],
  ["previous_sgpa", "Previous SGPA", 0, 10, 0.1],
  ["backlogs", "Current backlogs", 0, 30, 1],
  ["internal_test_1", "Internal test 1 (out of 50)", 0, 50, 1],
  ["internal_test_2", "Internal test 2 (out of 50)", 0, 50, 1],
  ["assignment_score", "Assignment score (out of 20)", 0, 20, 1],
];

export default function FinalExamPrediction() {
  const [form, setForm] = useState(initial);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const update = (event) => {
    const { name, value, type, checked } = event.target;
    setForm((current) => ({ ...current, [name]: type === "checkbox" ? checked : Number(value) }));
    setResult(null);
  };

  const submit = async (event) => {
    event.preventDefault();
    setLoading(true); setError(""); setResult(null);
    try {
      const response = await api.post("/api/student/final-exam-prediction", form);
      setResult(response.data);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return <section>
    <div className="page-heading"><div><span>Experimental model · Synthetic dataset</span><h1>Final Exam Score Estimator</h1><p className="muted">Explore a separate candidate model using academic and study inputs.</p></div></div>
    <div className="panel" style={{marginBottom:20}}>
      <div className="panel-heading"><div><span>Candidate model</span><h3><BrainCircuit size={18}/> Before-exam academic inputs</h3></div><span className="badge">Offline candidate</span></div>
      <p className="muted">This estimator is separate from your existing EduPredict score prediction. It is available only when the server has a compatible candidate artifact configured.</p>
      <form onSubmit={submit}>
        <div className="form-grid">
          {fields.map(([name,label,min,max,step])=><label key={name}>{label}<input type="number" name={name} min={min} max={max} step={step} value={form[name]} onChange={update} required/></label>)}
        </div>
        <div className="form-grid" style={{marginTop:16}}>
          <label><input type="checkbox" name="extracurricular" checked={form.extracurricular} onChange={update}/> Participates in extracurricular activities</label>
          <label><input type="checkbox" name="internet_access" checked={form.internet_access} onChange={update}/> Has internet access</label>
        </div>
        {error && <div className="alert" role="alert"><AlertCircle size={17}/> {error}</div>}
        <button className="button primary" type="submit" disabled={loading} style={{marginTop:18}}>{loading?<><LoaderCircle className="spin"/> Estimating…</>:<><Sparkles size={17}/> Estimate final exam score</>}</button>
      </form>
    </div>
    {result && <article className="panel" aria-live="polite">
      <span className="eyebrow">Synthetic demonstration estimate</span>
      <div className="forecast"><strong>{result.predicted_final_exam_score}</strong><small> / 100</small></div>
      <p>Model: {result.model_type} · Version: {result.model_version}</p>
      <p className="muted">Held-out test MAE: {result.held_out_test_metrics?.mae ?? "Not supplied"}</p>
      <p className="muted">{result.disclaimer}</p>
    </article>}
  </section>;
}
