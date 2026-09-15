# FastAPI & SQLAlchemy — Interview-Ready Deep Dive (Part 2)

> [!NOTE]
> Continuation from Part 1. This covers Testing, CI/CD, Performance, API Design, and 40+ general backend/full-stack interview questions.

---

## Module 6 — Testing FastAPI + SQLAlchemy

### 6.1 Test Infrastructure (Your conftest.py)

**Q: How did you set up isolated, reproducible tests for an async FastAPI app?**

```python
# 1. In-memory SQLite engine (no disk, no cleanup)
_test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
_TestSessionLocal = async_sessionmaker(_test_engine, class_=AsyncSession,
                                       expire_on_commit=False)

# 2. Override the real DB dependency
app.dependency_overrides[get_db] = _override_get_db

# 3. Create/drop tables for EACH test (full isolation)
@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# 4. Force mock LLM responses (no OpenAI costs in CI)
get_settings().openai_api_key = ""
```

**Q: Why in-memory SQLite instead of a test PostgreSQL container?**
*"Speed — in-memory SQLite runs entirely in RAM with zero network I/O. For unit tests that validate business logic and route behavior, SQLite is sufficient. For integration tests that need Postgres-specific features (JSON operators, full-text search, CTEs), I'd spin up a Postgres container in CI using GitHub Actions service containers."*

### 6.2 The Async Test Client

**Q: How do you make HTTP requests in tests without running uvicorn?**

```python
@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)  # In-process ASGI transport
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
```

*"httpx's `ASGITransport` mounts the FastAPI app directly in-process. No TCP sockets, no ports, no server startup. Requests go through the full middleware stack and dependency injection chain but in microseconds."*

### 6.3 Auth Test Helper

**Q: How do you test authenticated endpoints?**

```python
@pytest_asyncio.fixture
async def auth_headers(client):
    # Register + login in one fixture
    await client.post("/api/auth/register", json={
        "email": "test@example.com", "password": "testpass123"
    })
    resp = await client.post("/api/auth/login", json={
        "email": "test@example.com", "password": "testpass123"
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# Usage in tests:
async def test_create_interview(client, auth_headers):
    resp = await client.post("/api/interviews", headers=auth_headers,
                             json={"interview_type": "technical"})
    assert resp.status_code == 201
```

### 6.4 Mocking External Services

**Q: How do you test the LLM agent pipeline without calling OpenAI?**

```python
from unittest.mock import AsyncMock, patch

@patch("agents.base_agent.AsyncOpenAI")
async def test_resume_analysis(mock_openai):
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value.choices = [
        AsyncMock(message=AsyncMock(content='{"skills": ["Python"]}'))
    ]
    mock_openai.return_value = mock_client
    
    result = await analyze_resume({"resume_text": "Python developer"})
    assert "Python" in result["resume_analysis"]["skills"]
```

**Q: What's the difference between `Mock`, `MagicMock`, and `AsyncMock`?**

| Type | Use case |
|---|---|
| `Mock` | Sync methods, simple attribute access |
| `MagicMock` | Sync + magic methods (`__len__`, `__iter__`) |
| `AsyncMock` | Async methods (`await mock.method()`) |

---

## Module 7 — CI/CD, Docker & Deployment

### 7.1 Your GitHub Actions Pipeline

**Q: Walk through your CI/CD pipeline.**

```mermaid
graph LR
    Push[Push to main] --> Test[test-backend job]
    PR[Pull Request] --> Test
    Test --> |pip install -e .[dev]| PyTest[pytest backend/tests/ -v]
    PyTest --> |Pass| Build[build-push-images job]
    Build --> ECR_BE[Push Backend Image to ECR]
    Build --> ECR_FE[Push Frontend Image to ECR]
    ECR_BE --> EKS[Deploy to EKS]
    ECR_FE --> EKS
```

**Key design decisions:**
- Tests run on every PR **and** push — catches regressions before merge
- Image build only triggers on `main` push (not PRs) — saves CI minutes
- Images tagged with `github.sha` for traceability + `latest` for convenience
- ECR repos are auto-created if they don't exist (idempotent)

