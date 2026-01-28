from agno.agent import Agent
from agno.models.perplexity import Perplexity
from agno.models.openai import OpenAIChat
from agno.models.groq import Groq
from agno.models.openrouter import OpenRouter
from agno.db.sqlite import SqliteDb
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb
from agno.document.reader.pdf_reader import PDFReader
from agno.document.reader.csv_reader import CSVReader
from agno.document.reader.text_reader import TextReader
from agno.document.chunking.recursive_character import RecursiveCharacterChunker

import os
import tempfile
from typing import List, Dict, Optional

# Use absolute path for .exe persistence
app_data = os.path.join(os.path.expanduser("~"), ".myapp")
os.makedirs(app_data, exist_ok=True)

# Local SQLite for memory/sessions (FREE)
db = SqliteDb(db_file=os.path.join(app_data, "memory.db"))

# Local LanceDB for knowledge (FREE)
LANCE_URI = os.path.join(app_data, "lancedb")
knowledge = Knowledge(
    vector_db=LanceDb(
        table_name="user_documents",
        uri=LANCE_URI,
    ),
    chunker=RecursiveCharacterChunker(chunk_size=1000, chunk_overlap=200),
)

# Use a FIXED user_id for single-user environment
USER_ID = "local_user"

# ============================================================================
# RAG SERVICE FUNCTIONS (LOCAL & FREE)
# ============================================================================

def ingest_files(files: List[Dict[str, any]]) -> bool:
    """
    Ingest files into the LOCAL vector database (FREE).
    
    Args:
        files: List of {"name": str, "data": bytes}
    
    Returns:
        bool: True if ingestion successful
    """
    all_docs = []
    
    for file_info in files:
        name = file_info["name"]
        data = file_info["data"]
        
        # Save to temp file to use Agno readers
        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=os.path.splitext(name)[1]
        ) as tmp:
            tmp.write(data)
            tmp_path = tmp.name

        try:
            # Select appropriate reader based on file extension
            if name.lower().endswith(".pdf"):
                reader = PDFReader()
                docs = reader.read(tmp_path)
            elif name.lower().endswith(".csv"):
                reader = CSVReader()
                docs = reader.read(tmp_path)
            elif name.lower().endswith((".txt", ".md", ".py", ".js", ".json")):
                reader = TextReader()
                docs = reader.read(tmp_path)
            else:
                print(f"Unsupported file type: {name}")
                continue
            
            # Add filename to metadata for tracking
            for doc in docs:
                doc.meta_data["filename"] = name
            
            all_docs.extend(docs)
            
        except Exception as e:
            print(f"Error processing {name}: {e}")
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    # Load documents into the knowledge base
    if all_docs:
        knowledge.load_documents(all_docs, upsert=True)
        print(f"✓ Successfully ingested {len(all_docs)} document chunks from {len(files)} files")
        return True
    
    print("⚠ No documents were ingested")
    return False


def ingest_text(text: str, source_name: str = "text_input") -> bool:
    """
    Ingest raw text directly into the LOCAL vector database (FREE).
    
    Args:
        text: Raw text content
        source_name: Identifier for the text source
    
    Returns:
        bool: True if ingestion successful
    """
    try:
        reader = TextReader()
        # Save text to temp file
        with tempfile.NamedTemporaryFile(
            mode='w', 
            delete=False, 
            suffix=".txt"
        ) as tmp:
            tmp.write(text)
            tmp_path = tmp.name
        
        try:
            docs = reader.read(tmp_path)
            for doc in docs:
                doc.meta_data["source"] = source_name
            
            knowledge.load_documents(docs, upsert=True)
            print(f"✓ Successfully ingested text from {source_name}")
            return True
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
    except Exception as e:
        print(f"Error ingesting text: {e}")
        return False


def clear_knowledge_base() -> bool:
    """
    Clear all documents from the LOCAL knowledge base (FREE).
    
    Returns:
        bool: True if cleared successfully
    """
    try:
        import lancedb
        db_conn = lancedb.connect(LANCE_URI)
        
        if "user_documents" in db_conn.table_names():
            db_conn.drop_table("user_documents")
            print("✓ Knowledge base cleared")
        
        # Re-initialize the table structure
        knowledge.vector_db.create()
        return True
        
    except Exception as e:
        print(f"Error clearing knowledge base: {e}")
        return False


def search_knowledge_base(query: str, limit: int = 5) -> List[Dict]:
    """
    Search the LOCAL knowledge base (FREE).
    
    Args:
        query: Search query
        limit: Maximum number of results
    
    Returns:
        List of relevant document chunks with metadata
    """
    try:
        results = knowledge.vector_db.search(query=query, limit=limit)
        return results
    except Exception as e:
        print(f"Error searching knowledge base: {e}")
        return []


def get_knowledge_stats() -> Dict:
    """
    Get statistics about the LOCAL knowledge base.
    
    Returns:
        Dict with stats (document count, etc.)
    """
    try:
        import lancedb
        db_conn = lancedb.connect(LANCE_URI)
        
        if "user_documents" in db_conn.table_names():
            table = db_conn.open_table("user_documents")
            count = table.count_rows()
            return {
                "total_chunks": count,
                "status": "active"
            }
        else:
            return {
                "total_chunks": 0,
                "status": "empty"
            }
    except Exception as e:
        print(f"Error getting knowledge stats: {e}")
        return {"total_chunks": 0, "status": "error"}


# ============================================================================
# MODEL & AGENT CONFIGURATION
# ============================================================================

def get_model(provider, api_key, model_id=None):
    """Factory function to return the correct Agno model instance."""
    if provider == "openai":
        return OpenAIChat(id=model_id or "gpt-4o", api_key=api_key)
    elif provider == "groq":
        return Groq(id=model_id or "llama-3.3-70b-versatile", api_key=api_key)
    elif provider == "openrouter":
        return OpenRouter(id=model_id or "openai/gpt-4o-mini", api_key=api_key)
    elif provider == "perplexity":
        return Perplexity(id=model_id or "sonar-pro", api_key=api_key)
    else:
        # Default fallback
        return Perplexity(id="sonar-pro", api_key=api_key)


def get_agent(
    provider="perplexity", 
    api_key=None, 
    model_id=None, 
    user_id=USER_ID,
    enable_rag=True
):
    """
    Returns a configured Agno Agent with the specified provider and key.
    RAG is enabled by default using LOCAL & FREE LanceDB vector store.
    
    Args:
        provider: Model provider (perplexity, openai, groq, openrouter)
        api_key: API key for the provider
        model_id: Specific model ID to use
        user_id: User identifier
        enable_rag: Enable RAG with local vector database
    
    Returns:
        Agent: Configured Agno agent
    """
    agent_config = {
        "model": get_model(provider, api_key, model_id),
        "session_id": "workspace_main_session",
        "markdown": True,
        "description": "You are a professional workspace assistant with access to uploaded documents.",
        "db": db,
        "enable_user_memories": True,
        "add_memories_to_context": True,
        "add_history_to_context": True,
        "num_history_runs": 5,
    }
    
    # Add LOCAL & FREE RAG capabilities
    if enable_rag:
        agent_config["knowledge"] = knowledge
        agent_config["search_knowledge"] = True
    
    return Agent(**agent_config)


# Legacy support for original function signature
def get_perplexity_agent(api_key, user_id=USER_ID):
    """Legacy function for backward compatibility."""
    return get_agent(provider="perplexity", api_key=api_key, user_id=user_id)
