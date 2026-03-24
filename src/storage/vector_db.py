import os
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_qdrant import QdrantVectorStore
from src.services.embeddings import get_embeddings_model
from dotenv import load_dotenv

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION_NAME = "fpt_policies"

def get_qdrant_client():
    return QdrantClient(url=QDRANT_URL)

def ensure_collection(client: QdrantClient):
    if not client.collection_exists(QDRANT_COLLECTION_NAME):
        client.create_collection(
            collection_name=QDRANT_COLLECTION_NAME,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )

def get_qdrant_vector_store():
    embeddings = get_embeddings_model()
    return QdrantVectorStore.from_existing_collection(
        embedding=embeddings,
        url=QDRANT_URL,
        prefer_grpc=False,
        collection_name=QDRANT_COLLECTION_NAME,
    )
    
def ingest_documents_qdrant(chunks):
    embeddings = get_embeddings_model()
    QdrantVectorStore.from_documents(
        chunks,
        embeddings,
        url=QDRANT_URL,
        prefer_grpc=False,
        collection_name=QDRANT_COLLECTION_NAME,
    )