### 7.2 Docker Multi-Service Architecture

**Q: Explain your docker-compose setup.**

```yaml
services:
  backend:    # FastAPI on port 8000
    depends_on: [redis]
    volumes:
      - db_data:/app          # Persist SQLite DB across restarts
      - ./uploads:/app/uploads # Bind mount for resume files
  frontend:   # Next.js on port 3000
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000  # Docker DNS
  redis:      # Redis 7 Alpine on port 6379
    volumes:
      - redis_data:/data      # Persist cache across restarts
```

**Q: Why does frontend reference `http://backend:8000` not `localhost`?**
*"Inside Docker Compose, containers communicate via Docker's internal DNS. The service name `backend` resolves to the container's IP. Using `localhost` would look for a service inside the frontend container itself."*

**Q: What's the difference between a bind mount and a named volume?**
- **Bind mount** (`./uploads:/app/uploads`): Maps a host directory into the container. Changes are visible on both sides. Used for development and file sharing.
- **Named volume** (`db_data:/app`): Docker-managed storage. Survives container recreation. Used for persistent data like databases.

---

## Module 8 — Performance & Optimization

### 8.1 The N+1 Query Problem

**Q: What is the N+1 problem and how do you prevent it?**

```python
# ❌ N+1: 1 query for users + N queries for each user's interviews
users = (await db.execute(select(User))).scalars().all()
for user in users:
    print(user.interviews)  # Each access = 1 SELECT query!

# ✅ Fix: Eager loading
users = (await db.execute(
    select(User).options(selectinload(User.interviews))
)).scalars().all()
# Now it's just 2 queries: 1 for users, 1 for ALL their interviews
```

| Strategy | SQL Generated | Best for |
|---|---|---|
| `selectinload` | `SELECT * FROM interviews WHERE user_id IN (...)` | Collections |
| `joinedload` | `LEFT JOIN interviews ON ...` | Single objects |
| `subqueryload` | Subquery per relationship | Complex joins |

### 8.2 Connection Pooling

**Q: How does SQLAlchemy manage database connections?**

```python
engine = create_async_engine(
    url,
    pool_size=5,        # Maintain 5 persistent connections
    max_overflow=10,     # Allow 10 extra under load (total: 15)
    pool_timeout=30,     # Wait 30s for a free connection before error
    pool_recycle=1800,   # Recycle connections every 30min (avoid stale)
    pool_pre_ping=True,  # Test connection health before use
)
```

**Q: What happens when all 15 connections are in use?**
*"The 16th request blocks for up to `pool_timeout` seconds. If no connection frees up, SQLAlchemy raises `TimeoutError`. In production, I'd monitor pool exhaustion via Prometheus and scale horizontally or increase `pool_size`."*

### 8.3 Async Concurrency Patterns

**Q: When should you use `await` vs `asyncio.gather` vs `BackgroundTasks`?**

```python
# Sequential (your current approach — simple, safe)
state = await analyze_resume(state)
state = await analyze_jd(state)

# Parallel (when steps are independent)
resume_result, jd_result = await asyncio.gather(
    analyze_resume(state),
    analyze_jd(state)
)

# Background (fire-and-forget, non-blocking)
from fastapi import BackgroundTasks
@router.post("/interviews/{id}/complete")
async def complete(id: str, bg: BackgroundTasks):
    bg.add_task(send_completion_email, user.email, result)
    return result  # Returns immediately
```

**Q: Your resume and JD analysis are independent. Why not parallelize them?**
*"Good catch — they could run in parallel since neither depends on the other. However, both make LLM API calls, and running them concurrently doubles the token consumption spike. With rate-limited APIs like Groq, sequential calls avoid hitting RPM limits. In a production environment with higher rate limits, I'd absolutely use `asyncio.gather`."*

### 8.4 Database Query Optimization

**Q: How would you optimize this query for millions of rows?**

```python
# Your current pagination query
select(Interview).where(Interview.user_id == user_id)
    .order_by(Interview.created_at.desc())
    .offset(skip).limit(limit)
```

