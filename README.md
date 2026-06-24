# FPT Policy GraphRAG

A retrieval-augmented question-answering system for internal policy compliance at FPT Software. The service answers natural-language questions about company policy by combining semantic vector search with graph traversal, then routing each query to whichever retrieval mode (or combination) fits the question best.

The motivation is straightforward. Pure vector search handles "what does the policy say about X" well, but it struggles with questions that depend on relationships — who approves a given request, which department owns a process, how roles report to one another. Those are graph problems. Rather than force every query through a single retriever, the system inspects the query first and dispatches accordingly.

## How it works

A request travels through a LangGraph workflow rather than a fixed pipeline. The router node classifies the query and decides between vector retrieval, graph retrieval, or both. When both are selected, the two searches run as parallel branches and their results are merged downstream.

```
JWT validation
   └─ identity + session scope extracted
Conversation history
   └─ Redis (24h)  ──miss──▶  PostgreSQL
RAG cache lookup            (key: rag:cache:{sha256(query)}, 1h TTL)
   └─ hit ──▶ skip retrieval, go straight to generation
Router  ──▶  vector | graph | both
   ├─ Qdrant search (k=5)  ──▶  LLM reranker (gpt-4o-mini)  ──▶  top 3
   └─ Neo4j search (Text2Cypher, with fallback)
Synthesizer  ──▶  merge contexts
Generator (gpt-4o)  ──▶  answer
Persist: Redis RAG cache (1h) + PostgreSQL messages + Redis session (24h)
```

Reranking is done by the LLM rather than a local cross-encoder. The top five candidates from Qdrant are passed to `gpt-4o-mini` with a structured-output schema; the model returns ranked indices and the top three are kept. If that call fails for any reason, the system falls back to Qdrant's original ordering, so a reranker outage degrades quality without breaking the request.

The Redis RAG cache is keyed on the SHA-256 of the query text. Repeated or near-identical questions skip retrieval entirely and reuse the stored result for one hour, which is the dominant cost saving under realistic traffic where the same handful of policy questions recur.

## Architecture

| Layer | Technology | Role |
|-------|------------|------|
| API | FastAPI + Uvicorn | HTTP server, port 8000 |
| Orchestration | LangChain / LangGraph | Routing and agentic retrieval |
| Vector store | Qdrant | Semantic similarity search |
| Graph store | Neo4j | Relationship and approval-chain queries |
| Relational store | PostgreSQL | Users, conversations, messages |
| Cache | Redis | Session history (24h) and RAG results (1h) |
| Frontend | React 18 + TypeScript + Vite | Chat UI with Markdown rendering |

The graph schema uses six node labels — `Policy`, `Department`, `Role`, `Concept`, `Employee`, `Document` — connected by relationships such as `REPORTS_TO`, `REQUIRES_APPROVAL_FROM`, `GOVERNS`, and `HANDLES_ISSUE`. Every node is identified by a single `id` property.

## Authentication

Access is gated by JWT. A client registers, logs in to receive an access token, and attaches that token as a `Bearer` header on every subsequent call. Passwords are hashed with bcrypt through `passlib`. The `get_current_user` dependency is injected into all protected routes, so identity is available wherever a request is handled and conversations are scoped per user.

```
POST /api/v1/auth/register   create an account
POST /api/v1/auth/token      log in, returns { access_token }
GET  /api/v1/auth/me         current user (Bearer required)
```

On the frontend the token lives in `localStorage` under `fpt_access_token`. A `401` response clears the token and returns the user to the login screen.

## API surface

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/auth/register` | Register a new user |
| POST | `/api/v1/auth/token` | Log in, obtain JWT |
| GET | `/api/v1/auth/me` | Current user info |
| POST | `/api/v1/chat` | Ask the compliance assistant |
| GET | `/api/v1/conversations` | List the caller's conversations |
| GET | `/api/v1/history/{session_id}` | Fetch a conversation |
| DELETE | `/api/v1/history/{session_id}` | Delete a conversation |

Interactive documentation is served at `/docs` once the backend is running.

## Running locally

The project targets Python 3.13 and manages dependencies with [uv](https://github.com/astral-sh/uv).

Start the data stores in Docker and run the API against them:

```bash
docker compose up neo4j qdrant redis postgres -d   # databases only
uv sync                                            # install dependencies
cp .env.example .env                               # then fill in secrets
python -m app.main                                 # API on :8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev        # Vite dev server on :5173
```

Or bring up the entire stack at once:

```bash
docker compose up --build
```

Host port mapping under Compose:

| Service | Host | Container |
|---------|------|-----------|
| Frontend (Nginx) | 3000 | 80 |
| Backend API | 8000 | 8000 |
| Neo4j Browser | 7474 | 7474 |
| Neo4j Bolt | 7687 | 7687 |
| Qdrant REST | 6335 | 6333 |
| Qdrant gRPC | 6336 | 6334 |
| Redis | 6380 | 6379 |
| PostgreSQL | 5433 | 5432 |

## Configuration

Required secrets are `OPENAI_API_KEY` and `JWT_SECRET_KEY` (use a random string of at least 32 characters). Database URIs, JWT lifetime, reranker depth (`RERANKER_TOP_N`), and cache TTLs (`SESSION_TTL_SECONDS`, `RAG_CACHE_TTL_SECONDS`) are all set through environment variables; see `.env.example` for the full list and defaults.

## Testing

```bash
python -m pytest tests/ -v
```

The suite runs against an in-memory SQLite database and mocks the retrieval pipeline, so no live Neo4j, Qdrant, or Redis instance is needed. This is the same path the CI workflow exercises on every push and pull request.

## Repository layout

```
app/                FastAPI application
  api/routes/         auth, chat, conversation endpoints
  core/               JWT, config, database and Redis clients
  db/                 SQLAlchemy models and session factory
  services/           ai_service, cache_service, reranker, nodes/
  schemas/            request/response models
frontend/           React + Vite client
src/                 ingestion pipeline and shared LLM/storage logic
docker/             backend and frontend Dockerfiles
tests/              auth, chat, and reranker tests
docker-compose.yml
pyproject.toml
```

## Continuous integration

The workflow in `.github/workflows/ci-cd.yml` runs the test suite on pushes to `main` and `develop` and on pull requests to `main`. When tests pass on `main`, it builds the backend image and publishes it to GitHub Container Registry, tagged with both `latest` and the commit SHA.
