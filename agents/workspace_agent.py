from agno.agent import Agent
from agno.models.perplexity import Perplexity
from agno.db.sqlite import SqliteDb
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb

# Use absolute path for .exe persistence
import os
app_data = os.path.join(os.path.expanduser("~"), ".myapp")
os.makedirs(app_data, exist_ok=True)

# Local SQLite for memory/sessions
db = SqliteDb(db_file=os.path.join(app_data, "memory.db"))

# Local LanceDB for knowledge (no server needed)
knowledge = Knowledge(
    vector_db=LanceDb(
        table_name="user_documents",
        uri=os.path.join(app_data, "lancedb"),
    ),
)

# Add user files (CSV or PDF)
# knowledge.add_content(path="path/to/file.csv")  # or .pdf

# Use a FIXED user_id for your single-user .exe
USER_ID = "local_user"

def get_perplexity_agent(api_key, user_id=USER_ID):
    return Agent(
        model=Perplexity(id="sonar-pro", api_key=api_key),
        session_id="workspace_main_session",
        markdown=True,
        description="You are a professional workspace assistant.",
        # Local memory with SQLite
        db=db,
        enable_user_memories=True,
        add_memories_to_context=True,  # Ensures memories are loaded
        # ADD THIS to load chat history into context:
        add_history_to_context=True,
        num_history_runs=5,  # Optional: limit how many past turns to include
        # Local knowledge with LanceDB
        knowledge=knowledge,
        search_knowledge=True,
    )