**Optimizations:**
1. **Composite index**: `CREATE INDEX idx_user_created ON interviews(user_id, created_at DESC)`
2. **Keyset pagination** (for deep pages):
```python
# Instead of OFFSET (which scans skipped rows):
select(Interview).where(
    Interview.user_id == user_id,
    Interview.created_at < last_seen_timestamp  # Cursor-based
).order_by(Interview.created_at.desc()).limit(limit)
```
3. **Select only needed columns** to reduce data transfer:
```python
select(Interview.id, Interview.status, Interview.created_at)
    .where(Interview.user_id == user_id)
```

---

## Module 9 — REST API Design Best Practices

### 9.1 HTTP Status Codes

**Q: Which status codes do you use and why?**

| Code | Meaning | Your usage |
|---|---|---|
| `200` | OK | GET endpoints, login |
| `201` | Created | POST register, POST create interview |
| `204` | No Content | DELETE interview, POST logout |
| `400` | Bad Request | Missing resume/JD |
| `401` | Unauthorized | Invalid/expired/revoked JWT |
| `403` | Forbidden | Accessing another user's interview |
| `404` | Not Found | Interview/result doesn't exist |
| `409` | Conflict | Duplicate email on register |
| `413` | Payload Too Large | File exceeds 10MB |
| `422` | Unprocessable Entity | PDF extraction failure |
| `429` | Too Many Requests | Rate limit exceeded |

### 9.2 Pagination

**Q: Compare offset-based vs cursor-based pagination.**

| Aspect | Offset (yours) | Cursor-based |
|---|---|---|
| Implementation | `OFFSET skip LIMIT limit` | `WHERE created_at < cursor` |
| Deep pages | Slow (scans skipped rows) | Constant time |
| New inserts | Can cause duplicates/skips | Stable |
| Random access | ✅ Jump to page 50 | ❌ Must traverse sequentially |
| Best for | Admin dashboards | Infinite scroll feeds |

### 9.3 Idempotency

**Q: Is your `POST /register` idempotent? Should it be?**
*"No — calling it twice with the same email returns 409 on the second call, which is correct behavior. Registration is inherently non-idempotent. However, `PUT /users/{id}/role` IS idempotent — setting `is_admin=True` twice produces the same result. For payment-like endpoints, I'd add an `Idempotency-Key` header and store results in Redis."*

### 9.4 API Versioning

**Q: How would you version your API?**
*"URL prefix versioning: `/api/v1/interviews/`, `/api/v2/interviews/`. In FastAPI, this is just a router prefix change. I'd run both versions simultaneously during migration, with v1 marked deprecated via OpenAPI tags."*

### 9.5 OpenAPI / Swagger

**Q: How does FastAPI auto-generate API documentation?**
*"FastAPI reads type hints from route signatures, Pydantic schemas, and `response_model` to generate an OpenAPI 3.0 spec. It's served at `/docs` (Swagger UI) and `/redoc` (ReDoc). Every field constraint from Pydantic (`min_length`, `max_length`, `EmailStr`) appears in the schema. The `tags` parameter on routers groups endpoints logically."*

---

## Module 10 — General Backend & Full-Stack Rapid-Fire

### HTTP & Networking

**Q1: Difference between `PUT` and `PATCH`?**
- **PUT**: Replace the entire resource. Client sends the complete object.
- **PATCH**: Partial update. Client sends only changed fields.
- *"My `PUT /users/{id}/role` is technically a PATCH since it only modifies `is_admin`. I'd rename it to PATCH in a stricter API."*

**Q2: What is CORS and why is it needed?**
*"Cross-Origin Resource Sharing. Browsers block requests from `localhost:3000` (frontend) to `localhost:8000` (backend) by default as a security measure. CORS headers tell the browser which origins, methods, and headers are allowed. Without my CORSMiddleware, the frontend can't talk to the API."*

**Q3: Difference between cookies and JWT for auth?**

