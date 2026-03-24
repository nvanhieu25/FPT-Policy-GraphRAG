from pydantic import BaseModel, Field
from src.core.state import RetrievalState
from src.services.llm import get_llm_model
from src.storage.vector_db import get_qdrant_vector_store
from src.storage.graph_db import get_neo4j_graph

class RouteDecision(BaseModel):
    decision: str = Field(description="Must be one of: 'vector', 'graph', or 'both'")

def router_node(state: RetrievalState) -> dict:
    query = state["query"]
    prompt = f"""
Given the user query, decide if we should use vector search (for broad semantic similarity), graph search (for finding specific relationships between roles, departments, concepts, or exact policies), or both.
Respond with 'vector', 'graph', or 'both'. Defaults to both if unsure.
Query: {query}"""
    llm = get_llm_model()
    try:
        response = llm.with_structured_output(RouteDecision).invoke(prompt)
        decision = response.decision.lower()
        if decision not in ["vector", "graph", "both"]:
            decision = "both"
    except Exception:
        decision = "both"
    
    return {"routing_decision": decision}

def qdrant_search_node(state: RetrievalState) -> dict:
    query = state["query"]
    print(f"[QdrantSearch] Executing vector search for: {query}")
    try:
        qdrant = get_qdrant_vector_store()
        docs = qdrant.similarity_search(query, k=3)
        context = "\n\n".join(doc.page_content for doc in docs)
        return {"qdrant_context": context}
    except Exception as e:
        print(f"[QdrantSearch] Error: {e}")
        return {"qdrant_context": ""}

class CypherQuery(BaseModel):
    query: str = Field(description="A valid Neo4j Cypher query")

def neo4j_search_node(state: RetrievalState) -> dict:
    query = state["query"]
    print(f"[Neo4jSearch] Executing Text2Cypher for: {query}")
    llm = get_llm_model()
    prompt = f"""
You are an expert Neo4j Cypher query developer.

=== SCHEMA ===
Node Labels: Policy, Department, Role, Concept, Employee, Document
IMPORTANT: All nodes have ONLY the `id` property. Always use `n.id` not `n.name`.

Valid Relationships (Topology):
- (Role)-[:REPORTS_TO]->(Role)
- (Role/Department)-[:REQUIRES_APPROVAL_FROM]->(Department)
- (Policy)-[:GOVERNS]->(Concept)
- (Department)-[:HANDLES_ISSUE]->(Concept)

=== QUERY RULES ===
1. Use `n.id` for all property access.
2. CRITICAL: The graph data is in ENGLISH. You MUST translate Vietnamese keywords to English before querying. (e.g., "bộ phận mua sắm" -> "procurement").
3. Use case-insensitive partial matching: `toLower(n.id) CONTAINS toLower('english_keyword')`.
4. Keep queries read-only. Do NOT hallucinate labels or relationship types.
5. Limit the results to a maximum of 15 paths to avoid context overflow.

=== EXAMPLES ===
User: "Xung đột lợi ích phải báo cáo cho ai?"
Cypher: MATCH (c:Concept)-[r]-(d:Department) WHERE toLower(c.id) CONTAINS toLower('conflict of interest') RETURN labels(c)[0] as From, c.id as FromName, type(r) as Relation, labels(d)[0] as To, d.id as ToName LIMIT 15
User: "Giám đốc cần xin phép ai khi đầu tư ngoài?"
Cypher: MATCH (role:Role)-[r:REQUIRES_APPROVAL_FROM]->(d:Department) WHERE toLower(role.id) CONTAINS toLower('director') RETURN role.id as Role_Name, type(r) as Action, d.id as Dept_Name LIMIT 10

Question: {query}
"""
    graph = get_neo4j_graph()
    try:
        result = llm.with_structured_output(CypherQuery).invoke(prompt)
        cypher = result.query
        print(f"[Neo4jSearch] Generated Cypher: {cypher}")
        records = graph.query(cypher)
        if not records:
            print("[Neo4jSearch] Query returned 0 results. Trying broader fallback...")
            
            class FallbackKeyword(BaseModel):
                keyword: str = Field(description="A single core english noun extracted or translated from the query")

            kw_prompt = f"Extract exactly one core single-word English noun that represents the main entity in this query (translate to English if necessary): {query}"
            
            try:
                kw_result = llm.with_structured_output(FallbackKeyword).invoke(kw_prompt)
                keyword = kw_result.keyword.strip()
                if keyword:
                    fallback_cypher = f"MATCH (n)-[r]-(m) WHERE toLower(n.id) CONTAINS toLower('{keyword}') RETURN labels(n)[0] as FromType, n.id as FromName, type(r) as Relation, labels(m)[0] as ToType, m.id as ToName LIMIT 15"
                    print(f"[Neo4jSearch] Fallback Cypher (Keyword: {keyword}): {fallback_cypher}")
                    records = graph.query(fallback_cypher)
            except Exception as e:
                print(f"[Neo4jSearch] LLM fallback extraction failed: {e}")
                
        context = str(records) if records else ""
        print(f"[Neo4jSearch] Returned {len(records) if records else 0} records.")
        return {"neo4j_context": context}
    except Exception as e:
        print(f"[Neo4jSearch] Text2Cypher error: {e}")
        try:
            print("[Neo4jSearch] Attempting generic keyword fallback...")
            fallback_records = graph.query(
                "MATCH (n)-[r]->(m) RETURN labels(n) as from_type, n.id as from_id, "
                "type(r) as rel, labels(m) as to_type, m.id as to_id LIMIT 15"
            )
            return {"neo4j_context": f"Graph sample: {fallback_records}"}
        except Exception as e2:
            print(f"[Neo4jSearch] Persistent failure: {e2}")
            return {"neo4j_context": ""}

def synthesizer_node(state: RetrievalState) -> dict:
    q_ctx = state.get("qdrant_context", "")
    n_ctx = state.get("neo4j_context", "")
    query = state["query"]
    
    print("[Synthesizer] Merging contexts...")
    prompt = f"""
You are synthesizing retrieved context from a graph and a vector database for an AI assistant.
Combine vector search results and graph search results smoothly into a coherent body of knowledge.
Focus only on relevant details to the query. Keep it informative.

Query: {query}

--- VECTOR CONTEXT ---
{q_ctx}

--- GRAPH CONTEXT ---
{n_ctx}
"""
    llm = get_llm_model()
    response = llm.invoke(prompt)
    return {"synthesized_context": response.content}
