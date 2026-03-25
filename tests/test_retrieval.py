"""
tests/test_retrieval.py

Unit tests for reranker and RAG cache.
"""
import pytest
from unittest.mock import MagicMock, patch
from langchain_core.documents import Document


def make_docs(contents):
    return [Document(page_content=c) for c in contents]


def test_reranker_returns_top_n():
    from app.services.reranker import rerank, RankedIndices
    docs = make_docs(["irrelevant doc", "leave policy details", "unrelated content"])
    mock_result = RankedIndices(indices=[1, 2, 0])
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value.invoke.return_value = mock_result
    with patch("app.services.reranker.ChatOpenAI", return_value=mock_llm):
        result = rerank("leave policy", docs, top_n=2)
    assert len(result) == 2
    assert result[0].page_content == "leave policy details"


def test_reranker_respects_top_n():
    from app.services.reranker import rerank, RankedIndices
    docs = make_docs(["a", "b", "c", "d", "e"])
    mock_result = RankedIndices(indices=[2, 0, 4, 1, 3])
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value.invoke.return_value = mock_result
    with patch("app.services.reranker.ChatOpenAI", return_value=mock_llm):
        result = rerank("query", docs, top_n=3)
    assert len(result) == 3
    assert result[0].page_content == "c"


def test_reranker_empty_docs():
    from app.services.reranker import rerank
    result = rerank("query", [])
    assert result == []


def test_reranker_fallback_on_llm_error():
    from app.services.reranker import rerank
    docs = make_docs(["a", "b", "c"])
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value.invoke.side_effect = Exception("LLM error")
    with patch("app.services.reranker.ChatOpenAI", return_value=mock_llm):
        result = rerank("query", docs, top_n=2)
    assert len(result) == 2
    assert result[0].page_content == "a"
