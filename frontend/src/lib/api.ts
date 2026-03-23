/**
 * API client for the AI Interviewer backend.
 * Wraps fetch with auth headers and error handling.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function getAuthHeaders(): HeadersInit {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_URL}${endpoint}`;
  const headers: HeadersInit = {
    ...getAuthHeaders(),
    ...(options.headers || {}),
  };

  // Don't set Content-Type for FormData (browser handles it)
  if (!(options.body instanceof FormData)) {
    (headers as Record<string, string>)["Content-Type"] = "application/json";
  }

  const response = await fetch(url, { ...options, headers });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw new ApiError(
      errorBody.detail || `Request failed with status ${response.status}`,
      response.status
    );
  }

  return response.json();
}

// ── Auth ──────────────────────────────────────────────────────────
export const authApi = {
  register: (email: string, password: string, fullName?: string) =>
    request<{ id: string; email: string }>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name: fullName }),
    }),

  login: (email: string, password: string) =>
    request<{ access_token: string; token_type: string }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  getMe: () =>
    request<{
      id: string;
      email: string;
      full_name: string | null;
      is_active: boolean;
      created_at: string;
    }>("/api/auth/me"),
};

// ── Interviews ───────────────────────────────────────────────────
export interface Interview {
  id: string;
  user_id: string;
  jd_text: string | null;
  resume_filename: string | null;
  status: string;
  interview_type: string;
  personality_mode: string;
  difficulty_level: string;
  current_question_index: number;
  created_at: string;
  updated_at: string;
}

export interface Question {
  question_index: number;
  question_text: string;
  question_type: string;
  difficulty: string;
  total_questions: number;
}

export interface AnswerEvaluation {
  question_index: number;
  score: number;
  feedback: string;
  follow_up: string | null;
  encouragement?: string;
}

export interface InterviewResult {
  id: string;
  interview_id: string;
  overall_score: number | null;
  technical_score: number | null;
  behavioral_score: number | null;
  communication_score: number | null;
  problem_solving_score: number | null;
  feedback: string | null;
  skill_gaps: string | null;
  improvement_plan: string | null;
  strengths: string | null;
  weaknesses: string | null;
  total_questions: number | null;
  questions_answered: number | null;
  created_at: string;
}

export const interviewApi = {
  create: (data: {
    jd_text?: string;
    interview_type?: string;
    personality_mode?: string;
    difficulty_level?: string;
  }) =>
    request<Interview>("/api/interviews/", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  list: (skip = 0, limit = 20) =>
    request<{ interviews: Interview[]; total: number }>(
      `/api/interviews/?skip=${skip}&limit=${limit}`
    ),

  get: (id: string) => request<Interview>(`/api/interviews/${id}`),

  uploadResume: (interviewId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<Interview>(
      `/api/interviews/${interviewId}/upload-resume`,
      { method: "POST", body: formData }
    );
  },

  uploadJD: (interviewId: string, jdText?: string, file?: File) => {
    const formData = new FormData();
    if (file) formData.append("file", file);
    if (jdText) formData.append("jd_text", jdText);
    return request<Interview>(
      `/api/interviews/${interviewId}/upload-jd`,
      { method: "POST", body: formData }
    );
  },

  start: (interviewId: string) =>
    request<Interview>(`/api/interviews/${interviewId}/start`, {
      method: "POST",
    }),

  getNextQuestion: (interviewId: string) =>
    request<Question>(`/api/interviews/${interviewId}/next-question`),

  submitAnswer: (
    interviewId: string,
    questionIndex: number,
    answerText: string,
    timeTakenSeconds?: number,
    warnings?: string[]
  ) =>
    request<AnswerEvaluation>(`/api/interviews/${interviewId}/submit-answer`, {
      method: "POST",
      body: JSON.stringify({
        question_index: questionIndex,
        answer_text: answerText,
        time_taken_seconds: timeTakenSeconds,
        warnings: warnings || [],
      }),
    }),

  complete: (interviewId: string) =>
    request<InterviewResult>(`/api/interviews/${interviewId}/complete`, {
      method: "POST",
    }),

  getResults: (interviewId: string) =>
    request<InterviewResult>(`/api/interviews/${interviewId}/results`),

  delete: (interviewId: string) =>
    request<void>(`/api/interviews/${interviewId}`, {
      method: "DELETE",
    }),
};

export const executionApi = {
  executeCode: (language: string, code: string, version: string = "*") =>
    request<{
      stdout: string;
      stderr: string;
      compile_output: string | null;
      language: string;
      version: string;
    }>("/api/execute", {
      method: "POST",
      body: JSON.stringify({ language, code, version }),
    }),
};
