import React, { useState, useEffect } from "react";
import { 
  Play, Sparkles, CheckCircle2, AlertCircle, Clock, Search, 
  Filter, FileText, BarChart2, ShieldAlert, RefreshCw, UploadCloud, Loader2
} from "lucide-react";
import { apiService } from "../services/api";
import { GlassCard } from "../components/GlassCard";
import { 
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, PieChart, Pie, Cell, Legend 
} from "recharts";
import { useChallenge } from "../context/ChallengeContext";

export const ChallengePanel: React.FC = () => {
  
  // Pipeline global state
  const {
    running,
    results,
    validation,
    error,
    selectedFile,
    setSelectedFile,
    progressPercent,
    progressStep,
    progressLogs,
    runPipeline: handleRunPipeline,
    setError
  } = useChallenge();
  
  const [dragActive, setDragActive] = useState(false);
  
  // Advanced search filters state
  const [searchQuery, setSearchQuery] = useState("");
  const [filterTitle, setFilterTitle] = useState("");
  const [filterLocation, setFilterLocation] = useState("");
  const filterNotice = "all";
  const [filterRisk, setFilterRisk] = useState("all");
  const [showFilters, setShowFilters] = useState(false);



  // Autoscroll logs console
  useEffect(() => {
    const consoleElem = document.getElementById("logs-console");
    if (consoleElem) {
      consoleElem.scrollTop = consoleElem.scrollHeight;
    }
  }, [progressLogs]);

  const isStageDone = (key: string) => {
    switch (key) {
      case "load_jd":
        return progressLogs.some(l => l.includes("Loaded Job Description"));
      case "load_cache":
        return progressLogs.some(l => l.includes("Loaded") && l.includes("profiles into cache"));
      case "load_vector_index":
        return progressLogs.some(l => l.includes("Loaded/Built vector index"));
      case "semantic_retrieval":
        return progressLogs.some(l => l.includes("Retrieved Top") && l.includes("candidates"));
      case "feature_eng_and_ranking":
        return progressLogs.some(l => l.includes("Engineered features"));
      case "write_csv":
        return progressLogs.some(l => l.includes("Exported submission CSV"));
      case "validation":
        return progressLogs.some(l => l.includes("Validated submission CSV"));
      default:
        return false;
    }
  };

  const isStageActive = (key: string) => {
    if (progressStep.includes("Failed") || progressStep.includes("complete")) return false;
    switch (key) {
      case "load_jd":
        return progressStep.includes("Job Description") && !isStageDone("load_jd");
      case "load_cache":
        return progressStep.includes("candidates") && !isStageDone("load_cache");
      case "load_vector_index":
        return progressStep.includes("vector index") && !isStageDone("load_vector_index");
      case "semantic_retrieval":
        return progressStep.includes("Semantic Retrieval") && !isStageDone("semantic_retrieval");
      case "feature_eng_and_ranking":
        return progressStep.includes("Hybrid Ranker") && !isStageDone("feature_eng_and_ranking");
      case "write_csv":
        return progressStep.includes("submission CSV") && !isStageDone("write_csv");
      case "validation":
        return progressStep.includes("Validating submission") && !isStageDone("validation");
      default:
        return false;
    }
  };



  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      validateAndSetFile(droppedFile);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (selectedFile: File) => {
    setError(null);
    const ext = selectedFile.name.split(".").pop()?.toLowerCase();
    if (ext !== "jsonl") {
      setError("Unsupported format. Please upload a .jsonl candidate dataset.");
      return;
    }
    setSelectedFile(selectedFile);
  };



  // Filter the list of top candidates locally based on advanced search criteria
  const getFilteredCandidates = () => {
    if (!results || !results.results) return [];
    
    return results.results.filter((c: any) => {
      // 1. Title filter
      if (filterTitle && !c.title.toLowerCase().includes(filterTitle.toLowerCase())) {
        return false;
      }
      
      // 2. Risk filter
      if (filterRisk !== "all" && c.risk_level !== filterRisk) {
        return false;
      }
      
      // 3. Location filter (mocked or checks raw explanation/info)
      if (filterLocation && !c.explanation.toLowerCase().includes(filterLocation.toLowerCase())) {
        // Simple search in explanation/reasoning details
        return false;
      }
      
      // 4. Notice Period (mock check)
      if (filterNotice !== "all") {
        const isShortNotice = c.explanation.toLowerCase().includes("notice");
        if (filterNotice === "short" && !isShortNotice) {
          // just a heuristic filter for demonstration
        }
      }

      // 5. Semantic Search Query
      if (searchQuery) {
        const text = `${c.name} ${c.title} ${c.explanation}`.toLowerCase();
        if (!text.includes(searchQuery.toLowerCase())) {
          return false;
        }
      }
      
      return true;
    });
  };

  const filteredCandidates = getFilteredCandidates();

  // Format Recharts data
  const getFeatureImportanceData = () => {
    if (!results || !results.feature_importances) return [];
    return Object.entries(results.feature_importances).map(([k, v]) => ({
      feature: k.replace("_score", "").replace("_", " "),
      importance: Math.round(Number(v) * 100)
    })).sort((a, b) => b.importance - a.importance);
  };

  const featureImportanceData = getFeatureImportanceData();
  const COLORS = ["#38A169", "#DD6B20", "#E53E3E"]; // Low, Medium, High risk colors

  const getRiskPieData = () => {
    if (!results || !results.risk_distribution) return [];
    return Object.entries(results.risk_distribution).map(([k, v]) => ({
      name: k,
      value: v
    }));
  };
  const riskPieData = getRiskPieData();

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Banner */}
      <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Redrob Challenge Control Panel
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Discovery pipeline: Ingestion of 100,000 candidates → FAISS search → LTR ranking → CSV Export & Validation.
          </p>
        </div>

        <button
          onClick={handleRunPipeline}
          disabled={running}
          className="flex h-10 items-center justify-center gap-2 rounded-lg bg-red-500 px-5 text-sm font-semibold text-white shadow-sm hover:bg-red-600 transition-all disabled:opacity-50 cursor-pointer"
        >
          {running ? (
            <>
              <RefreshCw className="h-4 w-4 animate-spin" />
              <span>Streaming & Ranking (CPU)...</span>
            </>
          ) : (
            <>
              <Play className="h-4 w-4" />
              <span>Run Pipeline Offline</span>
            </>
          )}
        </button>
      </div>

      {/* Dataset Upload Area */}
      <GlassCard className="mb-6 p-0">
        <input
          type="file"
          id="jsonl-upload"
          className="hidden"
          accept=".jsonl"
          onChange={handleFileChange}
        />
        
        {selectedFile ? (
          <div
            onDragEnter={handleDrag}
            onDragOver={handleDrag}
            onDragLeave={handleDrag}
            onDrop={handleDrop}
            className="flex flex-col items-center justify-center border-2 border-dashed rounded-xl p-8 text-center border-slate-200"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-50 border border-slate-200 text-slate-500 mb-3">
              <UploadCloud className="h-5 w-5" />
            </div>
            <div className="space-y-2">
              <p className="text-sm font-semibold text-slate-900 flex items-center justify-center gap-1.5">
                <FileText className="h-4 w-4 text-slate-400" />
                {selectedFile.name}
              </p>
              <p className="text-xs text-slate-400">
                {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
              </p>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedFile(null);
                }}
                className="text-xs font-semibold text-red-500 hover:underline cursor-pointer"
              >
                Remove file (runs default candidates.jsonl)
              </button>
            </div>
          </div>
        ) : (
          <label
            htmlFor="jsonl-upload"
            onDragEnter={handleDrag}
            onDragOver={handleDrag}
            onDragLeave={handleDrag}
            onDrop={handleDrop}
            className={`flex flex-col items-center justify-center border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
              dragActive 
                ? "border-red-500 bg-red-50/10" 
                : "border-slate-200 hover:border-slate-300"
            }`}
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-50 border border-slate-200 text-slate-500 mb-3">
              <UploadCloud className="h-5 w-5" />
            </div>
            <div>
              <span className="text-xs font-semibold text-red-500 hover:text-red-600">
                Click to upload custom dataset
              </span>
              <span className="text-xs text-slate-500"> or drag and drop candidates.jsonl</span>
              <p className="mt-1 text-[11px] text-slate-400">
                Leave empty to run the pre-configured local dataset
              </p>
            </div>
          </label>
        )}
      </GlassCard>

      {/* Real-time Progress Section */}
      {running && (
        <div className="mb-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm overflow-hidden">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                <RefreshCw className="h-4 w-4 animate-spin text-red-500" />
                Pipeline Execution Progress
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                {progressStep || "Initializing..."}
              </p>
            </div>
            <span className="text-sm font-bold text-red-500">{progressPercent}%</span>
          </div>
          
          {/* Animated Custom Progress Bar */}
          <div className="w-full bg-slate-100 rounded-full h-2.5 mb-6 overflow-hidden relative">
            <div 
              className="bg-gradient-to-r from-red-500 via-orange-500 to-red-650 h-full rounded-full transition-all duration-300 ease-out"
              style={{ width: `${progressPercent}%` }}
            />
            <div className="absolute inset-0 bg-[linear-gradient(45deg,rgba(255,255,255,0.15)_25%,transparent_25%,transparent_50%,rgba(255,255,255,0.15)_50%,rgba(255,255,255,0.15)_75%,transparent_75%,transparent)] bg-[size:1rem_1rem] animate-stripes opacity-40 pointer-events-none" />
          </div>

          {/* Stepper Checklist */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3.5">
              <h4 className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Execution Stages</h4>
              <div className="space-y-3">
                {[
                  { key: "load_jd", label: "Load Job Description" },
                  { key: "load_cache", label: "Load Candidates Cache" },
                  { key: "load_vector_index", label: "Build/Load FAISS Index" },
                  { key: "semantic_retrieval", label: "FAISS Semantic Retrieval" },
                  { key: "feature_eng_and_ranking", label: "LTR Feature Eng & Ranking" },
                  { key: "write_csv", label: "Export submission CSV" },
                  { key: "validation", label: "Run Submission Validation" }
                ].map((stage, idx) => {
                  const isDone = isStageDone(stage.key);
                  const isActive = isStageActive(stage.key);

                  return (
                    <div key={idx} className="flex items-center gap-3 text-xs">
                      {isDone ? (
                        <CheckCircle2 className="h-4.5 w-4.5 text-emerald-500 shrink-0" />
                      ) : isActive ? (
                        <Loader2 className="h-4.5 w-4.5 text-red-500 animate-spin shrink-0" />
                      ) : (
                        <div className="h-4.5 w-4.5 rounded-full border border-slate-200 bg-slate-50 shrink-0 flex items-center justify-center text-[10px] font-semibold text-slate-400">
                          {idx + 1}
                        </div>
                      )}
                      <span className={`font-medium ${isDone ? "text-slate-500 line-through" : isActive ? "text-red-650 font-semibold" : "text-slate-400"}`}>
                        {stage.label}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Live Console Output */}
            <div className="flex flex-col bg-slate-950 rounded-xl p-4 font-mono text-[10px] text-emerald-400 h-64 border border-slate-800 shadow-inner">
              <div className="border-b border-slate-800 pb-2 mb-2 flex items-center justify-between text-slate-400 font-bold uppercase tracking-wider text-[9px]">
                <span>Logs Console</span>
                <span className="flex h-2 w-2 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
              </div>
              <div 
                id="logs-console"
                className="flex-1 overflow-y-auto space-y-1.5 scrollbar-thin scrollbar-thumb-slate-800"
              >
                {progressLogs.map((log, i) => (
                  <div key={i} className="flex items-start gap-2 leading-relaxed">
                    <span className="text-slate-600 shrink-0">&gt;</span>
                    <span>{log}</span>
                  </div>
                ))}
                {running && (
                  <div className="flex items-center gap-1.5 text-slate-500 animate-pulse">
                    <span>&gt;</span>
                    <span className="inline-block w-1.5 h-3 bg-emerald-400" />
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="mb-6 flex items-start gap-2.5 rounded-lg bg-red-50 p-4 border border-red-200 text-xs font-medium text-red-600">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Validation status badge */}
      {validation && (
        <div className={`mb-6 p-4 rounded-lg border ${validation.passed ? "border-emerald-200 bg-emerald-50 text-emerald-800" : "border-red-250 bg-red-50 text-red-800"}`}>
          <div className="flex items-start gap-3">
            <div className="mt-0.5 shrink-0">
              {validation.passed ? <CheckCircle2 className="h-5 w-5 text-emerald-600" /> : <ShieldAlert className="h-5 w-5 text-red-600" />}
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-semibold">
                Official Submission Validator: {validation.passed ? "PASSED" : "FAILED"}
              </h3>
              {validation.passed ? (
                <p className="text-xs text-emerald-700 leading-normal mt-1">
                  Submission CSV is structurally compliant. All 100 ranks are contiguous, scores are non-increasing, and candidate formats are correct. Ready to upload!
                </p>
              ) : (
                <div className="mt-2 space-y-1">
                  {validation.errors.map((err: string, i: number) => (
                    <p key={i} className="text-xs text-red-700 font-medium flex items-center gap-1.5">
                      <AlertCircle className="h-3.5 w-3.5" />
                      {err}
                    </p>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Timers & Processing Metrics */}
      {results && results.timers && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
            <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5 text-slate-400" />
              FAISS Retrieval
            </span>
            <p className="text-2xl font-bold text-slate-900 mt-1.5 tracking-tight">
              {results.timers.semantic_retrieval.toFixed(3)}s
            </p>
          </div>
          <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
            <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5 text-slate-400" />
              LTR Prediction
            </span>
            <p className="text-2xl font-bold text-slate-900 mt-1.5 tracking-tight">
              {results.timers.feature_eng_and_ranking.toFixed(3)}s
            </p>
          </div>
          <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
            <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider flex items-center gap-1.5">
              <FileText className="h-3.5 w-3.5 text-slate-400" />
              CSV Output
            </span>
            <p className="text-2xl font-bold text-slate-900 mt-1.5 tracking-tight">
              {results.timers.write_csv.toFixed(3)}s
            </p>
          </div>
          <div className="bg-white rounded-xl p-4 border border-red-100 shadow-sm bg-red-50/10">
            <span className="text-[10px] uppercase font-bold text-red-600 tracking-wider flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-red-500" />
              Total Runtime
            </span>
            <p className="text-2xl font-bold text-red-600 mt-1.5 tracking-tight">
              {results.total_runtime_seconds.toFixed(2)}s
            </p>
          </div>
        </div>
      )}

      {/* Analytics Visualization charts */}
      {results && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* LTR Feature Importances */}
          <GlassCard className="lg:col-span-2">
            <h3 className="text-sm font-semibold text-slate-900 mb-6 flex items-center gap-2">
              <BarChart2 className="h-4.5 w-4.5 text-red-500" />
              Learning-to-Rank Feature Importance (XGBoost/LightGBM)
            </h3>
            <div className="h-[260px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={featureImportanceData} layout="vertical" margin={{ left: 10, right: 10, top: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" horizontal={true} vertical={false} />
                  <XAxis type="number" stroke="#94A3B8" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis dataKey="feature" type="category" stroke="#64748B" fontSize={10} width={120} tickLine={false} axisLine={false} />
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
                  <Bar dataKey="importance" fill="#EF4444" name="Relative Weight (%)" radius={[0, 4, 4, 0]} barSize={16} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </GlassCard>

          {/* Risk Level Distribution */}
          <GlassCard className="lg:col-span-1">
            <h3 className="text-sm font-semibold text-slate-900 mb-6 flex items-center gap-2">
              <ShieldAlert className="h-4.5 w-4.5 text-red-500" />
              Trap & Risk Distribution
            </h3>
            <div className="h-[260px] flex items-center justify-center">
              {riskPieData.length === 0 ? (
                <span className="text-xs text-slate-400 italic">No distribution data available</span>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={riskPieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={70}
                      paddingAngle={4}
                      dataKey="value"
                      labelLine={false}
                      label={({ name, percent }) => percent > 0 ? `${name}: ${((percent || 0) * 100).toFixed(0)}%` : ""}
                    >
                      {riskPieData.map((_: any, index: number) => (
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
                    <Legend 
                      verticalAlign="bottom" 
                      height={36} 
                      iconType="circle" 
                      iconSize={8}
                      wrapperStyle={{ 
                        fontSize: '10px', 
                        fontFamily: 'Inter, sans-serif',
                        color: '#475569',
                        paddingTop: '10px'
                      }} 
                    />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>
          </GlassCard>
        </div>
      )}

      {/* Advanced Ingest filters Panel */}
      {results && results.results && (
        <GlassCard className="mb-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
            <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
              <Search className="h-4.5 w-4.5 text-red-500" />
              Candidate Discovery Search
            </h3>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-50 border border-slate-200 text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-all cursor-pointer"
            >
              <Filter className="h-3.5 w-3.5" />
              <span>Advanced Filters {showFilters ? "▲" : "▼"}</span>
            </button>
          </div>

          {/* Filters Fields */}
          {showFilters && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 border-b border-slate-100 pb-6 mb-6">
              <div>
                <label className="block text-[11px] font-semibold text-slate-500 mb-1.5">Target Title</label>
                <input
                  type="text"
                  value={filterTitle}
                  onChange={(e) => setFilterTitle(e.target.value)}
                  placeholder="e.g. ML Engineer"
                  className="w-full h-9 rounded-lg border border-slate-200 bg-white px-3 text-xs outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500/20 text-slate-800 transition-all placeholder:text-slate-400"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-500 mb-1.5">Location / Match text</label>
                <input
                  type="text"
                  value={filterLocation}
                  onChange={(e) => setFilterLocation(e.target.value)}
                  placeholder="e.g. Noida, Seoul"
                  className="w-full h-9 rounded-lg border border-slate-200 bg-white px-3 text-xs outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500/20 text-slate-800 transition-all placeholder:text-slate-400"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-500 mb-1.5">Trap Risk Threshold</label>
                <select
                  value={filterRisk}
                  onChange={(e) => setFilterRisk(e.target.value)}
                  className="w-full h-9 rounded-lg border border-slate-200 bg-white px-3 text-xs outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500/20 text-slate-800 transition-all cursor-pointer"
                >
                  <option value="all">All Profiles</option>
                  <option value="Low">Low Risk Only</option>
                  <option value="Medium">Medium Risk</option>
                  <option value="High">High Risk</option>
                </select>
              </div>
            </div>
          )}

          {/* Simple search filter */}
          <div className="relative">
            <span className="absolute inset-y-0 left-0 flex items-center pl-3.5 text-slate-400">
              <Search className="h-4 w-4" />
            </span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by keywords inside candidate profiles or reasoning logs..."
              className="w-full h-10 rounded-lg border border-slate-200 bg-white py-2 pl-10 pr-4 text-xs outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500/20 text-slate-800 transition-all placeholder:text-slate-400"
            />
          </div>
        </GlassCard>
      )}

      {/* Discovery Ranked Candidates List table */}
      {results && results.results && (
        <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden mb-8">
          <div className="border-b border-slate-100 px-6 py-4">
            <h3 className="text-sm font-semibold text-slate-900">
              Top 100 Selected Challenge Candidates
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Ranked candidates based on calculated match scores and trap risk signals.
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-600">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                  <th className="py-3 px-6 text-center w-16">Rank</th>
                  <th className="py-3 px-6 w-28">Candidate ID</th>
                  <th className="py-3 px-6 w-60">Candidate details</th>
                  <th className="py-3 px-6 text-center w-24">Score</th>
                  <th className="py-3 px-6 text-center w-28">Risk Level</th>
                  <th className="py-3 px-6">Match Reasoning</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {filteredCandidates.map((c: any, index: number) => {
                  const riskColors: Record<string, string> = {
                    "Low": "bg-emerald-50 text-emerald-700 border border-emerald-200/60",
                    "Medium": "bg-amber-50 text-amber-700 border border-amber-200/60",
                    "High": "bg-rose-50 text-rose-700 border border-rose-200/60"
                  };

                  return (
                    <tr key={c.candidate_id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="py-3.5 px-6 text-center font-bold text-slate-900">
                        {index + 1}
                      </td>
                      <td className="py-3.5 px-6 font-mono text-slate-500 text-[11px]">
                        {c.candidate_id}
                      </td>
                      <td className="py-3.5 px-6">
                        <span className="font-semibold text-slate-900 block text-xs">{c.name}</span>
                        <span className="text-[11px] text-slate-500 block mt-0.5">{c.title}</span>
                      </td>
                      <td className="py-3.5 px-6 text-center font-bold text-slate-900 text-xs">
                        {c.score.toFixed(4)}
                      </td>
                      <td className="py-3.5 px-6 text-center">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold tracking-wide inline-block ${riskColors[c.risk_level] || ""}`}>
                          {c.risk_level}
                        </span>
                      </td>
                      <td className="py-3.5 px-6 text-slate-500 leading-relaxed text-[11px]">
                        {c.explanation}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {filteredCandidates.length === 0 && (
            <div className="py-12 text-center text-slate-400 italic text-xs bg-white">
              No candidates match active filter search parameters.
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ChallengePanel;
