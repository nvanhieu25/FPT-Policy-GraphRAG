# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**FPT Policy GraphRAG** is a hybrid retrieval-augmented generation system for internal policy compliance assistance at FPT Software. It combines:
- **Vector search** (Qdrant) for semantic similarity
- **Graph search** (Neo4j) for relationship-based queries
- **Hybrid routing** to intelligently choose or combine both search modes
- **LangGraph orchestration** for multi-step agentic workflows
- **JWT authentication** for user identity and session scoping
- **LLM-based reranking** via OpenAI API (no local model required)
- **Redis RAG cache** to skip retrieval for repeated queries (1h TTL)

The system includes a FastAPI backend, React frontend, and four database services (PostgreSQL, Neo4j, Qdrant, Redis).

---

## Architecture

### Backend Stack
- **FastAPI** (uvicorn) — HTTP API server on port 8000
- **LangChain / LangGraph** — LLM orchestration and agentic workflows
- **PostgreSQL** — Persistent conversation and user storage (port 5432, exposed on 5433)
- **Neo4j** — Graph database for relational policy data (port 7687)
- **Qdrant** — Vector database for semantic search (port 6333)
- **Redis** — Cache for conversation history (24h TTL) and RAG query results (1h TTL)

### Frontend Stack
- **React 18** with TypeScript
- **Vite** for bundling and HMR
- **React Markdown** for policy rendering
- **JWT token** stored in `localStorage`, sent as `Authorization: Bearer` header

---

## Key Layers

1. **Ingestion Pipeline** (`src/ingestion/`)
   - Extracts policies from documents (PDF via PyMUPDF)
   - Chunks content and creates embeddings
   - Populates Neo4j and Qdrant

2. **LangGraph Workflow** (`app/services/ai_service.py`, `app/services/nodes/`)
   - Router node decides between vector/graph/hybrid search
   - Qdrant and Neo4j search nodes execute retrieval in parallel via LangGraph branching
   - LLM-based reranker scores and selects top-k combined results
   - Synthesizer aggregates results
   - Generator produces final answers

3. **FastAPI Routes** (`app/api/routes/`)
   - `POST /api/v1/auth/register` — Register new user
   - `POST /api/v1/auth/token` — Login, returns JWT access token
   - `GET  /api/v1/auth/me` — Get current user info (JWT protected)
   - `POST /api/v1/chat` — Send query to compliance assistant (JWT protected)
   - `GET  /api/v1/conversations` — List user's conversations (JWT protected)
   - `GET  /api/v1/history/{session_id}` — Get conversation history (JWT protected)
   - `DELETE /api/v1/history/{session_id}` — Delete conversation (JWT protected)

4. **Authentication** (`app/core/auth.py`)
   - JWT access tokens signed with `JWT_SECRET_KEY`
   - `get_current_user` FastAPI dependency injected into all protected routes
   - Passwords hashed with bcrypt via `passlib`

5. **Data Persistence** (`app/db/`)
   - `models.py` — SQLAlchemy ORM models for PostgreSQL
     - `User` — User accounts (email, username, hashed_password, is_active)
     - `Conversation` — Session metadata (title, message count, user_id FK)
     - `Message` — Individual messages (role: human/ai, content, created_at)

6. **Services** (`app/services/`)
   - `ai_service.py` — RAG orchestration (LangGraph) with Redis RAG cache
   - `cache_service.py` — Redis session cache (24h) + RAG query cache (1h)
   - `reranker.py` — LLM-based reranking via `gpt-4o-mini` structured output

---

## Common Commands

### Backend Development

**Install dependencies (uv recommended):**
```bash
uv sync
# or
pip install -r requirements.txt
```

**Run backend locally (with auto-reload):**
```bash
python -m app.main
```
Server runs on `http://localhost:8000`. API docs at `/docs`.

**Environment setup:**
```bash
cp .env.example .env
# Fill in: JWT_SECRET_KEY, OPENAI_API_KEY, and database URIs
```

### Frontend Development

**Install dependencies:**
```bash
cd frontend && npm install
```

**Run dev server:**
```bash
npm run dev
```
Frontend runs on `http://localhost:5173` (with HMR).

**Build for production:**
```bash
npm run build
```

### Docker & Full Stack

**Start all services:**
```bash
docker compose up --build
```

Port mapping (host → container):

