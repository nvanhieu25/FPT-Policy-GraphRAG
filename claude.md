# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**FPT Policy GraphRAG** is a hybrid retrieval-augmented generation system for internal policy compliance assistance at FPT Software. It combines:
- **Vector search** (Qdrant) for semantic similarity
- **Graph search** (Neo4j) for relationship-based queries
- **Hybrid routing** to intelligently choose or combine both search modes
- **LangGraph orchestration** for multi-step agentic workflows

The system includes a FastAPI backend, React frontend, and four database services (PostgreSQL, Neo4j, Qdrant, Redis).

## Architecture

### Backend Stack
- **FastAPI** (uvicorn) — HTTP API server on port 8000
- **LangChain / LangGraph** — LLM orchestration and agentic workflows
- **PostgreSQL** — Persistent conversation storage (port 5432, exposed on 5433)
- **Neo4j** — Graph database for relational policy data (port 7687)
- **Qdrant** — Vector database for semantic search (port 6333)
- **Redis** — Cache for conversation history with TTL (port 6379)

### Frontend Stack
- **React 18** with TypeScript
- **Vite** for bundling and HMR
- **React Markdown** for policy rendering

### Key Layers

1. **Ingestion Pipeline** (`src/ingestion/`)
   - Extracts policies from documents (PDF via PyMUPDF)
   - Chunks content and creates embeddings
   - Populates Neo4j and Qdrant

2. **LangGraph Workflow** (`src/core/graph.py`, `src/nodes/`)
   - Routing node decides between vector/graph/hybrid search
   - Qdrant and Neo4j search nodes execute retrieval
   - Synthesizer aggregates results
   - Generator produces final answers

3. **FastAPI Routes** (`app/api/routes/`)
   - `/api/v1/chat` — Send query to compliance assistant
   - `/api/v1/history/{session_id}` — Get/delete conversation history

4. **Data Persistence** (`app/db/`)
   - `models.py` — SQLAlchemy ORM models for PostgreSQL
     - `Conversation` — Session metadata (title, message count, timestamps)
     - `Message` — Individual messages (role: human/ai, content, created_at)

5. **Services** (`app/services/`)
   - `ai_service.py` — Main RAG orchestration (LangGraph)
   - `cache_service.py` — Redis-backed session caching (24h TTL)

## Common Commands

### Backend Development

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Run backend locally (with auto-reload):**
```bash
python -m app.main
```
Server runs on `http://localhost:8000`. API docs at `/docs`.

**Environment setup:**
Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
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
Output: `frontend/dist/` — automatically served by FastAPI when present.

**Linting:**
```bash
npm run lint
```

### Docker & Full Stack

**Start all services:**
```bash
docker compose up --build
```

Port Mapping (host → container):
| Service | Host Port | Container Port | Purpose |
|---------|-----------|-----------------|---------|
| Frontend | 3000 | 80 | React app (Nginx) |
| Backend API | 8000 | 8000 | FastAPI |
| Neo4j Browser | 7474 | 7474 | Graph DB UI |
| Neo4j Bolt | 7687 | 7687 | Graph DB protocol |
| Qdrant API | 6335 | 6333 | Vector DB REST |
| Qdrant gRPC | 6336 | 6334 | Vector DB gRPC |
| Redis | 6380 | 6379 | Cache layer |
| PostgreSQL | 5433 | 5432 | Conversation DB |

**Start only databases (for local backend development):**
```bash
docker compose up neo4j qdrant redis
```

**Rebuild a specific service:**
```bash
docker compose build backend && docker compose up backend
```

## Database Setup & Ingestion

### PostgreSQL (Persistent Conversation Storage)
- Connection: `postgresql://fpt:fpt_password@localhost:5433/fpt_chat` (locally)
- Inside Docker: `postgresql+asyncpg://fpt:fpt_password@postgres:5432/fpt_chat`
- Tables: `conversations`, `messages`
- Storage persisted to `data/postgres/`
- **Schema auto-creates on first run** via SQLAlchemy ORM

