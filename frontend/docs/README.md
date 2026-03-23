# AI Interviewer - Frontend Architecture & Documentation

## Overview
The frontend is built using **Next.js 14**, utilizing the App Router architecture. It communicates asynchronously with the FastAPI backend to orchestrate human-like technical interviews, capturing voice (STT), rendering a glowing AI Visualizer, executing real-time code, and mapping comprehensive analytics.

## Technology Stack
- **Framework**: React 18, Next.js 14
- **State Management**: Zustand (`src/lib/stores.ts`)
- **API Client**: Native `fetch()` wrapper (`src/lib/api.ts`)
- **UI Animation**: Framer Motion
- **Charting Engine**: Recharts (for `/dashboard/analytics`)

---

## Component Architecture

### 1. `InterviewRoomPage` (`/src/app/interview/[id]/page.tsx`)
This is the heart of the application. It maintains the rapid WebSocket-style flow of an interview using HTTP requests.
- **Microphone Handling**: Exposes `MediaRecorder` APIs to chunk `audio/wav` blobs. Sends these blobs to `/api/media/stt` to extract accurate text responses from the candidate.
- **Continuous Conversational Pipeline**: 
  - Submits the recorded/typed candidate answer (`interviewApi.submitAnswer()`).
  - Renders the resulting scorecard object locally.
  - Generates the continuous conversational "Interviewer Response" by silently pre-fetching the Next Question.
  - Combines `feedbackText + nextQuestionText` into ONE string and sends it to `/api/media/tts` to prevent audio/voice overlap.
- **Audio Visualizer**: Maps the `isAudioPlaying` state to a Draggable Picture-In-Picture `<motion.div>` which visually pulses with the AI voice for maximum user engagement.
- **Anti-Cheat Monitoring**: `document.addEventListener("visibilitychange")` and `window.addEventListener("blur")` track tab-switching and secretly append warnings to the final answer submission payload.

### 2. `CodeEditor` (`/src/components/CodeEditor.tsx`)
A dynamic component wrapper around `@monaco-editor/react`. It is rendered absolutely via `next/dynamic { ssr: false }` to prevent hydration mismatches. It injects a Python 3 syntax highlighter and binds to `codeContent` state in the interview room.

### 3. `AnalyticsPage` (`/src/app/dashboard/analytics/page.tsx`)
Pulls the user's historical interview evaluations to create a progress heatmap. 
- **Skill Gap Parsing**: Robustly parses the `res.skill_gaps` JSON array from the backend (which is output structurally by the LLM) into text keys (e.g. `gap.skill || gap.topic`) to map occurrences in a visually distinct warning list.
- **Data Rendering**: Aggregates `technical`, `behavioral`, and `problem_solving` scores into a `RadarChart` (global averages) and `BarChart` (chronological progress).

---

## State Management (`useAuthStore`)
Zustand orchestrates the JWT authentication lifecycle:
```typescript
interface AuthState {
  token: string | null;
  user: User | null;
  login: (token: string, user: User) => void;
  logout: () => void;
  hydrate: () => void;
}
```
`hydrate()` safely maps `localStorage.getItem("access_token")` on the client side after the initial SSR tree mounts, keeping UI sync locked.

---

## API & Backend Integration (`lib/api.ts`)
Every function automatically injects the Bearer Token into headers. The core flow methods include:
- `create(jd_text, resume_text, personality)`: Triggers the backend RAG pipeline to generate a customized 5-question pool.
- `getNextQuestion(id)`: Retreives the current question index safely.
- `submitAnswer(id, idx, answer, time_taken, warnings)`: Pushes the candidate's exact dictation/code. Waits for the LLM to process the code syntax, accuracy, and communication tone before returning `AnswerEvaluation`. 

## Best Practices
- **No Native Modals**: Custom inline State variables (`confirmExit`) are used for destructive actions like quitting an interview to prevent browser-engine blocking inconsistencies.
- **Graceful Error Handling**: Global custom `react-hot-toast` displays specific API 400+ errors smoothly to the user right on top of the UI.