| Service       | Host Port | Container Port | Purpose              |
|---------------|-----------|----------------|----------------------|
| Frontend      | 3000      | 80             | React app (Nginx)    |
| Backend API   | 8000      | 8000           | FastAPI              |
| Neo4j Browser | 7474      | 7474           | Graph DB UI          |
| Neo4j Bolt    | 7687      | 7687           | Graph DB protocol    |
| Qdrant API    | 6335      | 6333           | Vector DB REST       |
| Qdrant gRPC   | 6336      | 6334           | Vector DB gRPC       |
| Redis         | 6380      | 6379           | Cache layer          |
| PostgreSQL    | 5433      | 5432           | Conversation DB      |

**Start only databases (for local backend dev):**
```bash
docker compose up neo4j qdrant redis postgres -d
```

**Rebuild a specific service:**
```bash
docker compose build backend && docker compose up backend
```

### Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific file
python -m pytest tests/test_auth.py -v
```

---

## Authentication

### Flow
```
POST /api/v1/auth/register  → create account
POST /api/v1/auth/token     → login, returns { access_token }
GET  /api/v1/auth/me        → get current user (Bearer token required)
```

### Protecting a route
```python
from app.core.auth import get_current_user

@router.post("/chat")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
```

### Frontend token management
- Token stored in `localStorage` under key `fpt_access_token`
- All API requests send `Authorization: Bearer <token>` header
- On 401 response → token cleared → page reloads to login screen

---

## GraphRAG Pipeline

### Data flow per request
```
1. JWT validated → user identity extracted
2. Load conversation history from Redis (24h cache)
   └─ Cache miss → fallback to PostgreSQL
3. Check RAG cache in Redis (1h TTL, key: rag:cache:{sha256(query)})
   └─ Cache hit → skip retrieval, go to generation
4. Router node → decide: vector / graph / both
5. Qdrant search (k=5) → LLM reranker (gpt-4o-mini) → top 3 docs
   + Neo4j search (Text2Cypher with fallback)
6. Synthesizer → merge contexts
7. Generator (gpt-4o) → final answer
8. Store RAG result in Redis (1h TTL)
9. Persist messages to PostgreSQL + update Redis session (24h TTL)
```

### Redis key patterns

| Key pattern                    | TTL  | Purpose                     |
|-------------------------------|------|-----------------------------|
| `chat:history:{session_id}`   | 24h  | Conversation session cache  |
| `rag:cache:{sha256_of_query}` | 1h   | GraphRAG retrieval cache    |

### LLM-based reranker (`app/services/reranker.py`)
- Sends query + top-5 Qdrant docs to `gpt-4o-mini` with structured output
- LLM returns ranked indices → extract top-3
- Fallback: if LLM fails → return original Qdrant order (top-3)
- No local model or extra packages required

---

## Project Structure

```
.
├── .github/
│   └── workflows/
│       └── ci-cd.yml              # GitHub Actions: test + Docker build/push
│
├── app/                           # FastAPI application
│   ├── main.py                    # Entry point, lifespan, SPA routing
│   ├── api/
│   │   ├── router.py              # Central route aggregator
│   │   └── routes/
│   │       ├── auth.py            # Register, login, me endpoints
│   │       ├── message.py         # Chat endpoint (JWT protected)
│   │       └── conversation.py    # History endpoints (JWT protected)
│   ├── core/
│   │   ├── auth.py                # JWT logic, get_current_user dependency
│   │   ├── config.py              # Settings (pydantic-settings)
│   │   ├── database.py            # Neo4j, Qdrant connection mgmt
│   │   └── redis_client.py        # Redis pool
│   ├── db/
│   │   ├── models.py              # User, Conversation, Message ORM models
│   │   └── session.py             # Async session factory + init_db
│   ├── services/
│   │   ├── ai_service.py          # RAG orchestration with Redis cache
│   │   ├── cache_service.py       # Session cache + RAG query cache
│   │   ├── reranker.py            # LLM-based reranking (gpt-4o-mini)
│   │   ├── conversation_service.py
│   │   ├── user_service.py        # User CRUD
│   │   └── nodes/
│   │       ├── retrieval.py       # Router, Qdrant, Neo4j, synthesizer nodes
│   │       └── generator.py       # Answer generation node
│   └── schemas/
│       ├── auth.py                # UserCreate, UserResponse, TokenResponse
│       └── conversation.py        # ChatRequest, ChatResponse, HistoryResponse
│
├── frontend/                      # React + Vite
│   └── src/
│       ├── components/
│       │   ├── Auth/              # LoginPage (login + register)
│       │   ├── Chat/
│       │   ├── Header/            # Header with logout button
│       │   ├── Input/
│       │   └── Sidebar/
│       ├── hooks/
│       │   └── useChat.ts
│       ├── api/
│       │   └── client.ts          # API client with JWT header + auth helpers
│       ├── types/
│       └── App.tsx                # Auth gate: shows LoginPage or Chat
│
├── src/                           # Shared Python logic
│   ├── core/                      # LangGraph definitions (reference)
│   ├── nodes/                     # Node implementations (reference)
│   ├── services/                  # LLM + embedding clients
│   ├── storage/                   # Neo4j + Qdrant wrappers
│   └── ingestion/                 # Document ingestion pipeline
│
├── docker/
│   ├── backend.Dockerfile
│   └── frontend.Dockerfile
│
├── tests/
│   ├── conftest.py                # SQLite in-memory DB + ASGI client fixtures
│   ├── test_auth.py               # Auth endpoint tests
│   ├── test_chat.py               # Chat endpoint tests (mocked pipeline)
│   └── test_retrieval.py          # Reranker unit tests
│
├── data/                          # Persistent volumes (gitignored)
│   ├── neo4j/
│   ├── qdrant/
│   ├── postgres/
│   ├── redis/
│   ├── raw/
│   ├── processed/
│   └── index/
│
├── docker-compose.yml
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # uv dependency manifest
├── pytest.ini                     # asyncio_mode = auto
└── .env.example                   # Environment template
```

---

## Environment Variables

```bash
# LLM (required)
OPENAI_API_KEY=sk-...

