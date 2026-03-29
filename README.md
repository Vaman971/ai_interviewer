# AI Interviewer 

An intelligent, end-to-end human-like interview practice platform built with **Next.js 14**, **FastAPI**, **Groq/OpenAI**, and dynamic **Text-to-Speech Streaming**. This platform simulates real-life technical, behavioral, and system design interviews, complete with a beautifully animated voice visualizer, real-time code execution, and deep analytical feedback.

## 🚀 Features

### Core Experience
* **Dynamic Conversational Flow**: The AI analyzes your resume and Job Description, asking context-aware, follow-up questions based entirely on your answers.
* **Animated Voice Visualizer UI**: A highly polished, draggable Picture-in-Picture (PIP) widget that pulses symbiotically with the AI’s generative voice.
* **Integrated Code Editor**: A built-in Python 3 environment that lets you execute DSA and System Design solutions live during the interview while explaining your thought process via text or voice.
* **Advanced Speech-to-Text (STT)**: Use your microphone to answer questions just like a real interview, utilizing seamless browser MediaRecorder APIs streaming to deep transcription models.

### Post-Interview Analytics
* **Comprehensive Scoring**: Immediate 0-10 feedback generated per answer (Technical, Behavioral, Problem Solving).
* **Skill Gap Identification**: The LLM parses your overarching weaknesses and builds an interactive heatmap across multiple sessions to track your preparation progress.
* **Anti-Cheating Mechanisms**: Built-in tab-switch and focus-loss tracking to simulate true testing conditions.

---

## 🏗️ Architecture & Technology Stack

The platform is split into a heavily customized, responsive **Next.js frontend** and a highly concurrent **FastAPI backend**.

### 1. Frontend (Next.js 14 + React)
* **Framework**: Next.js 14 (App Router)
* **Styling**: Pure CSS (Glassmorphism, CSS Modules, modern floating layouts)
* **Animation**: Framer Motion (Driving the fluid UI, PIP widget dragging, and voice visualizer rings)
* **State Management**: Zustand (Authentication hydration)
* **Data Visualization**: Recharts (Analytics radar and bar charts)

#### How The Frontend Works End-to-End:
When an interview begins, the UI mounts an `InterviewRoomPage` which streams continuous structured data arrays from the Backend's LLM engine. The candidate can type or use their microphone (which captures an `audio/wav` Blob and posts it to the `/api/media/stt` endpoint). 
Upon submission, the frontend orchestrates a fluid timeline: it awaits the evaluation JSON, visually renders the feedback, silently fetches the *next* question, concatenates the feedback and the next question into one seamless string, and passes it to the `AudioStream` engine to trigger the glowing Voice Visualizer.

### 2. Backend (FastAPI + Python 3.11)
* **Core API**: FastAPI (with async Pydantic validation)
* **Database**: PostgreSQL (via SQLAlchemy ORM, managing User, Interview, and Document state)
* **LLM Engine**: Groq (`llama-3.3-70b-versatile`) or OpenAI (`gpt-4o`) accessed via a shared, extensible Agent architecture.
* **Vector Storage (RAG)**: Qdrant (for embedding resumes and JDs to build semantic interview contexts).
* **Caching/PubSub**: Redis (Session management and rate limiting).

#### How The Backend Works End-to-End:
The backend operates entirely asynchronously. When an answer is submitted to `/api/interviews/{id}/answer`, the `BaseAgent` kicks in. It retrieves the entire conversation memory history from PostgreSQL, packages it into a strict XML/JSON schema prompt, and asks the Groq/OpenAI inference endpoint to output a constrained JSON evaluation containing a `score`, `feedback`, and `encouragement`.
Simultaneously, an internal mechanism dictates if the interview has reached its limits. If not, it requests a procedurally generated `question_text` based directly on the candidate's last stated weaknesses or strengths. 

---

## 💻 Running the Project Locally

### Prerequisites
* **Python 3.11+**
* **Node.js 18+**
* At least one LLM Key (Groq or OpenAI)

### 1. Backend Setup
Navigate to the `/backend` directory:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```
Copy `.env.example` to `.env` and fill in your keys:
```env
DATABASE_URL=sqlite:///./sql_app.db
SECRET_KEY=your_super_secret_key
GROQ_API_KEY=gsk_your_key_here
LLM_BASE_URL=https://api.groq.com/openai/v1
```
Run the FastAPI development server:
```bash
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
Navigate to the `/frontend` directory:
```bash
cd frontend
npm install
```
Start the Next.js development server:
```bash
npm run dev
```

Visit `http://localhost:3000` to access the application.

---

## 📚 Detailed Documentation

* **[Backend Documentation (Sphinx)](./backend/docs/index.rst)**: Dive deep into the Python application structures, ORM models, Pydantic schemas, and LLM Agent design.
* **[Frontend Documentation](./frontend/docs/README.md)**: Explore the Next.js routing structure, Zustand state trees, Framer Motion UI components, and API integration hooks. 

---

## 🐳 Docker Deployment
The project includes a production-ready `docker-compose.yml` that seamlessly orchestrates the Next.js standalone server, the FastAPI python backend, and a Redis caching layer.

```bash
docker compose up --build -d
```

Once built, the AI Interviewer platform is instantly available at **http://localhost:3000** with the API running on **http://localhost:8000**. Kubernetes manifests (`/infra/k8s/`) are also provided for EKS/GKE cluster deployments.
