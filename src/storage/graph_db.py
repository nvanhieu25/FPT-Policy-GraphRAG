import os
from dotenv import load_dotenv

load_dotenv()

_neo4j_graph_instance = None


class Neo4jGraphWrapper:
    """Lightweight Neo4j wrapper that avoids heavy schema introspection.
    
    Uses the neo4j Python driver directly instead of LangChain's Neo4jGraph,
    which can hang during schema introspection.
    """
    
    def __init__(self, uri: str, username: str, password: str):
        from neo4j import GraphDatabase
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        # Verify connectivity
        self.driver.verify_connectivity()
    
    def query(self, cypher: str, params: dict = None) -> list[dict]:
        """Execute a Cypher query and return results as list of dicts."""
        with self.driver.session() as session:
            result = session.run(cypher, parameters=params or {})
            return [record.data() for record in result]
    
    def close(self):
        self.driver.close()


def get_neo4j_graph() -> Neo4jGraphWrapper:
    """Get a cached Neo4j graph instance."""
    global _neo4j_graph_instance
    if _neo4j_graph_instance is None:
        uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        username = os.environ.get("NEO4J_USERNAME", "neo4j")
        password = os.environ.get("NEO4J_PASSWORD", "password")
        _neo4j_graph_instance = Neo4jGraphWrapper(uri, username, password)
    return _neo4j_graph_instance


def get_neo4j_langchain_graph():
    """Get LangChain Neo4jGraph instance (for ingestion pipeline only).
    
    Warning: This can be slow due to schema introspection.
    """
    from langchain_community.graphs import Neo4jGraph
    return Neo4jGraph(
        url=os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
        username=os.environ.get("NEO4J_USERNAME", "neo4j"),
        password=os.environ.get("NEO4J_PASSWORD", "password"),
    )