| Aspect | Cookies | JWT (yours) |
|---|---|---|
| Storage | Browser (httpOnly) | Client-side (localStorage/memory) |
| CSRF vulnerable | ✅ Yes | ❌ No |
| XSS vulnerable | ❌ (httpOnly) | ✅ (if in localStorage) |
| Stateless | ❌ (needs session store) | ✅ |
| Mobile support | Poor | Excellent |

**Q4: What happens when you type a URL in the browser?**
DNS lookup → TCP handshake → TLS handshake → HTTP request → Server processing → HTTP response → Browser rendering → DOM construction → CSS parsing → JS execution.

### Database Fundamentals

**Q5: ACID properties — explain each.**
- **Atomicity**: Transaction is all-or-nothing (your `rollback()` on error)
- **Consistency**: DB moves from one valid state to another (constraints enforced)
- **Isolation**: Concurrent transactions don't interfere (see isolation levels)
- **Durability**: Committed data survives crashes (WAL in PostgreSQL)

**Q6: SQL vs NoSQL — when to use which?**

| Use case | SQL (PostgreSQL) | NoSQL (MongoDB) |
|---|---|---|
| Your users/interviews | ✅ Relational, ACID | Overkill |
| Chat transcripts | Possible but rigid | ✅ Flexible schema |
| Session analytics | ✅ Complex aggregations | ✅ Time-series collections |
| Full-text search | ✅ (tsvector) | ✅ (Atlas Search) |

**Q7: What is an index? When NOT to use one?**
*"An index is a B-Tree (or Hash/GIN/GiST) data structure that speeds up lookups from O(n) to O(log n). Don't add indexes on: columns with low cardinality (boolean), tables with frequent writes (each INSERT updates the index), or columns you never filter/sort on."*

**Q8: Write a CTE to find each user's latest interview score.**
```sql
WITH LatestInterviews AS (
    SELECT i.user_id, i.id as interview_id,
           ROW_NUMBER() OVER (
               PARTITION BY i.user_id 
               ORDER BY i.created_at DESC
           ) as rn
    FROM interviews i
    WHERE i.status = 'scored'
)
SELECT li.user_id, u.email, r.overall_score
FROM LatestInterviews li
JOIN users u ON u.id = li.user_id
JOIN results r ON r.interview_id = li.interview_id
WHERE li.rn = 1
ORDER BY r.overall_score DESC;
```

### Python & Concurrency

**Q9: What is the GIL? How does async bypass it?**
*"The GIL (Global Interpreter Lock) prevents multiple threads from executing Python bytecode simultaneously. Async doesn't bypass it — it uses cooperative multitasking on a single thread. When one coroutine awaits I/O (network, DB), the event loop switches to another coroutine. This is ideal for I/O-bound work (my LLM calls, DB queries) but NOT for CPU-bound work."*

**Q10: `async def` vs `def` in FastAPI route handlers?**
- `async def`: Runs on the event loop. Use for I/O-bound handlers.
- `def`: FastAPI runs it in a **threadpool** automatically. Use for sync/CPU-bound code.
- *"All my handlers are `async def` because they call async DB sessions and async HTTP clients."*

**Q11: What are context managers? Why `async with`?**
```python
# Sync context manager
with open("file.txt") as f:
    data = f.read()

# Async context manager (your DB session)
async with async_session() as session:
    # session is open here
    yield session
# session is automatically closed here
```

### System Design

**Q12: Design a URL shortener.**
1. **API**: `POST /shorten {url}` → `{short_url}`, `GET /{code}` → 301 redirect
2. **Storage**: PostgreSQL with `(code VARCHAR(7) PK, original_url TEXT, created_at)`
3. **Code generation**: Base62 encode an auto-increment ID or use first 7 chars of MD5
4. **Caching**: Redis `GET short:{code}` → original_url (99% reads)
5. **Scale**: Read replicas, CDN for redirects, rate limit creation

**Q13: How would you design a real-time notification system?**
1. **Publish**: Backend publishes events to Redis Pub/Sub or Kafka
2. **Deliver**: WebSocket server subscribes and pushes to connected clients
3. **Fallback**: Store undelivered notifications in DB, deliver on next connection
4. **Scale**: Use Redis Streams for persistence + fan-out across pods

