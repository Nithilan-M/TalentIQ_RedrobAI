import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { UploadCloud, FileText, CheckCircle2, AlertCircle, ArrowRight, ShieldCheck } from "lucide-react";
import { apiService } from "../services/api";
import { GlassCard } from "../components/GlassCard";

export const JobUpload: React.FC = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successData, setSuccessData] = useState<any>(null);

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
    if (ext !== "pdf" && ext !== "docx" && ext !== "txt") {
      setError("Unsupported format. Please upload PDF, DOCX, or TXT.");
      return;
    }
    setFile(selectedFile);
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    
    try {
      const res = await apiService.uploadJobDescription(file);
      // Save JD ID as active
      localStorage.setItem("active_jd_id", String(res.id));
      setSuccessData(res);
    } catch (err: any) {
      setError(err.message || "Failed to process job description. Verify your API key configuration.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          Upload Job Description
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Upload a job spec file. Our AI Agent will extract core requirements, technologies, and experience parameters.
        </p>
      </div>

      {!successData ? (
        <GlassCard className="relative overflow-hidden p-0">
          <input
            type="file"
            id="file-upload"
            className="hidden"
            accept=".pdf,.docx,.txt"
            onChange={handleFileChange}
          />
          
          {file ? (
            <div
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              className={`flex flex-col items-center justify-center border-2 border-dashed rounded-xl p-8 text-center transition-all ${
                dragActive 
                  ? "border-red-500 bg-red-50/10" 
                  : "border-slate-200 hover:border-slate-300"
              }`}
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-50 border border-slate-200 text-slate-500 mb-3">
                <UploadCloud className="h-5 w-5" />
              </div>
              <div className="space-y-2">
                <p className="text-sm font-semibold text-slate-900 flex items-center justify-center gap-1.5">
                  <FileText className="h-4 w-4 text-slate-400" />
                  {file.name}
                </p>
                <p className="text-xs text-slate-400">
                  {(file.size / 1024).toFixed(1)} KB
                </p>
                <button
                  onClick={() => setFile(null)}
                  className="text-xs font-semibold text-red-500 hover:underline cursor-pointer"
                >
                  Remove file
                </button>
              </div>
            </div>
          ) : (
            <label
              htmlFor="file-upload"
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
                  Click to upload
                </span>
                <span className="text-xs text-slate-500"> or drag and drop</span>
                <p className="mt-1 text-[11px] text-slate-400">
                  Accepts PDF, Word, or plain text up to 10MB
                </p>
              </div>
            </label>
          )}

          {error && (
            <div className="m-4 flex items-start gap-2 rounded-lg bg-red-50 p-3 border border-red-200 text-xs font-medium text-red-600">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {file && (
            <div className="p-4 bg-slate-50 border-t border-slate-100 flex justify-end">
              <button
                onClick={handleUpload}
                disabled={loading}
                className="flex h-9 items-center space-x-1.5 rounded-lg bg-red-500 px-4 text-xs font-medium text-white shadow-sm hover:bg-red-600 disabled:opacity-50 cursor-pointer"
              >
                {loading ? (
                  <span>Extracting criteria...</span>
                ) : (
                  <>
                    <span>Extract Criteria</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </>
                )}
              </button>
            </div>
          )}
        </GlassCard>
      ) : (
        <div className="space-y-4">
          <div className="flex items-start gap-3 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-emerald-800">
            <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-semibold">
                Criteria Extracted Successfully!
              </h3>
              <p className="mt-1 text-xs text-emerald-700 leading-normal">
                We scanned "{successData.title}" and mapped <strong>{successData.skills_required.length} required skills</strong> and <strong>{successData.technologies.length} core technologies</strong>.
              </p>
            </div>
          </div>

          <GlassCard>
            <h3 className="text-base font-semibold mb-4 flex items-center gap-2 text-slate-900 border-b border-slate-200 pb-3">
              <ShieldCheck className="h-4.5 w-4.5 text-red-500" />
              Extracted Structured Criteria Summary
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-2">
                  Required Skills ({successData.skills_required.length})
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {successData.skills_required.length > 0 ? (
                    successData.skills_required.map((skill: string, i: number) => (
                      <span key={i} className="rounded-md border border-slate-200 bg-slate-50 px-2 py-0.5 text-xs font-medium text-slate-700">
                        {skill}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-slate-400 italic">None found</span>
                  )}
                </div>
              </div>

              <div>
                <h4 className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-2">
                  Frameworks & Tools ({successData.technologies.length})
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {successData.technologies.length > 0 ? (
                    successData.technologies.map((tech: string, i: number) => (
                      <span key={i} className="rounded-md border border-slate-200 bg-slate-50 px-2 py-0.5 text-xs font-medium text-slate-700">
                        {tech}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-slate-400 italic">None found</span>
                  )}
                </div>
              </div>
            </div>

            <div className="mt-8 flex justify-between border-t border-slate-200 pt-5">
              <button
                onClick={() => setSuccessData(null)}
                className="rounded-lg border border-slate-200 bg-white hover:bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700 cursor-pointer"
              >
                Upload another
              </button>
              <button
                onClick={() => navigate("/upload-resume")}
                className="flex items-center space-x-1.5 rounded-lg bg-red-500 px-3.5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-red-600 cursor-pointer"
              >
                <span>Parse Resumes for this Job</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </GlassCard>
        </div>
      )}
    </div>
  );
};

export default JobUpload;
