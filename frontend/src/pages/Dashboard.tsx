import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { 
  Users, TrendingUp, Sparkles, Search, FileDown, 
  GitCompare, AlertCircle, FileText, ChevronRight, Download
} from "lucide-react";
import { apiService } from "../services/api";
import { GlassCard } from "../components/GlassCard";

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [activeJdId, setActiveJdId] = useState<number | null>(null);
  const [activeJdTitle, setActiveJdTitle] = useState<string>("");
  const [candidates, setCandidates] = useState<any[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [stats, setStats] = useState({
    total_candidates: 0,
    average_match_score: 0,
    high_potential_count: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    setLoading(true);
    setError(null);
    const savedJdId = localStorage.getItem("active_jd_id");
    if (!savedJdId) {
      setError("No active job description loaded. Please upload a Job Description to begin.");
      setLoading(false);
      return;
    }

    try {
      const jdId = Number(savedJdId);
      setActiveJdId(jdId);
      
      // Fetch JD details
      const jdDetails = await apiService.getJobDescriptionDetails(jdId);
      setActiveJdTitle(jdDetails.title);

      // Fetch Candidates list
      const candidateList = await apiService.listCandidates(jdId);
      setCandidates(candidateList);

      // Fetch Analytics summary stats
      const analytics = await apiService.getAnalytics(jdId);
      setStats({
        total_candidates: analytics.total_candidates,
        average_match_score: analytics.average_match_score,
        high_potential_count: analytics.high_potential_count
      });
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to load dashboard data. Ensure backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeJdId) return;
    setLoading(true);
    try {
      const results = await apiService.listCandidates(activeJdId, searchQuery);
      setCandidates(results);
    } catch (err) {
      console.error("Semantic search failed:", err);
    } finally {
      setLoading(false);
    }
  };

  const toggleSelectCandidate = (id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleCompare = () => {
    if (selectedIds.length < 2) return;
    navigate(`/compare?ids=${selectedIds.join(",")}`);
  };

  const handleExportCSV = async () => {
    if (!activeJdId) return;
    try {
      const blob = await apiService.exportCandidatesCSV(activeJdId);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `Candidates_Rankings_${activeJdTitle.replace(/\s+/g, "_")}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error(err);
      alert("Failed to export candidates listing CSV.");
    }
  };

  const handleDownloadPDF = async (candidateId: number, name: string) => {
    try {
      const blob = await apiService.exportCandidatePDF(candidateId);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `Candidate_Dossier_${name.replace(/\s+/g, "_")}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error(err);
      alert("Failed to export candidate dossier PDF.");
    }
  };

  if (loading && candidates.length === 0) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center dark:bg-slate-950">
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-primary-500 border-t-transparent" />
          <p className="text-sm font-semibold text-slate-500">Accessing Recruiter Dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Top Banner */}
      <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Recruiter Dashboard
          </h1>
          {activeJdTitle ? (
            <p className="mt-1 text-sm text-slate-500">
              Active Job Description: <span className="font-semibold text-red-500">{activeJdTitle}</span>
            </p>
          ) : (
            <p className="mt-1 text-sm text-red-500 font-semibold flex items-center gap-1">
              <AlertCircle className="h-4 w-4" />
              Upload a Job Description to get started!
            </p>
          )}
        </div>

        {activeJdTitle && (
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={handleExportCSV}
              className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm transition-all cursor-pointer"
            >
              <FileDown className="h-4 w-4 text-slate-400" />
              <span>Export CSV</span>
            </button>
            <button
              onClick={() => navigate("/upload-resume")}
              className="flex items-center gap-1.5 rounded-lg bg-red-500 px-3.5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-red-600 transition-all cursor-pointer"
            >
              <span>+ Parse Resumes</span>
            </button>
          </div>
        )}
      </div>

      {error && (
        <GlassCard className="border-red-100 bg-red-50/50 p-8 mb-6 text-center">
          <AlertCircle className="mx-auto h-10 w-10 text-red-500 mb-3" />
          <h3 className="text-lg font-bold text-slate-900 mb-1">No Active Context</h3>
          <p className="text-slate-500 mb-6 max-w-sm mx-auto text-sm">{error}</p>
          <button
            onClick={() => navigate("/upload-jd")}
            className="rounded-lg bg-red-500 px-5 py-2 text-sm font-semibold text-white shadow hover:bg-red-600 cursor-pointer"
          >
            Create Job Description
          </button>
        </GlassCard>
      )}

      {activeJdTitle && (
        <>
          {/* Dashboard Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <GlassCard className="flex items-center gap-4 p-5">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-slate-200 text-slate-600 bg-slate-50">
                <Users className="h-5 w-5" />
              </div>
              <div>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Total Candidates</span>
                <h3 className="text-2xl font-bold text-slate-900 mt-0.5">{stats.total_candidates}</h3>
              </div>
            </GlassCard>

            <GlassCard className="flex items-center gap-4 p-5">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-slate-200 text-slate-600 bg-slate-50">
                <TrendingUp className="h-5 w-5" />
              </div>
              <div>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Average Match score</span>
                <h3 className="text-2xl font-bold text-slate-900 mt-0.5">{stats.average_match_score}%</h3>
              </div>
            </GlassCard>

            <GlassCard className="flex items-center gap-4 p-5">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-slate-200 text-slate-600 bg-slate-50">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">High Potential</span>
                <h3 className="text-2xl font-bold text-slate-900 mt-0.5">{stats.high_potential_count}</h3>
              </div>
            </GlassCard>
          </div>

          {/* Semantic Search Bar */}
          <GlassCard className="mb-6 p-4">
            <form onSubmit={handleSearch} className="flex gap-2">
              <div className="relative flex-1">
                <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">
                  <Search className="h-4 w-4" />
                </span>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder='Search candidates semantically, e.g. "React developer who knows FastAPI and Docker"'
                  className="h-10 w-full rounded-lg border border-slate-200 bg-white py-2 pl-9 pr-3 text-sm outline-none transition-all focus:border-red-500 focus:ring-1 focus:ring-red-500 text-slate-900 placeholder:text-slate-400"
                />
              </div>
              <button
                type="submit"
                className="h-10 rounded-lg bg-red-500 px-5 text-sm font-medium text-white shadow-sm hover:bg-red-600 transition-all cursor-pointer"
              >
                Search
              </button>
            </form>
          </GlassCard>

          {/* Candidates Table List */}
          <GlassCard className="overflow-hidden p-0">
            <div className="flex items-center justify-between border-b border-slate-200 px-6 py-5 gap-4">
              <h3 className="text-base font-semibold text-slate-900">
                Candidate Evaluation List
              </h3>
              
              {selectedIds.length >= 2 && (
                <button
                  onClick={handleCompare}
                  className="flex items-center gap-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 px-3.5 py-1.5 text-xs font-semibold text-white shadow-sm transition-all cursor-pointer"
                >
                  <GitCompare className="h-3.5 w-3.5" />
                  <span>Compare Candidates ({selectedIds.length})</span>
                </button>
              )}
            </div>

            {candidates.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-slate-400">
                <FileText className="h-10 w-10 text-slate-300 mb-2" />
                <p className="text-xs">No candidates processed yet. Upload resumes to generate rankings!</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-500">
                  <thead>
                    <tr className="border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider bg-slate-50/75">
                      <th className="py-3 px-3 text-center w-[40px]">
                        <span className="sr-only">Select</span>
                      </th>
                      <th className="py-3 px-4">Name</th>
                      <th className="py-3 px-4 text-center">Score</th>
                      <th className="py-3 px-4 text-center">AI Decision</th>
                      {candidates[0]?.similarity_score !== undefined && (
                        <th className="py-3 px-4 text-center">Search Match</th>
                      )}
                      <th className="py-3 px-4">Top Skills</th>
                      <th className="py-3 px-4 text-right pr-6">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {candidates.map((c) => {
                      const decColors: Record<string, string> = {
                        "Strong Hire": "bg-emerald-50 text-emerald-700 border-emerald-200",
                        "Hire": "bg-blue-50 text-blue-700 border-blue-200",
                        "Borderline": "bg-amber-50 text-amber-700 border-amber-200",
                        "No Hire": "bg-rose-50 text-rose-700 border-rose-200"
                      };

                      return (
                        <tr key={c.id} className="hover:bg-slate-50/50 transition-colors">
                          <td className="py-3.5 px-3 text-center">
                            <input
                              type="checkbox"
                              checked={selectedIds.includes(c.id)}
                              onChange={() => toggleSelectCandidate(c.id)}
                              className="h-4 w-4 rounded border-slate-300 text-red-500 focus:ring-red-500 cursor-pointer"
                            />
                          </td>
                          <td className="py-3.5 px-4 font-semibold text-slate-900">
                            {c.name}
                            <span className="block text-xs font-normal text-slate-500 mt-0.5">{c.email}</span>
                          </td>
                          <td className="py-3.5 px-4 text-center font-bold text-red-500 text-base">
                            {c.overall_score}%
                          </td>
                          <td className="py-3.5 px-4 text-center font-medium">
                            <span className={`px-2.5 py-1 rounded-md text-[11px] font-medium border ${decColors[c.decision] || "bg-slate-50 text-slate-600 border-slate-200"}`}>
                              {c.decision}
                            </span>
                          </td>
                          {c.similarity_score !== undefined && (
                            <td className="py-3.5 px-4 text-center font-semibold text-slate-600">
                              {c.similarity_score > 0 ? `${(c.similarity_score * 100).toFixed(0)}%` : "0%"}
                            </td>
                          )}
                          <td className="py-3.5 px-4">
                            <div className="flex flex-wrap gap-1 max-w-[220px]">
                              {c.skills.slice(0, 4).map((skill: string, i: number) => (
                                <span key={i} className="text-[10px] font-medium px-2 py-0.5 rounded border border-slate-200 bg-slate-50 text-slate-600">
                                  {skill}
                                </span>
                              ))}
                              {c.skills.length > 4 && (
                                <span className="text-[9px] font-bold text-slate-400 pl-1 align-middle">+{c.skills.length - 4}</span>
                              )}
                            </div>
                          </td>
                          <td className="py-3.5 px-4 text-right pr-6">
                            <div className="flex items-center justify-end gap-1.5">
                              <button
                                onClick={() => handleDownloadPDF(c.id, c.name)}
                                className="flex h-8 w-8 items-center justify-center rounded-md border border-slate-200 bg-white hover:bg-slate-50 text-slate-400 hover:text-slate-600 transition-colors"
                              >
                                <Download className="h-4 w-4" />
                              </button>
                              <button
                                onClick={() => navigate(`/candidate/${c.id}`)}
                                className="flex items-center gap-1 rounded-md border border-slate-200 bg-white hover:bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-700 transition-all"
                              >
                                <span>Details</span>
                                <ChevronRight className="h-3 w-3" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </GlassCard>
        </>
      )}
    </div>
  );
};

export default Dashboard;
