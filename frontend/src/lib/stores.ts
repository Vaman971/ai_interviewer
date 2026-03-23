/**
 * Zustand stores for global state management.
 */

import { create } from "zustand";

// ── Auth Store ───────────────────────────────────────────────────
interface AuthState {
  token: string | null;
  user: { id: string; email: string; full_name: string | null } | null;
  isAuthenticated: boolean;
  setAuth: (token: string, user: AuthState["user"]) => void;
  logout: () => void;
  hydrate: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,
  isAuthenticated: false,

  setAuth: (token, user) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("access_token", token);
      localStorage.setItem("user", JSON.stringify(user));
    }
    set({ token, user, isAuthenticated: true });
  },

  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
    }
    set({ token: null, user: null, isAuthenticated: false });
  },

  hydrate: () => {
    if (typeof window === "undefined") return;
    const token = localStorage.getItem("access_token");
    const userStr = localStorage.getItem("user");
    if (token && userStr) {
      try {
        const user = JSON.parse(userStr);
        set({ token, user, isAuthenticated: true });
      } catch {
        set({ token: null, user: null, isAuthenticated: false });
      }
    }
  },
}));

// ── Interview Store ──────────────────────────────────────────────
interface InterviewState {
  currentInterviewId: string | null;
  currentQuestionIndex: number;
  answers: { questionIndex: number; answer: string; timeTaken: number }[];
  isInterviewActive: boolean;
  setCurrentInterview: (id: string) => void;
  addAnswer: (questionIndex: number, answer: string, timeTaken: number) => void;
  setInterviewActive: (active: boolean) => void;
  resetInterview: () => void;
}

export const useInterviewStore = create<InterviewState>((set) => ({
  currentInterviewId: null,
  currentQuestionIndex: 0,
  answers: [],
  isInterviewActive: false,

  setCurrentInterview: (id) =>
    set({ currentInterviewId: id, currentQuestionIndex: 0, answers: [] }),

  addAnswer: (questionIndex, answer, timeTaken) =>
    set((state) => ({
      answers: [...state.answers, { questionIndex, answer, timeTaken }],
      currentQuestionIndex: questionIndex + 1,
    })),

  setInterviewActive: (active) => set({ isInterviewActive: active }),

  resetInterview: () =>
    set({
      currentInterviewId: null,
      currentQuestionIndex: 0,
      answers: [],
      isInterviewActive: false,
    }),
}));
