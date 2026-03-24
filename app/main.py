"""
app/main.py

FastAPI application entry point.
Manages the full lifecycle (startup / shutdown) of Redis, Neo4j, and Qdrant connections.
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.redis_client import close_redis_pool
from app.core.database import close_neo4j, close_qdrant
from app.db.session import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan context manager — replaces deprecated @app.on_event handlers
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Resources are initialised lazily on first use (no blocking at startup).
    We only need to ensure they are cleanly closed on shutdown.
    """
    logger.info("=== FPT Policy GraphRAG API starting up ===")
    await init_db()
    logger.info("PostgreSQL tables ready.")
    yield
    # --- shutdown ---
    logger.info("=== Shutting down — closing connections ===")
    close_neo4j()
    close_qdrant()
    await close_redis_pool()
    logger.info("=== All connections closed. Goodbye! ===")


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="FPT Policy GraphRAG API",
    description=(
        "Hybrid GraphRAG compliance assistant for FPT Software internal policies. "
        "Combines vector search (Qdrant) and graph search (Neo4j) via LangGraph."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow all origins for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all API routes under /api/v1
app.include_router(api_router, prefix="/api/v1")

# Serve built frontend (frontend/dist) if it exists
_frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(_frontend_dist / "assets")), name="assets")

    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        return FileResponse(str(_frontend_dist / "index.html"))

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        """Catch-all route — serves index.html for client-side routing."""
        return FileResponse(str(_frontend_dist / "index.html"))


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["System"], summary="Health check")
async def health():
    """Simple liveness check — returns 200 when the server is running."""
    return {"status": "ok", "service": "FPT Policy GraphRAG API"}


# ---------------------------------------------------------------------------
# Dev entrypoint: python -m app.main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
