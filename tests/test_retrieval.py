"""
tests/test_retrieval.py

Unit tests for reranker and RAG cache.
"""
import pytest
from unittest.mock import MagicMock, patch
from langchain_core.documents import Document


def make_docs(contents):
    return [Document(page_content=c) for c in contents]


def test_reranker_orders_by_score():
    from app.services.reranker import rerank
    docs = make_docs(["irrelevant doc", "leave policy details", "unrelated content"])
    scores = [0.1, 0.9, 0.3]
    with patch("app.services.reranker.get_reranker") as mock_get:
        mock_model = MagicMock()
        mock_model.predict.return_value = scores
        mock_get.return_value = mock_model
        result = rerank("leave policy", docs, top_n=3)
    assert result[0].page_content == "leave policy details"


def test_reranker_respects_top_n():
    from app.services.reranker import rerank
    docs = make_docs(["a", "b", "c", "d", "e"])
    scores = [0.5, 0.4, 0.3, 0.2, 0.1]
    with patch("app.services.reranker.get_reranker") as mock_get:
        mock_model = MagicMock()
        mock_model.predict.return_value = scores
        mock_get.return_value = mock_model
        result = rerank("query", docs, top_n=2)
    assert len(result) == 2


def test_reranker_empty_docs():
    from app.services.reranker import rerank
    result = rerank("query", [])
    assert result == []
