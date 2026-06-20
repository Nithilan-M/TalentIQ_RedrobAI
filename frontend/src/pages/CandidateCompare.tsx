import React, { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { ArrowLeft, BarChart2, ShieldAlert, Sparkles, RefreshCw } from "lucide-react";
import { apiService } from "../services/api";
import { GlassCard } from "../components/GlassCard";
import { 
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar 
} from "recharts";

export const CandidateCompare: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [candidates, setCandidates] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadComparison();
  }, [searchParams]);

  const loadComparison = async () => {
    const idsString = searchParams.get("ids");
    if (!idsString) {
      setError("No candidate IDs provided for comparison.");
      setLoading(false);
      return;
    }

    const ids = idsString.split(",").map(Number);
    setLoading(true);
    setError(null);
    try {
      const data = await apiService.compareCandidates(ids);
      setCandidates(data);
    } catch (err: any) {
      setError(err.message || "Failed to load comparison data.");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center bg-slate-50/50">
        <div className="flex flex-col items-center gap-3">
          <RefreshCw className="h-7 w-7 animate-spin text-red-500" />
          <p className="text-xs font-semibold text-slate-500">Compiling candidate comparison datasets...</p>
        </div>
      </div>
    );
  }

  if (error || candidates.length === 0) {
    return (
      <div className="mx-auto max-w-md px-4 py-16 text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-50 text-red-500 mb-4 border border-red-200">
          <ShieldAlert className="h-6 w-6" />
        </div>
        <h2 className="text-base font-semibold text-slate-900 mb-1.5">Comparison Error</h2>
        <p className="text-xs text-slate-500 mb-6 leading-relaxed">{error || "No candidate profiles could be loaded."}</p>
        <button
          onClick={() => navigate("/")}
          className="inline-flex h-9 items-center justify-center rounded-lg bg-red-500 px-4 text-xs font-semibold text-white shadow-sm hover:bg-red-600 transition-all cursor-pointer"
        >
          Return to Dashboard
        </button>
      </div>
    );
  }

  // Dimensions evaluated: Skill Match, Experience, Projects, Education, Certifications, Leadership, Soft Skills
  const dimensions = [
    { subject: "Skill Match", key: "skill_match_score" },
    { subject: "Experience", key: "experience_score" },
    { subject: "Projects", key: "projects_score" },
    { subject: "Education", key: "education_score" },
    { subject: "Certifications", key: "certifications_score" },
    { subject: "Leadership", key: "leadership_score" },
    { subject: "Soft Skills", key: "soft_skills_score" }
  ];

  const radarData = dimensions.map((dim) => {
    const row: any = { subject: dim.subject };
    candidates.forEach((c) => {
      row[c.name] = c[dim.key] || 0;
    });
    return row;
  });

  // Colors for candidates (shades of premium red, crimson, rose)
  const colors = ["#EF4444", "#3B82F6", "#10B981", "#F59E0B"];

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6 flex items-center gap-3">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors cursor-pointer"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back</span>
        </button>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          Committee Comparison Panel
        </h1>
      </div>

      {/* Visual Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Match Scores Bar Chart */}
        <GlassCard>
          <h3 className="text-sm font-semibold text-slate-900 mb-6 flex items-center gap-2">
            <BarChart2 className="h-4.5 w-4.5 text-red-500" />
            Overall Fit Score Comparison
          </h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={candidates} margin={{ top: 0, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" horizontal={true} vertical={false} />
                <XAxis dataKey="name" stroke="#94A3B8" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis domain={[0, 100]} stroke="#94A3B8" fontSize={10} tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#ffffff', 
                    borderColor: '#E2E8F0', 
                    borderRadius: '8px', 
                    fontSize: '11px',
                    fontFamily: 'Inter, sans-serif',
                    boxShadow: '0 1px 3px 0 rgba(0,0,0,0.05)'
                  }} 
                />
                <Bar dataKey="overall_score" name="Overall Match Score" radius={[4, 4, 0, 0]} barSize={32}>
                  {candidates.map((_, index) => (
                    <Bar key={`cell-${index}`} fill={colors[index % colors.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        {/* Competency Radar Chart */}
        <GlassCard>
          <h3 className="text-sm font-semibold text-slate-900 mb-6 flex items-center gap-2">
            <Sparkles className="h-4.5 w-4.5 text-red-500" />
            Dimension Competency Breakdown
          </h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarData}>
                <PolarGrid stroke="#E2E8F0" />
                <PolarAngleAxis dataKey="subject" stroke="#64748B" fontSize={10} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#94A3B8" fontSize={9} />
                {candidates.map((c, index) => (
                  <Radar
                    key={c.id}
                    name={c.name}
                    dataKey={c.name}
                    stroke={colors[index % colors.length]}
                    fill={colors[index % colors.length]}
                    fillOpacity={0.15}
                  />
                ))}
                <Legend iconType="circle" wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#ffffff', 
                    borderColor: '#E2E8F0', 
                    borderRadius: '8px', 
                    fontSize: '11px',
                    fontFamily: 'Inter, sans-serif',
                    boxShadow: '0 1px 3px 0 rgba(0,0,0,0.05)'
                  }} 
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>
      </div>

      {/* Detailed Side-by-side Table Matrix */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden mb-8">
        <div className="border-b border-slate-100 px-6 py-4">
          <h3 className="text-sm font-semibold text-slate-900">
            Side-by-Side Comparison Matrix
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Granular breakdown of evaluated performance dimensions, qualifications, and verdicts.
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-600">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                <th className="py-3 px-6 w-1/5">Parameters</th>
                {candidates.map((c, idx) => (
                  <th key={c.id} className="py-3 px-6 w-1/4">
                    <div className="flex items-center gap-2 font-semibold text-slate-800">
                      <span className="h-2.5 w-2.5 rounded-full inline-block" style={{ backgroundColor: colors[idx % colors.length] }} />
                      {c.name}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {/* Overall Score Row */}
              <tr className="hover:bg-slate-50/30 transition-colors">
                <td className="py-4 px-6 font-semibold text-slate-950">Overall Match</td>
                {candidates.map((c) => (
                  <td key={c.id} className="py-4 px-6 font-extrabold text-red-600 text-base">
                    {c.overall_score}%
                  </td>
                ))}
              </tr>

              {/* Verdict Decision Row */}
              <tr className="hover:bg-slate-50/30 transition-colors">
                <td className="py-4 px-6 font-semibold text-slate-950">Verdict</td>
                {candidates.map((c) => {
                  const decColors: Record<string, string> = {
                    "Strong Hire": "bg-emerald-50 text-emerald-700 border border-emerald-200/60",
                    "Hire": "bg-red-50 text-red-700 border border-red-250/60",
                    "Borderline": "bg-amber-50 text-amber-700 border border-amber-200/60",
                    "No Hire": "bg-rose-50 text-rose-700 border border-rose-200/60"
                  };
                  return (
                    <td key={c.id} className="py-4 px-6 font-bold">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] tracking-wide inline-block border ${decColors[c.decision] || ""}`}>
                        {c.decision}
                      </span>
                    </td>
                  );
                })}
              </tr>

              {/* Core Skills Row */}
              <tr className="hover:bg-slate-50/30 transition-colors">
                <td className="py-4 px-6 font-semibold text-slate-950">Skills Map</td>
                {candidates.map((c) => (
                  <td key={c.id} className="py-4 px-6">
                    <div className="flex flex-wrap gap-1 max-h-[120px] overflow-y-auto">
                      {c.skills.slice(0, 10).map((skill: string, i: number) => (
                        <span key={i} className="text-[10px] font-medium px-2 py-0.5 rounded border border-slate-200/50 bg-slate-50 text-slate-600">
                          {skill}
                        </span>
                      ))}
                      {c.skills.length > 10 && (
                        <span className="text-[10px] font-bold text-slate-400 pl-1 self-center">+{c.skills.length - 10} more</span>
                      )}
                    </div>
                  </td>
                ))}
              </tr>

              {/* Total Experience Row */}
              <tr className="hover:bg-slate-50/30 transition-colors">
                <td className="py-4 px-6 font-semibold text-slate-950">Past Roles Count</td>
                {candidates.map((c) => (
                  <td key={c.id} className="py-4 px-6 text-slate-700 font-semibold">
                    {c.experience_count} companies
                  </td>
                ))}
              </tr>

              {/* Total Projects Row */}
              <tr className="hover:bg-slate-50/30 transition-colors">
                <td className="py-4 px-6 font-semibold text-slate-950">Portfolio Projects</td>
                {candidates.map((c) => (
                  <td key={c.id} className="py-4 px-6 text-slate-700 font-semibold">
                    {c.project_count} projects
                  </td>
                ))}
              </tr>

              {/* Certifications Row */}
              <tr className="hover:bg-slate-50/30 transition-colors">
                <td className="py-4 px-6 font-semibold text-slate-950">Certifications</td>
                {candidates.map((c) => (
                  <td key={c.id} className="py-4 px-6 text-slate-700 font-semibold">
                    {c.certification_count} certs
                  </td>
                ))}
              </tr>

              {/* Consensus Paragraph */}
              <tr className="hover:bg-slate-50/30 transition-colors">
                <td className="py-4 px-6 font-semibold text-slate-950">AI Consensus Note</td>
                {candidates.map((c) => (
                  <td key={c.id} className="py-4 px-6 text-slate-500 leading-relaxed max-w-[200px]">
                    {c.summary}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default CandidateCompare;
