"""
app/services/reranker.py

LLM-based reranking for Qdrant vector search results.
Uses the existing OpenAI client — no additional packages required.
"""
import logging
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from app.core.config import settings

logger = logging.getLogger(__name__)


class RankedIndices(BaseModel):
    indices: list[int] = Field(
        description="Indices of documents sorted by relevance to the query, most relevant first."
    )


def rerank(query: str, docs: list, top_n: int | None = None) -> list:
    """Rerank LangChain Document objects using LLM scoring. Returns top_n docs."""
    if not docs:
        return docs

    n = top_n if top_n is not None else settings.reranker_top_n

    numbered = "\n\n".join(
        f"[{i}] {doc.page_content[:300]}" for i, doc in enumerate(docs)
    )
    prompt = f"""You are a relevance ranking assistant.
Given the query and a list of document excerpts, return the indices of the documents \
sorted from most to least relevant to the query. Only include the top {n} most relevant indices.

Query: {query}

Documents:
{numbered}"""

    llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
    try:
        result = llm.with_structured_output(RankedIndices).invoke(prompt)
        top_indices = [i for i in result.indices if 0 <= i < len(docs)][:n]
        reranked = [docs[i] for i in top_indices]
        # Fill remaining slots if LLM returned fewer than n indices
        if len(reranked) < n:
            seen = set(top_indices)
            for i, doc in enumerate(docs):
                if i not in seen:
                    reranked.append(doc)
                if len(reranked) >= n:
                    break
        logger.debug("[Reranker] Reranked %d docs → top %d via LLM.", len(docs), n)
        return reranked
    except Exception as e:
        logger.warning("[Reranker] LLM rerank failed, returning original order: %s", e)
        return docs[:n]
