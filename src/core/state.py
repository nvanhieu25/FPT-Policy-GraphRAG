from typing import TypedDict, Annotated, Sequence
import operator
from langchain_core.messages import BaseMessage

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
