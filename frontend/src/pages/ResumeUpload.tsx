import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { UploadCloud, FileText, AlertCircle, Play, Sparkles, ChevronRight, Eye } from "lucide-react";
import { apiService } from "../services/api";
import { GlassCard } from "../components/GlassCard";

interface UploadingFile {
  file: File;
  status: "queued" | "extracting" | "grading" | "completed" | "failed";
  error?: string;
  candidateId?: number;
  overallScore?: number;
  decision?: string;
}

export const ResumeUpload: React.FC = () => {
  const navigate = useNavigate();
  const [activeJdId, setActiveJdId] = useState<number | null>(null);
  const [activeJdTitle, setActiveJdTitle] = useState<string>("");
  const [files, setFiles] = useState<UploadingFile[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [globalError, setGlobalError] = useState<string | null>(null);

  useEffect(() => {
    loadActiveJd();
  }, []);

  const loadActiveJd = async () => {
    const savedJdId = localStorage.getItem("active_jd_id");
    if (!savedJdId) {
      setGlobalError("No active Job Description selected. Please upload a Job Description first.");
      return;
    }

    try {
      const details = await apiService.getJobDescriptionDetails(Number(savedJdId));
      setActiveJdId(details.id);
      setActiveJdTitle(details.title);
    } catch (err) {
      setGlobalError("Failed to fetch active Job Description. Try uploading a new one.");
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
    
    if (e.dataTransfer.files) {
      addFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      addFiles(Array.from(e.target.files));
    }
  };

  const addFiles = (selectedFiles: File[]) => {
    const newFiles: UploadingFile[] = selectedFiles
      .filter((file) => {
        const ext = file.name.split(".").pop()?.toLowerCase();
        return ext === "pdf" || ext === "docx" || ext === "txt";
      })
      .map((file) => ({
        file,
        status: "queued"
      }));
    
    if (newFiles.length === 0) {
      setGlobalError("Only PDF, DOCX, and TXT files are accepted.");
      return;
    }

    setFiles((prev) => [...prev, ...newFiles]);
  };

  const handleStartProcessing = async () => {
    if (!activeJdId || files.length === 0) return;
    setProcessing(true);
    setGlobalError(null);

    // We process sequentially or in batch to show live extraction & debate progress state changes!
    // Since our backend accepts a list of files, we can upload them in batches, or we can send files one-by-one to provide granular UI loading feedback!
    // Uploading one-by-one is MUCH better for UX as it shows individual progress bars for each candidate!
    for (let i = 0; i < files.length; i++) {
      if (files[i].status === "completed") continue;
      
      // Update status to extracting text
      updateFileStatus(i, { status: "extracting" });

      try {
        // Mock a slight stage transition for user visual cue
        updateFileStatus(i, { status: "grading" });
        
        // Post file to backend
        const result = await apiService.uploadResumes(activeJdId, [files[i].file]);
        
        if (result.successful && result.successful.length > 0) {
          const info = result.successful[0];
          updateFileStatus(i, {
            status: "completed",
            candidateId: info.candidate_id,
            overallScore: info.overall_score,
            decision: info.decision
          });
        } else {
          const errorMsg = result.failed && result.failed.length > 0 ? result.failed[0].error : "Parsing failure";
          updateFileStatus(i, { status: "failed", error: errorMsg });
        }
      } catch (err: any) {
        updateFileStatus(i, { status: "failed", error: err.message || "Failed to contact backend." });
      }
    }
    
    setProcessing(false);
  };

  const updateFileStatus = (index: number, updates: Partial<UploadingFile>) => {
    setFiles((prev) => {
      const copy = [...prev];
      copy[index] = { ...copy[index], ...updates };
      return copy;
    });
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Candidate Resume Upload
          </h1>
          {activeJdTitle && (
            <p className="mt-1 text-sm text-slate-500">
              Evaluating candidates against: <strong className="text-red-500 font-semibold">{activeJdTitle}</strong>
            </p>
          )}
        </div>
        
        {files.length > 0 && !processing && (
          <button
            onClick={handleStartProcessing}
            className="flex items-center space-x-1.5 rounded-lg bg-red-500 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-red-600 cursor-pointer transition-all"
          >
            <Play className="h-4 w-4" />
            <span>Start Committee Evaluation</span>
          </button>
        )}
      </div>

      {globalError && (
        <div className="mb-6 flex items-start gap-2.5 rounded-lg bg-red-50 p-4 border border-red-200 text-xs font-medium text-red-600">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{globalError}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Container */}
        <div className="lg:col-span-1 space-y-4">
          <GlassCard
            onDragEnter={handleDrag}
            onDragOver={handleDrag}
            onDragLeave={handleDrag}
            onDrop={handleDrop}
            className={`border-2 border-dashed p-0 text-center transition-all ${
              dragActive 
                ? "border-red-500 bg-red-50/10" 
                : "border-slate-200 hover:border-slate-300"
            }`}
          >
            <input
              type="file"
              id="resume-upload"
              multiple
              className="hidden"
              accept=".pdf,.docx,.txt"
              onChange={handleFileChange}
            />
            
            <label
              htmlFor="resume-upload"
              className="flex flex-col items-center justify-center p-8 cursor-pointer w-full h-full"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-50 border border-slate-200 text-slate-500 mb-3">
                <UploadCloud className="h-5 w-5" />
              </div>
              <span className="text-xs font-semibold text-red-500 hover:text-red-600">
                Select resume files
              </span>
              <p className="text-[11px] text-slate-400 mt-1">
                Supports multiple PDF, DOCX, or TXT
              </p>
            </label>
          </GlassCard>

          <GlassCard className="p-5 border-slate-200 bg-white shadow-sm">
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5 mb-3">
              <Sparkles className="h-4 w-4 text-red-500" />
              AI Committee Steps
            </h4>
            <ul className="space-y-3 text-xs text-slate-600">
              <li className="flex items-center gap-2">
                <ChevronRight className="h-3 w-3 text-red-500 shrink-0" />
                <span>Extract clean text from documents.</span>
              </li>
              <li className="flex items-center gap-2">
                <ChevronRight className="h-3 w-3 text-red-500 shrink-0" />
                <span>AI structuring of experiences & projects.</span>
              </li>
              <li className="flex items-center gap-2">
                <ChevronRight className="h-3 w-3 text-red-500 shrink-0" />
                <span>Advocate vs. Skeptic committee debate.</span>
              </li>
              <li className="flex items-center gap-2">
                <ChevronRight className="h-3 w-3 text-red-500 shrink-0" />
                <span>Verdict consensus & interview guides.</span>
              </li>
            </ul>
          </GlassCard>
        </div>

        {/* Upload List & Progress */}
        <div className="lg:col-span-2">
          <GlassCard className="min-h-[300px] p-0 overflow-hidden">
            <div className="border-b border-slate-200 px-6 py-4">
              <h3 className="text-sm font-semibold text-slate-900">
                Uploads Queue ({files.length})
              </h3>
            </div>

            {files.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 text-slate-400">
                <FileText className="h-10 w-10 text-slate-200 mb-2" />
                <p className="text-xs">Queue is empty. Select files to load candidates.</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-100 px-6">
                {files.map((f, idx) => (
                  <div key={idx} className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 first:pt-4 last:pb-4">
                    <div className="flex items-center gap-3">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-50 border border-slate-200 text-slate-400">
                        <FileText className="h-4.5 w-4.5" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-semibold truncate max-w-[250px] text-slate-800">
                          {f.file.name}
                        </p>
                        <p className="text-xs text-slate-400 mt-0.5">
                          {(f.file.size / 1024).toFixed(1)} KB
                        </p>
                      </div>
                    </div>

                    {/* Progress States */}
                    <div className="flex items-center gap-4">
                      {f.status === "queued" && (
                        <span className="rounded-md border border-slate-200 bg-slate-50 px-2 py-0.5 text-xs font-medium text-slate-500">
                          Queued
                        </span>
                      )}
                      
                      {f.status === "extracting" && (
                        <span className="flex items-center gap-1.5 text-xs font-semibold text-blue-600">
                          <span className="h-1.5 w-1.5 rounded-full bg-blue-600 animate-ping" />
                          Extracting text...
                        </span>
                      )}

                      {f.status === "grading" && (
                        <span className="flex items-center gap-1.5 text-xs font-semibold text-amber-600">
                          <span className="h-1.5 w-1.5 rounded-full bg-amber-500 animate-ping" />
                          AI Committee Debating...
                        </span>
                      )}

                      {f.status === "completed" && (
                        <div className="flex items-center gap-2.5">
                          <div className="text-right">
                            <span className="text-xs font-medium px-2 py-0.5 rounded border border-emerald-200 bg-emerald-50 text-emerald-700">
                              {f.decision}
                            </span>
                            <span className="text-xs font-bold text-slate-700 ml-2">
                              {f.overallScore}% Match
                            </span>
                          </div>
                          <button
                            onClick={() => navigate(`/candidate/${f.candidateId}`)}
                            className="flex h-7 w-7 items-center justify-center rounded-md border border-slate-200 bg-white text-slate-400 hover:text-slate-600 transition-colors"
                          >
                            <Eye className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      )}

                      {f.status === "failed" && (
                        <div className="flex items-center gap-2">
                          <span className="rounded-md border border-red-200 bg-red-50 px-2 py-0.5 text-xs font-semibold text-red-600 flex items-center gap-1">
                            <AlertCircle className="h-3.5 w-3.5" />
                            Failed
                          </span>
                        </div>
                      )}

                      {!processing && f.status === "queued" && (
                        <button
                          onClick={() => removeFile(idx)}
                          className="text-xs text-red-500 font-semibold hover:underline cursor-pointer"
                        >
                          Remove
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </GlassCard>
        </div>
      </div>
    </div>
  );
};

export default ResumeUpload;