# JWT Authentication (required)
JWT_SECRET_KEY=change-me-to-a-long-random-string-minimum-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Neo4j
NEO4J_URI=bolt://neo4j:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# Qdrant
QDRANT_URL=http://qdrant:6333

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# PostgreSQL
POSTGRES_URL=postgresql+asyncpg://fpt:fpt_password@postgres:5432/fpt_chat

# Reranker
RERANKER_TOP_N=3

# Cache TTL
SESSION_TTL_SECONDS=86400
RAG_CACHE_TTL_SECONDS=3600

# LangSmith (optional)
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=
LANGCHAIN_PROJECT=FPT_Policy_GraphRAG
```

---

## CI/CD Pipeline (`.github/workflows/ci-cd.yml`)

**Triggers:** push to `main`/`develop`, PR to `main`

**Jobs:**
1. **test** — install deps, run `python -m pytest tests/` with SQLite (no real DB needed)
2. **deploy** — build Docker image, push to GHCR (`ghcr.io/nvanhieu25/fpt-policy-graphrag/backend`)
   - Only runs on push to `main` after `test` passes
   - Tags: `latest` + `{commit-sha}`

---

## Database Setup

### PostgreSQL
- Tables auto-create on startup via `init_db()` (SQLAlchemy `create_all`)
- Tables: `users`, `conversations`, `messages`
- `conversations.user_id` is a nullable FK to `users.id`

### Redis key patterns
```bash
# Session history
docker exec fpt_redis redis-cli GET "chat:history:{session_id}"

# RAG cache
docker exec fpt_redis redis-cli KEYS "rag:cache:*"
```

### Neo4j graph schema
- Node labels: `Policy`, `Department`, `Role`, `Concept`, `Employee`, `Document`
- All nodes use `id` property only
- Relationships: `REPORTS_TO`, `REQUIRES_APPROVAL_FROM`, `GOVERNS`, `HANDLES_ISSUE`

---

## Troubleshooting

**"Not authenticated" error in frontend:**
- User needs to register/login first at `http://localhost:3000`
- Token stored in `localStorage` — clear browser storage and re-login if expired

**Backend won't connect to databases:**
- `docker compose ps` — check all containers are healthy
- Inside Docker, use internal hostnames: `neo4j:7687`, `qdrant:6333`, `redis:6379`, `postgres:5432`

**RAG responses slow (cache not working):**
- Check Redis: `docker exec fpt_redis redis-cli keys "rag:cache:*"`
- Verify `RAG_CACHE_TTL_SECONDS` is set in `.env`

**PostgreSQL tables not created:**
- Tables auto-create on first API call
- Manual check: `docker exec fpt_postgres psql -U fpt -d fpt_chat -c "\dt"`

**Frontend build fails:**
- `cd frontend && rm -rf node_modules && npm install`
- Node version must be 18+
