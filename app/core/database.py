"""
app/core/database.py

Manages connections to Neo4j and Qdrant.
Logic is preserved from src/storage/graph_db.py and src/storage/vector_db.py
but integrated with centralized Settings and proper lifecycle management.
"""
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Neo4j
# ---------------------------------------------------------------------------

_neo4j_instance = None


class Neo4jGraphWrapper:
    """Lightweight Neo4j wrapper that avoids heavy schema introspection.

    Uses the neo4j Python driver directly instead of LangChain's Neo4jGraph,
    which can hang during schema introspection.
    """

    def __init__(self, uri: str, username: str, password: str):
        from neo4j import GraphDatabase

        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.driver.verify_connectivity()
        logger.info("[Neo4j] Connection verified at %s", uri)

    def query(self, cypher: str, params: dict = None) -> list[dict]:
        """Execute a Cypher query and return results as list of dicts."""
        with self.driver.session() as session:
            result = session.run(cypher, parameters=params or {})
            return [record.data() for record in result]

    def close(self):
        self.driver.close()
        logger.info("[Neo4j] Driver closed.")


def get_neo4j_graph() -> Neo4jGraphWrapper:
    """Return the cached Neo4j wrapper instance (lazy singleton)."""
    global _neo4j_instance
    if _neo4j_instance is None:
        _neo4j_instance = Neo4jGraphWrapper(
            uri=settings.neo4j_uri,
            username=settings.neo4j_username,
            password=settings.neo4j_password,
        )
    return _neo4j_instance


def close_neo4j():
    """Close the Neo4j driver (call on app shutdown)."""
    global _neo4j_instance
    if _neo4j_instance is not None:
        _neo4j_instance.close()
        _neo4j_instance = None


def get_neo4j_langchain_graph():
    """Return a LangChain Neo4jGraph instance — used ONLY for ingestion pipeline.

    Warning: slow due to schema introspection; do not use in request paths.
    """
    from langchain_community.graphs import Neo4jGraph

    return Neo4jGraph(
        url=settings.neo4j_uri,
        username=settings.neo4j_username,
        password=settings.neo4j_password,
    )


# ---------------------------------------------------------------------------
# Qdrant
# ---------------------------------------------------------------------------

_qdrant_client_instance = None


def get_qdrant_client():
    """Return the cached Qdrant client (lazy singleton)."""
    global _qdrant_client_instance
    if _qdrant_client_instance is None:
        from qdrant_client import QdrantClient

        _qdrant_client_instance = QdrantClient(url=settings.qdrant_url)
        logger.info("[Qdrant] Client initialized at %s", settings.qdrant_url)
    return _qdrant_client_instance


def close_qdrant():
    """Close the Qdrant client (call on app shutdown)."""
    global _qdrant_client_instance
    if _qdrant_client_instance is not None:
        _qdrant_client_instance.close()
        _qdrant_client_instance = None
        logger.info("[Qdrant] Client closed.")


def ensure_qdrant_collection():
    """Create the Qdrant collection if it does not already exist."""
    from qdrant_client.http.models import Distance, VectorParams

    client = get_qdrant_client()
    if not client.collection_exists(settings.qdrant_collection_name):
        client.create_collection(
            collection_name=settings.qdrant_collection_name,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )
        logger.info("[Qdrant] Created collection '%s'.", settings.qdrant_collection_name)


def get_qdrant_vector_store():
    """Return a LangChain QdrantVectorStore backed by the existing collection."""
    from langchain_qdrant import QdrantVectorStore
    from langchain_openai import OpenAIEmbeddings

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    return QdrantVectorStore.from_existing_collection(
        embedding=embeddings,
        url=settings.qdrant_url,
        prefer_grpc=False,
        collection_name=settings.qdrant_collection_name,
    )


def ingest_documents_qdrant(chunks):
    """Ingest document chunks into Qdrant (used by ingestion pipeline)."""
    from langchain_qdrant import QdrantVectorStore
    from langchain_openai import OpenAIEmbeddings

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    QdrantVectorStore.from_documents(
        chunks,
        embeddings,
        url=settings.qdrant_url,
        prefer_grpc=False,
        collection_name=settings.qdrant_collection_name,
    )
    logger.info("[Qdrant] Ingested %d chunks.", len(chunks))
