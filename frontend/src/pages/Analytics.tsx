import React, { useEffect, useState } from "react";
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area 
} from "recharts";
import { 
  AlertCircle, BarChart2, Briefcase, GraduationCap, Award, 
  Sparkles, TrendingUp, Users, RefreshCw 
} from "lucide-react";
import { apiService } from "../services/api";
import { GlassCard } from "../components/GlassCard";

export const Analytics: React.FC = () => {
  const [analyticsData, setAnalyticsData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    const savedJdId = localStorage.getItem("active_jd_id");
    if (!savedJdId) {
      setError("No active Job Description selected. Please upload a Job Description first.");
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await apiService.getAnalytics(Number(savedJdId));
      setAnalyticsData(data);
    } catch (err: any) {
      setError(err.message || "Failed to load analytics.");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center bg-slate-50/50">
        <div className="flex flex-col items-center gap-3">
          <RefreshCw className="h-7 w-7 animate-spin text-red-500" />
          <p className="text-xs font-semibold text-slate-500">Aggregating hiring pipeline statistics...</p>
        </div>
      </div>
    );
  }

  if (error || !analyticsData) {
    return (
      <div className="mx-auto max-w-md px-4 py-16 text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-50 text-red-500 mb-4 border border-red-200">
          <AlertCircle className="h-6 w-6" />
        </div>
        <h2 className="text-base font-semibold text-slate-900 mb-1.5">Analytics Error</h2>
        <p className="text-xs text-slate-500 mb-6 leading-relaxed">{error || "No analytics data could be computed."}</p>
        <button
          onClick={() => window.location.reload()}
          className="inline-flex h-9 items-center justify-center rounded-lg bg-red-500 px-4 text-xs font-semibold text-white shadow-sm hover:bg-red-600 transition-all cursor-pointer"
        >
          Retry Load
        </button>
      </div>
    );
  }

  const { 
    total_candidates, average_match_score, high_potential_count, 
    skill_distribution, experience_distribution, education_distribution, 
    hiring_funnel, score_distribution 
  } = analyticsData;

  // Colors for charts (shades of premium red, crimson, rose)
  const COLORS = ["#EF4444", "#F87171", "#FCA5A5", "#FECACA"];
  const FUNNEL_COLORS = ["#EF4444", "#F87171", "#FB7185", "#FDA4AF"];

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          Recruitment Insights & Analytics
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Aggregated diagnostics across the entire candidate pool for the active role.
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-red-50 border border-red-100 text-red-500">
            <Users className="h-5 w-5" />
          </div>
          <div>
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">Total Candidates Evaluated</span>
            <h3 className="text-2xl font-bold text-slate-900 mt-1 tracking-tight">{total_candidates}</h3>
          </div>
        </div>

        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-slate-50 border border-slate-100 text-slate-600">
            <TrendingUp className="h-5 w-5" />
          </div>
          <div>
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">Average Match Fit Score</span>
            <h3 className="text-2xl font-bold text-slate-900 mt-1 tracking-tight">{average_match_score}%</h3>
          </div>
        </div>

        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-emerald-50 border border-emerald-100 text-emerald-600">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">High Potential (&gt; 80%)</span>
            <h3 className="text-2xl font-bold text-slate-900 mt-1 tracking-tight">{high_potential_count}</h3>
          </div>
        </div>
      </div>

      {/* Analytics Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Skill Gap Analysis Bar Chart */}
        <GlassCard>
          <h3 className="text-sm font-semibold text-slate-900 mb-6 flex items-center gap-2">
            <BarChart2 className="h-4.5 w-4.5 text-red-500" />
            Top 10 Candidate Skills Frequency
          </h3>
          <div className="h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={skill_distribution} margin={{ top: 0, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" horizontal={true} vertical={false} />
                <XAxis dataKey="skill" stroke="#94A3B8" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis stroke="#94A3B8" fontSize={10} tickLine={false} axisLine={false} />
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
                <Bar dataKey="count" fill="#EF4444" radius={[3, 3, 0, 0]} barSize={22} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        {/* Experience Distribution Pie Chart */}
        <GlassCard>
          <h3 className="text-sm font-semibold text-slate-900 mb-6 flex items-center gap-2">
            <Briefcase className="h-4.5 w-4.5 text-red-500" />
            Experience Bins Distribution
          </h3>
          <div className="h-[280px] flex items-center justify-center">
            {total_candidates === 0 ? (
              <span className="text-slate-400 italic text-xs">No metrics calculated yet</span>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={experience_distribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={85}
                    paddingAngle={4}
                    dataKey="count"
                    nameKey="range"
                    label={({ name, percent }) => `${name} (${((percent || 0) * 100).toFixed(0)}%)`}
                  >
                    {experience_distribution.map((_: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
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
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </GlassCard>

        {/* Education statistics */}
        <GlassCard>
          <h3 className="text-sm font-semibold text-slate-900 mb-6 flex items-center gap-2">
            <GraduationCap className="h-4.5 w-4.5 text-red-500" />
            Education Statistics (Degree Breakdown)
          </h3>
          <div className="h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={education_distribution} layout="vertical" margin={{ top: 0, right: 10, left: 10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" horizontal={true} vertical={false} />
                <XAxis type="number" stroke="#94A3B8" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis dataKey="degree" type="category" stroke="#64748B" fontSize={10} tickLine={false} axisLine={false} width={80} />
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
                <Bar dataKey="count" fill="#F87171" radius={[0, 3, 3, 0]} barSize={16} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        {/* Match Score Distribution Area Chart */}
        <GlassCard>
          <h3 className="text-sm font-semibold text-slate-900 mb-6 flex items-center gap-2">
            <Award className="h-4.5 w-4.5 text-red-500" />
            Candidate Score Spread Distribution
          </h3>
          <div className="h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={score_distribution} margin={{ top: 0, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" horizontal={true} vertical={false} />
                <XAxis dataKey="range" stroke="#94A3B8" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis stroke="#94A3B8" fontSize={10} tickLine={false} axisLine={false} />
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
                <Area type="monotone" dataKey="count" stroke="#EF4444" fill="#FEE2E2" fillOpacity={0.4} strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>
      </div>

      {/* Hiring Funnel Stage bar chart */}
      <GlassCard className="mb-8">
        <h3 className="text-sm font-semibold text-slate-900 mb-6 flex items-center gap-2">
          <Sparkles className="h-4.5 w-4.5 text-red-500" />
          Hiring Committee Verdict Funnel Stages
        </h3>
        <div className="h-[280px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={hiring_funnel} margin={{ top: 0, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" horizontal={true} vertical={false} />
              <XAxis dataKey="name" stroke="#94A3B8" fontSize={10} tickLine={false} axisLine={false} />
              <YAxis stroke="#94A3B8" fontSize={10} tickLine={false} axisLine={false} />
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
              <Bar dataKey="value" fill="#EF4444" radius={[4, 4, 0, 0]} barSize={28}>
                {hiring_funnel.map((_: any, index: number) => (
                  <Cell key={`cell-${index}`} fill={FUNNEL_COLORS[index % FUNNEL_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </GlassCard>
    </div>
  );
};

export default Analytics;
