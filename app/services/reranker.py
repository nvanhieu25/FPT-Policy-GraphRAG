"""
app/services/reranker.py

Cross-encoder reranking for Qdrant vector search results.
"""
import logging
from sentence_transformers import CrossEncoder
from app.core.config import settings

logger = logging.getLogger(__name__)
_model: CrossEncoder | None = None


def get_reranker() -> CrossEncoder:
    global _model
    if _model is None:
        logger.info("[Reranker] Loading cross-encoder model: %s", settings.reranker_model)
        _model = CrossEncoder(settings.reranker_model)
        logger.info("[Reranker] Model loaded.")
    return _model


def rerank(query: str, docs: list, top_n: int | None = None) -> list:
    """Rerank LangChain Document objects by cross-encoder score. Returns top_n docs."""
    if not docs:
        return docs
    n = top_n if top_n is not None else settings.reranker_top_n
    model = get_reranker()
    pairs = [(query, doc.page_content) for doc in docs]
    scores = model.predict(pairs)
    ranked = sorted(zip(scores, docs), key=lambda x: x[0], reverse=True)
    return [doc for _, doc in ranked[:n]]
