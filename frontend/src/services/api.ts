import { authService } from "./auth";

const BASE_URL = "http://127.0.0.1:8000/api";

async function request(endpoint: string, options: RequestInit = {}) {
  const token = authService.getToken();
  const headers = new Headers(options.headers || {});
  
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  // Set default Content-Type to JSON unless sending FormData (for files)
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    authService.logout();
    window.location.href = "/login";
    throw new Error("Session expired. Please log in again.");
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Request failed with status ${response.status}`);
  }

  // Handle file streaming downloads vs JSON
  const contentType = response.headers.get("content-type");
  if (contentType && (contentType.includes("application/pdf") || contentType.includes("text/csv"))) {
    return response.blob();
  }

  return response.json();
}

export const apiService = {
  // Job Descriptions
  async uploadJobDescription(file: File) {
    const formData = new FormData();
    formData.append("file", file);
    return request("/job-description/upload", {
      method: "POST",
      body: formData,
    });
  },

  async getLatestJobDescription() {
    return request("/job-description/latest");
  },

  async listJobDescriptions() {
    return request("/job-description/list");
  },

  async getJobDescriptionDetails(id: number) {
    return request(`/job-description/${id}`);
  },

  // Resumes / Candidates
  async uploadResumes(jobDescriptionId: number, files: File[]) {
    const formData = new FormData();
    formData.append("job_description_id", String(jobDescriptionId));
    files.forEach((file) => {
      formData.append("files", file);
    });
    return request("/resume/upload-resumes", {
      method: "POST",
      body: formData,
    });
  },

  async listCandidates(jobDescriptionId: number, query?: string) {
    const url = `/candidate/list?job_description_id=${jobDescriptionId}${
      query ? `&query=${encodeURIComponent(query)}` : ""
    }`;
    return request(url);
  },

  async getCandidateDetails(id: number) {
    return request(`/candidate/${id}`);
  },

  async compareCandidates(candidateIds: number[]) {
    return request("/candidate/compare", {
      method: "POST",
      body: JSON.stringify({ candidate_ids: candidateIds }),
    });
  },

  async regenerateInterviewQuestions(candidateId: number) {
    return request(`/candidate/${candidateId}/regenerate-interview`, {
      method: "POST",
    });
  },

  // Analytics
  async getAnalytics(jobDescriptionId: number) {
    return request(`/analytics/?job_description_id=${jobDescriptionId}`);
  },

  // Reports Exports (returns blob)
  async exportCandidatesCSV(jobDescriptionId: number) {
    return request(`/export/csv?job_description_id=${jobDescriptionId}`);
  },

  async exportCandidatePDF(candidateId: number) {
    return request(`/export/pdf?candidate_id=${candidateId}`);
  },

  // Redrob Challenge API methods
  async runChallengePipeline(file?: File) {
    if (file) {
      const formData = new FormData();
      formData.append("file", file);
      return request("/challenge/run", {
        method: "POST",
        body: formData,
      });
    }
    return request("/challenge/run", { method: "POST" });
  },

  async getChallengeJD() {
    return request("/challenge/jd");
  },

  async validateChallengeSubmission() {
    return request("/challenge/validate");
  },

  async getChallengeAnalytics() {
    return request("/challenge/analytics");
  }
};