### Redis (Session Cache - 24h TTL)
- Host: `localhost`, Port: `6380` (mapped from container 6379)
- Key pattern: `chat:history:{session_id}`
- Persisted to `data/redis/`
- Auto-cleanup after 24 hours (SESSION_TTL_SECONDS)

### Neo4j (Policy Graph)
- Bolt protocol: `bolt://localhost:7687` (or `neo4j:7687` inside Docker)
- Auth: `neo4j / password` (from docker-compose.yml)
- Browser UI: `http://localhost:7474`
- Storage persisted to `data/neo4j/`

### Qdrant (Vector Search)
- REST API: `http://localhost:6335`
- gRPC: `localhost:6336`
- Storage persisted to `data/qdrant/`

## Project Structure

```
.
├── app/                        # FastAPI application
│   ├── main.py                # Entry point, lifespan, SPA routing
│   ├── api/
│   │   ├── router.py          # Central route aggregator
│   │   └── routes/            # Endpoint implementations
│   │       ├── message.py     # Chat query endpoint
│   │       └── conversation.py # History retrieval/deletion
│   ├── core/
│   │   ├── config.py          # Settings management
│   │   ├── database.py        # Neo4j, Qdrant connection mgmt
│   │   └── redis_client.py    # Redis pool
│   ├── db/                    # Database persistence
│   │   ├── models.py          # SQLAlchemy ORM (Conversation, Message)
│   │   └── session.py         # Database session factory
│   ├── services/              # Business logic
│   │   ├── ai_service.py      # RAG orchestration (LangGraph)
│   │   ├── cache_service.py   # Redis integration
│   │   └── nodes/             # LangGraph nodes
│   └── schemas/               # Pydantic models
│
├── frontend/                   # React + Vite
│   ├── src/
│   │   ├── components/        # UI components
│   │   ├── hooks/             # Custom React hooks
│   │   ├── types/             # TypeScript interfaces
│   │   ├── api/               # API client code
│   │   └── App.tsx            # Root component
│   ├── package.json           # npm dependencies
│   └── tsconfig.json          # TypeScript config
│
├── src/                        # Shared Python logic (non-FastAPI)
│   ├── core/
│   │   ├── graph.py           # LangGraph workflow definition
│   │   └── state.py           # State schemas for LangGraph
│   ├── nodes/                 # LangGraph node implementations
│   │   ├── retrieval.py       # Search/routing/synthesis nodes
│   │   └── generator.py       # Answer generation node
│   ├── services/              # Utilities
│   │   ├── llm.py             # LLM client (OpenAI)
│   │   └── embeddings.py      # Embedding model
│   ├── storage/               # Database clients
│   │   ├── graph_db.py        # Neo4j wrapper
│   │   └── vector_db.py       # Qdrant wrapper
│   └── ingestion/             # Data pipeline
│       └── pipeline.py        # Document → chunks → embeddings
│
├── docker/                    # Dockerfiles
│   ├── backend.Dockerfile
│   └── frontend.Dockerfile
│
├── data/                      # Persistent volumes
│   ├── neo4j/
│   ├── qdrant/
│   └── redis/
│
├── docker-compose.yml         # Full stack orchestration
├── requirements.txt           # Python dependencies
├── .env.example               # Environment template
└── README.md / claude.md      # Documentation
```

## Data Flow

1. **Query arrives** → FastAPI `POST /api/v1/chat` with `{session_id, query}`
2. **Load history** → Fetch from Redis (fast, 24h cache)
   - If miss → Fetch from PostgreSQL (persistent backup)
3. **AI Service** → Invokes LangGraph workflow with conversation context
4. **Routing** → Router node decides search strategy (vector/graph/hybrid)
5. **Retrieval** → Qdrant and/or Neo4j search nodes fetch policy context
6. **Synthesis** → Aggregates and ranks search results
7. **Generation** → LLM produces answer using context + conversation history
8. **Persist** → Save conversation to both:
   - **PostgreSQL** (persistent, permanent)
   - **Redis** (cache, auto-expires after 24h)
