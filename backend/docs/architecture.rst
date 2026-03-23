Architecture Overview
=====================

The AI Interviewer backend is built on **FastAPI** to handle high-concurrency websocket and HTTP requests.

Core Components
---------------
1. **API Layer (`app/api/endpoints`)**: Houses all FastAPI route definitions. Uses Pydantic for rigorous schema validation.
2. **Services Layer (`app/services`)**: Business logic lives here. Includes:
   - `LLMEvaluator`: Connects to Groq/OpenAI. Extracts structural interview rubrics.
   - `STTService` / `TTSService`: Transcribes microphone audio and synthesizes interviewer voice.
   - `CodeExecutor`: Safely compiles Python execution rounds.
3. **Data Layer (`app/models` & `app/schemas`)**: SQLAlchemy models mapping to PostgreSQL tables.

Dependency Injection
--------------------
FastAPI `Depends()` is used extensively to inject the current DB session (`get_db`) and the active authenticated user (`get_current_user`).
