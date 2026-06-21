import React, { createContext, useContext, useState, useEffect } from "react";
import { apiService } from "../services/api";

interface ChallengeContextType {
  running: boolean;
  results: any;
  validation: any;
  error: string | null;
  selectedFile: File | null;
  setSelectedFile: (file: File | null) => void;
  progressPercent: number;
  progressStep: string;
  progressLogs: string[];
  runPipeline: () => Promise<void>;
  checkExistingSubmission: () => Promise<void>;
  setError: (err: string | null) => void;
}

const ChallengeContext = createContext<ChallengeContextType | undefined>(undefined);

export const ChallengeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [validation, setValidation] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [progressPercent, setProgressPercent] = useState(0);
  const [progressStep, setProgressStep] = useState("");
  const [progressLogs, setProgressLogs] = useState<string[]>([]);

  // Load any existing pipeline result on mount
  useEffect(() => {
    checkExistingSubmission();
  }, []);

  const checkExistingSubmission = async () => {
    try {
      const val = await apiService.validateChallengeSubmission();
      setValidation(val);
      const analytics = await apiService.getChallengeAnalytics();
      if (analytics.pipeline_executed) {
        setResults({
          validation_passed: val.passed,
          validation_errors: val.errors,
          validation_warnings: val.warnings,
          feature_importances: analytics.feature_importances,
          score_distribution: analytics.score_distribution
        });
      }
    } catch (err) {
      console.log("No previous submission compiled yet.");
    }
  };

  const runPipeline = async () => {
    if (running) return;
    setRunning(true);
    setError(null);
    setResults(null);
    setValidation(null);
    setProgressPercent(0);
    setProgressStep("Initializing connection...");
    setProgressLogs([]);
    
    try {
      await apiService.runChallengePipelineStream(
        selectedFile || undefined,
        (update) => {
          if (update.status === "processing") {
            setProgressPercent(update.progress);
            setProgressStep(update.message);
            setProgressLogs((prev) => [...prev, update.message]);
          } else if (update.status === "completed") {
            setProgressPercent(update.progress);
            setProgressStep(update.message);
            setProgressLogs((prev) => [...prev, update.message]);
            setResults(update.results);
            if (update.results && update.results.validation_passed !== undefined) {
              setValidation({
                passed: update.results.validation_passed,
                errors: update.results.validation_errors || [],
                warnings: update.results.validation_warnings || []
              });
            }
          } else if (update.status === "failed") {
            setError(update.message);
            setProgressStep("Failed");
            setProgressLogs((prev) => [...prev, `[ERROR] ${update.message}`]);
          }
        }
      );
    } catch (err: any) {
      setError(err.message || "Pipeline execution failed. Check file or backend log.");
      setProgressLogs((prev) => [...prev, `[ERROR] ${err.message || "Pipeline execution failed."}`]);
    } finally {
      setRunning(false);
    }
  };

  return (
    <ChallengeContext.Provider
      value={{
        running,
        results,
        validation,
        error,
        selectedFile,
        setSelectedFile,
        progressPercent,
        progressStep,
        progressLogs,
        runPipeline,
        checkExistingSubmission,
        setError,
      }}
    >
      {children}
    </ChallengeContext.Provider>
  );
};

export const useChallenge = () => {
  const context = useContext(ChallengeContext);
  if (!context) {
    throw new Error("useChallenge must be used within a ChallengeProvider");
  }
  return context;
};