9. **Response** → Return answer to frontend

## Key Considerations

### Connection Management
- **FastAPI lifespan** handles startup/shutdown of Neo4j, Qdrant, Redis, and PostgreSQL
- **Lazy initialization**: connections created on first use, not at startup
- **PostgreSQL**: SQLAlchemy async session factory with connection pooling
- **Tables auto-create** on first query (ORM declarative)
- See `app/main.py` lifespan, `app/core/` modules, and `app/db/session.py`

### Conversation Storage (Dual Layer)
- **PostgreSQL**: Permanent, queryable, indexed by session_id
- **Redis**: Cache with 24-hour TTL for fast access
- On chat: load from Redis (fast) → fallback to PostgreSQL if not found
- On save: write to both Redis and PostgreSQL simultaneously

### Static File Serving
- Built frontend (`frontend/dist/`) is mounted at `/` and `/assets`
- If `frontend/dist/` doesn't exist, only API is available
- Fallback SPA routing: all non-API paths serve `index.html` for client-side routing

### CORS
- Configured to allow all origins (`*`) for local development
- Frontend dev server (port 5173) makes CORS requests to backend (port 8000)
- Update in production

### Environment Variables
- Backend reads from `.env` (via `pydantic-settings`)
- Docker Compose overrides with service hostnames (e.g., `NEO4J_URI=bolt://neo4j:7687`)
- See `.env.example` for required keys (OpenAI API key, database URIs)

## Accessing Services

### Web Interfaces
- **Frontend (User UI)**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs (Swagger UI)
- **Backend ReDoc**: http://localhost:8000/redoc
- **Neo4j Browser**: http://localhost:7474 (user: `neo4j`, password: `password`)

### Direct Database Access
```bash
# PostgreSQL CLI
docker exec fpt_postgres psql -U fpt -d fpt_chat

# Redis CLI
docker exec fpt_redis redis-cli

# Neo4j Cypher Shell
docker exec fpt_neo4j cypher-shell -u neo4j -p password

# Qdrant REST API
curl http://localhost:6335/collections
```

## Testing

Tests directory is present but currently empty. Testing is typically ad-hoc via:
- Jupyter notebooks: `test_graphdb.ipynb`, `test_queries.ipynb`
- Manual API testing: OpenAPI docs at `http://localhost:8000/docs`
- Database inspection commands above

## Troubleshooting

**Backend won't connect to databases:**
- Ensure docker containers are healthy: `docker compose ps`
- Check environment variables in `.env`
- Inside containers, services use internal hostnames:
  - Neo4j: `neo4j:7687`
  - Qdrant: `qdrant:6333`
  - Redis: `redis:6379`
  - PostgreSQL: `postgres:5432`
- Locally, use `localhost` and mapped ports from docker-compose.yml

**PostgreSQL tables not created:**
- Tables auto-create on first API call via SQLAlchemy ORM
- To manually verify: `psql -h localhost -U fpt -d fpt_chat -p 5433`
- Or use Docker: `docker exec fpt_postgres psql -U fpt -d fpt_chat -c "\\dt"`

**Frontend build fails:**
- Clear node_modules: `cd frontend && rm -rf node_modules && npm install`
- Check Node version (recommend 18+)

**Redis connection issues:**
- Redis client expects async context in FastAPI. See `app/services/cache_service.py`
- Port mapping: container 6379 → host 6380
- Check Redis health: `docker exec fpt_redis redis-cli ping`

**Conversation history missing:**
- Check Redis first (fast cache): `docker exec fpt_redis redis-cli GET "chat:history:{session_id}"`
- Check PostgreSQL (persistent): `docker exec fpt_postgres psql -U fpt -d fpt_chat -c "SELECT * FROM conversations WHERE id = '{session_id}'"`
- History expires in Redis after 24h but persists in PostgreSQL
