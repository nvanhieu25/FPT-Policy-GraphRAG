import os
import glob
import fitz  # PyMuPDF
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.graph_transformers import LLMGraphTransformer

from src.services.llm import get_llm_model
from src.storage.vector_db import ensure_collection, get_qdrant_client, ingest_documents_qdrant
from src.storage.graph_db import get_neo4j_langchain_graph

DATA_DIR = "./data/raw"

def parse_pdfs(data_dir=DATA_DIR) -> list[Document]:
    """Parse PDFs from the data directory using PyMuPDF."""
    pdf_files = glob.glob(os.path.join(data_dir, "*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {data_dir}. Please add compliance documents.")
        return []

    documents = []
    for pdf_path in pdf_files:
        print(f"Parsing: {pdf_path}")
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text() + "\n"
            
            # Create a LangChain Document
            documents.append(Document(page_content=text, metadata={"source": os.path.basename(pdf_path)}))
        except Exception as e:
            print(f"Failed to parse {pdf_path}: {e}")

    return documents

def build_vector_db(documents: list[Document]):
    """Chunk documents and store in Qdrant Vector DB."""
    if not documents:
        return

    print("Splitting documents for Vector Search...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Generated {len(chunks)} chunks.")

    print("Connecting to Qdrant and ensuring collection bounds...")
    client = get_qdrant_client()
    ensure_collection(client)

    print("Ingesting into Qdrant...")
    ingest_documents_qdrant(chunks)
    print("Vector DB ingestion complete.")
    return chunks

def build_graph_db(chunks: list[Document]):
    """Extract nodes and relationships using LLM and store in Neo4j."""
    if not chunks:
        return

    print("Connecting to Neo4j...")
    try:
        graph = get_neo4j_langchain_graph()
    except Exception as e:
        print(f"Failed to connect to Neo4j: {e}")
        return

    print("Extracting Graph structures...")
    llm = get_llm_model()
    
    # Restrict the graph transformer to specific nodes and relationships as requested
    allowed_nodes = ["Policy", "Department", "Role", "Concept", "Employee"]
    allowed_relationships = [
        "REPORTS_TO", "REQUIRES_APPROVAL_FROM", "GOVERNS", 
        "BELONGS_TO", "DEFINES", "RELATES_TO", "APPLIES_TO"
    ]
    
    llm_transformer = LLMGraphTransformer(
        llm=llm,
        allowed_nodes=allowed_nodes,
        allowed_relationships=allowed_relationships
    )

    try:
        graph_documents = llm_transformer.convert_to_graph_documents(chunks)
        print(f"Extracted {len(graph_documents)} graph documents. Adding to Neo4j...")
        
        # Add to neo4j
        graph.add_graph_documents(
            graph_documents, 
            baseEntityLabel=True, 
            include_source=True
        )
        print("Graph DB ingestion complete.")
    except Exception as e:
        print(f"Error during Graph extraction/ingestion: {e}")

if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    docs = parse_pdfs()
    if docs:
        chunks = build_vector_db(docs)
        if chunks:
            build_graph_db(chunks)
    else:
        print(f"Please place your PDF files in the '{DATA_DIR}' directory and run again.")
