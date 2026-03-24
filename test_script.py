from langchain_community.graphs import Neo4jGraph
graph = Neo4jGraph()

print("=== CHECKING GRAPH DATA ===")
labels_query = "MATCH (n) UNWIND labels(n) as label RETURN label, count(*) as count ORDER BY count DESC LIMIT 10"
for r in graph.query(labels_query): print(f"- {r['label']}: {r['count']}")

print("---")
rels_query = "MATCH ()-[r]->() RETURN type(r) as relationship_type, count(*) as count ORDER BY count DESC LIMIT 10"
for r in graph.query(rels_query): print(f"- {r['relationship_type']}: {r['count']}")
