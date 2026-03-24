"""
app/services/ai_service.py

Encapsulates the full LangGraph pipeline (retrieval subgraph + main agent graph).
Moved from src/core/graph.py — import paths updated for the new app/ structure.
Graph topology and routing logic are preserved exactly.
"""
import logging
from typing import TypedDict, Annotated
import operator

from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

from app.services.nodes.retrieval import (
    router_node,
    qdrant_search_node,
    neo4j_search_node,
    synthesizer_node,
)
from app.services.nodes.generator import answer_generator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# State definitions (moved from src/core/state.py)
# ---------------------------------------------------------------------------

class RetrievalState(TypedDict):
    """State for the Retrieval SubGraph."""

    query: str
    routing_decision: str  # "vector", "graph", or "both"
    qdrant_context: str
    neo4j_context: str
    synthesized_context: str


class MainAgentState(TypedDict):
    """State for the Main Agent Graph."""

    messages: Annotated[list[BaseMessage], operator.add]
    current_question: str
    retrieved_info: str
    final_answer: str


# ---------------------------------------------------------------------------
# Retrieval subgraph
# ---------------------------------------------------------------------------

def build_retrieval_subgraph():
    """Build and compile the retrieval subgraph for vector/graph/hybrid search."""
    builder = StateGraph(RetrievalState)
    builder.add_node("router", router_node)
    builder.add_node("qdrant_search", qdrant_search_node)
    builder.add_node("neo4j_search", neo4j_search_node)
    builder.add_node("synthesizer", synthesizer_node)

    builder.add_edge(START, "router")

    def route_search(state: RetrievalState) -> list[str]:
        decision = state.get("routing_decision", "both").lower()
        if decision == "vector":
            print("[Router] Routing to: Vector DB (Qdrant)")
            return ["qdrant_search"]
        elif decision == "graph":
            print("[Router] Routing to: Graph DB (Neo4j)")
            return ["neo4j_search"]
        else:
            print("[Router] Routing to: Both (Hybrid)")
            return ["qdrant_search", "neo4j_search"]

    builder.add_conditional_edges("router", route_search, ["qdrant_search", "neo4j_search"])
    builder.add_edge("qdrant_search", "synthesizer")
    builder.add_edge("neo4j_search", "synthesizer")
    builder.add_edge("synthesizer", END)

    return builder.compile()


# ---------------------------------------------------------------------------
# Main agent graph
# ---------------------------------------------------------------------------

def _make_hybrid_research_node(retrieval_subgraph):
    """Return a closure that invokes the retrieval subgraph."""

    def hybrid_research_node(state: MainAgentState) -> dict:
        question = state["current_question"]
        print(f"\n[HybridResearch] Initiating Subgraph execution for: '{question}'")
        result = retrieval_subgraph.invoke({"query": question})
        synthesized = result.get("synthesized_context", "")
        print("[HybridResearch] Subgraph execution returned synthesized context.")
        return {"retrieved_info": synthesized}

    return hybrid_research_node


def build_super_agent():
    """Build and compile the main conversational agent graph."""
    retrieval_subgraph = build_retrieval_subgraph()

    builder = StateGraph(MainAgentState)
    builder.add_node("hybrid_research", _make_hybrid_research_node(retrieval_subgraph))
    builder.add_node("answer_generator", answer_generator)

    builder.add_edge(START, "hybrid_research")
    builder.add_edge("hybrid_research", "answer_generator")
    builder.add_edge("answer_generator", END)

    return builder.compile()


# ---------------------------------------------------------------------------
# Module-level compiled graph (lazy singleton)
# ---------------------------------------------------------------------------

_super_agent = None


def get_super_agent():
    """Return the compiled LangGraph agent, building it once on first call."""
    global _super_agent
    if _super_agent is None:
        logger.info("[AIService] Building super_agent graph...")
        _super_agent = build_super_agent()
        logger.info("[AIService] super_agent graph ready.")
    return _super_agent


async def run_query(question: str, history: list[BaseMessage] | None = None) -> str:
    """Run a single user question through the full GraphRAG pipeline with Redis caching."""
    from app.services.cache_service import get_rag_cache, set_rag_cache

    # Check RAG cache first
    cached = await get_rag_cache(question)
    if cached:
        logger.info("[AIService] RAG cache hit — skipping pipeline.")
        return cached

    agent = get_super_agent()
    initial_state = {
        "messages": history or [HumanMessage(content=question)],
        "current_question": question,
        "retrieved_info": "",
        "final_answer": "",
    }
    final_state = agent.invoke(initial_state)
    answer = final_state["final_answer"]

    # Cache the result
    await set_rag_cache(question, answer)
    return answer