**Q14: Explain the CAP theorem.**
- **Consistency**: Every read returns the latest write
- **Availability**: Every request gets a response
- **Partition tolerance**: System works despite network splits
- *"You can only guarantee 2 of 3. PostgreSQL is CP (consistent + partition tolerant). Cassandra is AP (available + partition tolerant). My app prioritizes CP because interview scores must be consistent."*

### Security

**Q15: What is SQL injection? How does SQLAlchemy prevent it?**
*"SQL injection happens when user input is concatenated into SQL strings. SQLAlchemy uses parameterized queries — `WHERE User.email == data.email` generates `WHERE email = $1` with the value bound separately. The DB driver escapes it, making injection impossible."*

**Q16: How do you store passwords securely?**
*"I use bcrypt via Passlib. Bcrypt is a deliberately slow adaptive hash with a built-in salt. The work factor makes brute-force infeasible. I never store plain-text passwords. The hash includes the salt, so I don't need a separate salt column."*

**Q17: What is HTTPS and why is it important?**
*"HTTPS = HTTP + TLS encryption. It encrypts data in transit, preventing eavesdropping on JWTs, passwords, and interview data. In production, my EKS ingress terminates TLS using an ACM certificate. Without HTTPS, Bearer tokens could be intercepted via MITM attacks."*

### DevOps & Infrastructure

**Q18: Docker — what's the difference between an image and a container?**
- **Image**: A read-only template (blueprint). Built from a Dockerfile.
- **Container**: A running instance of an image with its own writable layer.
- *"Think of an image as a class and a container as an object."*

**Q19: Explain Kubernetes concepts relevant to your deployment.**

| Concept | Your usage |
|---|---|
| **Pod** | Smallest unit — runs one container (FastAPI or Next.js) |
| **Deployment** | Manages pod replicas, rolling updates |
| **Service** | Stable DNS + load balancing across pods |
| **Ingress** | External HTTPS entry point (ALB) |
| **ConfigMap/Secret** | Inject env vars (API keys, DB URLs) |
| **HPA** | Auto-scale pods based on CPU/memory |

**Q20: Explain the difference between horizontal and vertical scaling.**
- **Vertical**: Bigger machine (more CPU/RAM). Simple but has limits.
- **Horizontal**: More machines/pods. My EKS setup scales FastAPI pods horizontally via HPA.
- *"Horizontal scaling requires stateless services. My FastAPI backend is stateless — session state lives in Redis and PostgreSQL, not in-memory. That's why I can scale to N pods."*

---

## Bonus — Questions They WILL Ask About Your Project

**Q: Why did you store JSON as Text columns instead of using PostgreSQL's JSONB type?**
*"For SQLite compatibility during development. SQLite doesn't have a native JSON type. In production PostgreSQL, I'd migrate to `JSONB` columns to enable JSON path queries, indexing on nested fields, and `@>` containment operators. With Alembic, this is a single migration: `op.alter_column('interviews', 'questions', type_=JSONB)`."*

**Q: Your `_get_user_interview` does 2 checks (exists + ownership). Can this be one query?**
*"Yes — I could combine them: `select(Interview).where(Interview.id == id, Interview.user_id == user_id)`. If it returns None, I'd return 404 (hiding the existence of other users' interviews for security). I separated them to give different error messages (404 vs 403), which is more debuggable."*

**Q: What would you change if you were to rebuild this from scratch?**
*"Three things: (1) Use PostgreSQL JSONB from day one instead of JSON-as-Text. (2) Add OpenTelemetry tracing to every agent node for end-to-end latency visibility. (3) Use Server-Sent Events instead of polling for the interview progress status updates — SSE is simpler than WebSockets for one-directional streaming."*

---

> [!IMPORTANT]
> **Study order**: Read Part 1 first (Modules 1-5), then this Part 2 (Modules 6-10). For the interview, focus on Modules 1, 2, 3, 8, and the Bonus section — these are the highest-probability question areas for an LG Soft Research Engineer role.
