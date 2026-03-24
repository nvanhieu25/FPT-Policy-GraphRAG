from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage
from src.core.state import RetrievalState, MainAgentState
from src.nodes.retrieval import (
    router_node,
    qdrant_search_node,
    neo4j_search_node,
    synthesizer_node,
)
from src.nodes.generator import answer_generator

def build_retrieval_subgraph():
    """Builds and compiles the retrieval subgraph for vector/graph/hybrid search."""
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

    # Edges from search nodes to synthesizer
    builder.add_edge("qdrant_search", "synthesizer")
    builder.add_edge("neo4j_search", "synthesizer")
    builder.add_edge("synthesizer", END)

    return builder.compile()

# Compile Subgraph
retrieval_subgraph = build_retrieval_subgraph()

def hybrid_research_node(state: MainAgentState) -> dict:
    """Invokes the retrieval subgraph and extracts synthesized context."""
    question = state["current_question"]
    print(f"\n[HybridResearch] Initiating Subgraph execution for: '{question}'")
    
    # Run the compiled subgraph
    result = retrieval_subgraph.invoke({"query": question})
    
    synthesized = result.get("synthesized_context", "")
    print("[HybridResearch] Subgraph execution returned synthesized context.")
    return {"retrieved_info": synthesized}

def build_super_agent():
    """Builds the main conversational agent graph."""
    builder = StateGraph(MainAgentState)
    builder.add_node("hybrid_research", hybrid_research_node)
    builder.add_node("answer_generator", answer_generator)

    builder.add_edge(START, "hybrid_research")
    builder.add_edge("hybrid_research", "answer_generator")
    builder.add_edge("answer_generator", END)

    return builder.compile()

# Compile Main Agent Graph
super_agent = build_super_agent()

if __name__ == "__main__":
    print("="*60)
    print("TESTING HYBRID GRAPHRAG WORKFLOW (REFACTORED ARCHITECTURE)")
    print("="*60)
    
    test_question = "Tôi ở bộ phận mua sắm. Anh trai tôi mở công ty văn phòng phẩm và muốn làm supplier cho công ty. Tôi có được quyết định chọn công ty của anh trai không và phải xin phép ai?"
    
    initial_state = {
        "messages": [HumanMessage(content=test_question)],
        "current_question": test_question,
        "retrieved_info": "",
        "final_answer": ""
    }
    
    try:
        final_state = super_agent.invoke(initial_state)
        print("\n" + "="*60)
        print("FINAL ANSWER")
        print("="*60)
        print(final_state["final_answer"])
    except Exception as e:
        print(f"\n[Error] Execution failed: {e}")
