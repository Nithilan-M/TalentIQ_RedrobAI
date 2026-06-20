import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { 
  ArrowLeft, FileDown, ShieldAlert, AlertTriangle, Sparkles, 
  HelpCircle, Calendar, User, CheckCircle2, RefreshCw 
} from "lucide-react";
import { apiService } from "../services/api";
import { GlassCard } from "../components/GlassCard";

export const CandidateDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      fetchDetails();
    }
  }, [id]);

  const fetchDetails = async () => {
    setLoading(true);
    setError(null);
    try {
      const details = await apiService.getCandidateDetails(Number(id));
      setData(details);
    } catch (err: any) {
      setError(err.message || "Failed to load candidate details.");
    } finally {
      setLoading(false);
    }
  };

  const handleExportPDF = async () => {
    if (!id || !data) return;
    try {
      const blob = await apiService.exportCandidatePDF(Number(id));
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `Candidate_Report_${data.candidate.name.replace(/\s+/g, "_")}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error("Failed to export PDF:", err);
      alert("Failed to export PDF dossier.");
    }
  };

  const handleRegenerateQuestions = async () => {
    if (!id) return;
    setRegenerating(true);
    try {
      const qs = await apiService.regenerateInterviewQuestions(Number(id));
      setData((prev: any) => ({ ...prev, interview_questions: qs }));
    } catch (err) {
      alert("Failed to regenerate questions.");
    } finally {
      setRegenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center bg-slate-50/50">
        <div className="flex flex-col items-center gap-3">
          <RefreshCw className="h-7 w-7 animate-spin text-red-500" />
          <p className="text-xs font-semibold text-slate-500">Evaluating candidate profiles...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="mx-auto max-w-md px-4 py-16 text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-50 text-red-500 mb-4 border border-red-200">
          <AlertTriangle className="h-6 w-6" />
        </div>
        <h2 className="text-base font-semibold text-slate-900 mb-1.5">Error Loading Details</h2>
        <p className="text-xs text-slate-500 mb-6 leading-relaxed">{error || "Candidate record not found."}</p>
        <button
          onClick={() => navigate("/")}
          className="inline-flex h-9 items-center justify-center rounded-lg bg-red-500 px-4 text-xs font-semibold text-white shadow-sm hover:bg-red-600 transition-all cursor-pointer"
        >
          Return to Dashboard
        </button>
      </div>
    );
  }

  const { candidate, ranking, recommendation, explainability, interview_questions } = data;

  // Decision style mapping
  const decisionColors: Record<string, string> = {
    "Strong Hire": "bg-emerald-50 text-emerald-700 border-emerald-200/60",
    "Hire": "bg-red-50 text-red-700 border-red-200/60",
    "Borderline": "bg-amber-50 text-amber-700 border-amber-200/60",
    "No Hire": "bg-rose-50 text-rose-700 border-rose-200/60"
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Header Controls */}
      <div className="mb-6 flex items-center justify-between">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors cursor-pointer"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to candidates</span>
        </button>

        <button
          onClick={handleExportPDF}
          className="flex h-9 items-center justify-center gap-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 px-4 text-xs font-semibold text-slate-700 shadow-sm transition-all cursor-pointer"
        >
          <FileDown className="h-4 w-4 text-red-500" />
          <span>Export Dossier PDF</span>
        </button>
      </div>

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Candidate Info Card & Scores */}
        <div className="lg:col-span-1 space-y-6">
          {/* Profile Overview */}
          <GlassCard>
            <div className="flex items-center gap-4 mb-6">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-red-50 border border-red-100 text-red-500 shadow-sm">
                <User className="h-5.5 w-5.5" />
              </div>
              <div className="min-w-0 flex-1">
                <h2 className="text-base font-bold text-slate-900 truncate">{candidate.name}</h2>
                <p className="text-xs text-slate-500 mt-0.5 truncate">{candidate.email || "No email"}</p>
                <p className="text-xs text-slate-500 truncate">{candidate.phone || "No phone"}</p>
              </div>
            </div>

            <div className="border-t border-slate-100 pt-4 space-y-2.5">
              <div className="flex justify-between items-center py-0.5">
                <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Verdict</span>
                <span className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${decisionColors[recommendation?.judge_decision || "Borderline"]}`}>
                  {recommendation?.judge_decision || "Borderline"}
                </span>
              </div>
              <div className="flex justify-between items-center py-0.5">
                <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Overall Match</span>
                <span className="text-base font-extrabold text-red-600">{ranking.overall_score}%</span>
              </div>
              <div className="flex justify-between items-center py-0.5">
                <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Judge Confidence</span>
                <span className="text-xs font-semibold text-slate-700">{recommendation?.judge_confidence}%</span>
              </div>
            </div>
          </GlassCard>

          {/* Explainability / Risk Ratings */}
          <GlassCard>
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider border-b border-slate-100 pb-3 mb-4 flex items-center gap-1.5">
              <ShieldAlert className="h-4 w-4 text-red-500" />
              AI Fit Diagnostics
            </h3>
            
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-xs font-semibold mb-1">
                  <span className="text-slate-500">Growth Potential</span>
                  <span className="text-emerald-600 font-bold">{explainability.potential_score}%</span>
                </div>
                <div className="h-1.5 w-full rounded-full bg-slate-100 overflow-hidden">
                  <div 
                    className="h-full rounded-full bg-emerald-500 transition-all duration-1000"
                    style={{ width: `${explainability.potential_score}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs font-semibold mb-1">
                  <span className="text-slate-500">Hiring Risk Factor</span>
                  <span className="text-red-500 font-bold">{explainability.risk_score}%</span>
                </div>
                <div className="h-1.5 w-full rounded-full bg-slate-100 overflow-hidden">
                  <div 
                    className="h-full rounded-full bg-red-500 transition-all duration-1000"
                    style={{ width: `${explainability.risk_score}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Missing Skills */}
            <div className="mt-6">
              <h4 className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2.5">
                Missing Required Skills
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {explainability.missing_skills?.length > 0 ? (
                  explainability.missing_skills.map((skill: string, i: number) => (
                    <span key={i} className="rounded-md bg-red-50 px-2 py-0.5 text-xs font-medium text-red-600 border border-red-200/50">
                      {skill}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-emerald-600 font-semibold italic flex items-center gap-1">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    All required skills present
                  </span>
                )}
              </div>
            </div>
          </GlassCard>

          {/* Evidence Checklist */}
          <GlassCard>
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4 pb-1">
              Scoring Evidence Used
            </h3>
            <ul className="space-y-3 text-xs text-slate-600">
              {explainability.evidence?.map((item: string, i: number) => (
                <li key={i} className="flex gap-2 items-start">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                  <span className="leading-relaxed">{item}</span>
                </li>
              ))}
            </ul>
          </GlassCard>
        </div>

        {/* Right Columns: AI Committee Debate & Candidate Profile details */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Section 1: AI Committee Decision Debate */}
          <GlassCard>
            <h3 className="text-sm font-semibold text-slate-900 mb-1 flex items-center gap-2">
              <Sparkles className="h-4.5 w-4.5 text-red-500" />
              AI Hiring Committee Debate
            </h3>
            <p className="text-xs text-slate-500 mb-6">
              Evaluation debate transcript and final recommendations consensus.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 border-b border-slate-100 pb-5 mb-5">
              {/* Advocate Agent */}
              <div className="rounded-xl bg-emerald-50/10 border border-emerald-100 p-4">
                <h4 className="text-xs font-bold text-emerald-700 flex items-center gap-1.5 mb-2.5">
                  <Sparkles className="h-3.5 w-3.5" />
                  Advocate Case summary
                </h4>
                <div className="text-xs text-slate-600 space-y-2 leading-relaxed whitespace-pre-line">
                  {recommendation?.advocate_feedback}
                </div>
              </div>

              {/* Skeptic Agent */}
              <div className="rounded-xl bg-red-50/10 border border-red-100 p-4">
                <h4 className="text-xs font-bold text-red-600 flex items-center gap-1.5 mb-2.5">
                  <ShieldAlert className="h-3.5 w-3.5" />
                  Skeptic Risk assessment
                </h4>
                <div className="text-xs text-slate-600 space-y-2 leading-relaxed whitespace-pre-line">
                  {recommendation?.skeptic_feedback}
                </div>
              </div>
            </div>

            {/* Judge Consensus Summary */}
            <div>
              <h4 className="text-xs font-bold text-red-600 uppercase tracking-wider mb-2">
                Consensus Verdict
              </h4>
              <p className="text-xs text-slate-700 leading-relaxed font-medium bg-slate-50 p-4 rounded-lg border border-slate-200">
                {recommendation?.judge_summary}
              </p>
            </div>
          </GlassCard>

          {/* Section 2: Detailed Experience Timeline */}
          <GlassCard>
            <h3 className="text-sm font-semibold text-slate-900 mb-6 flex items-center gap-2">
              <Calendar className="h-4.5 w-4.5 text-red-500" />
              Work History Timeline
            </h3>

            <div className="relative border-l-2 border-slate-100 pl-5 ml-2.5 space-y-6">
              {candidate.experiences?.map((exp: any, i: number) => (
                <div key={i} className="relative">
                  <span className="absolute -left-[27px] top-1.5 flex h-3 w-3 items-center justify-center rounded-full bg-red-500 border border-white" />
                  <div>
                    <h4 className="text-xs font-bold text-slate-900">
                      {exp.role} <span className="text-slate-400 font-normal">at</span> <span className="text-red-500 font-semibold">{exp.company}</span>
                    </h4>
                    <span className="text-[11px] text-slate-500 font-medium block mt-0.5">
                      {exp.duration}
                    </span>
                    <p className="text-xs text-slate-500 mt-2 leading-relaxed whitespace-pre-line">
                      {exp.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>

          {/* Section 3: Custom Interview Guide */}
          <GlassCard>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                <HelpCircle className="h-4.5 w-4.5 text-red-500" />
                Interview Copilot Guide
              </h3>
              <button
                onClick={handleRegenerateQuestions}
                disabled={regenerating}
                className="flex items-center gap-1 text-xs font-semibold text-red-500 hover:text-red-600 disabled:opacity-50 cursor-pointer"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${regenerating ? "animate-spin" : ""}`} />
                <span>Regenerate Guide</span>
              </button>
            </div>
            <p className="text-xs text-slate-500 mb-6">
              AI-generated behavioral and technical questions targeting resume gaps and candidate accomplishments.
            </p>

            <div className="space-y-3.5">
              {interview_questions?.map((q: any, i: number) => {
                const diffColors: Record<string, string> = {
                  "Easy": "bg-emerald-50 text-emerald-700 border border-emerald-200/50",
                  "Medium": "bg-amber-50 text-amber-700 border border-amber-200/50",
                  "Hard": "bg-rose-50 text-rose-700 border border-rose-200/50",
                };

                return (
                  <div key={i} className="p-4 rounded-xl border border-slate-200 bg-slate-50/40">
                    <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                      <span className="text-[10px] font-bold text-slate-600 bg-slate-100 px-2 py-0.5 rounded">
                        {q.category}
                      </span>
                      <span className={`text-[10px] font-semibold px-2.5 py-0.5 rounded-full ${diffColors[q.difficulty] || ""}`}>
                        {q.difficulty}
                      </span>
                    </div>
                    <p className="text-xs font-bold text-slate-800 mb-2 leading-snug">
                      {q.question}
                    </p>
                    <p className="text-xs text-slate-500 leading-normal">
                      <strong className="text-slate-700 font-semibold">Guidance:</strong> {q.guidance}
                    </p>
                  </div>
                );
              })}
            </div>
          </GlassCard>
          
        </div>
      </div>
    </div>
  );
};

export default CandidateDetails;
