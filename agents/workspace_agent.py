from agno.agent import Agent
from agno.models.perplexity import Perplexity
from agno.models.openai import OpenAIChat
from agno.models.groq import Groq
from agno.models.openrouter import OpenRouter
from agno.db.sqlite import SqliteDb
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb

# Use absolute path for .exe persistence
import os
app_data = os.path.join(os.path.expanduser("~"), ".myapp")
os.makedirs(app_data, exist_ok=True)

# Local SQLite for memory/sessions
db = SqliteDb(db_file=os.path.join(app_data, "memory.db"))

# Local LanceDB for knowledge
knowledge = Knowledge(
    vector_db=LanceDb(
        table_name="user_documents",
        uri=os.path.join(app_data, "lancedb"),
    ),
)

# Use a FIXED user_id for single-user environment
USER_ID = "local_user"

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

def get_agent(provider="perplexity", api_key=None, model_id=None, user_id=USER_ID):
    """Returns a configured Agno Agent with the specified provider and key."""
    return Agent(
        model=get_model(provider, api_key, model_id),
        session_id="workspace_main_session",
        markdown=True,
        description="You are a professional workspace assistant.",
        db=db,
        enable_user_memories=True,
        add_memories_to_context=True,
        add_history_to_context=True,
        num_history_runs=5,
        knowledge=knowledge,
        search_knowledge=True,
    )

# Legacy support for original function signature
def get_perplexity_agent(api_key, user_id=USER_ID):
    return get_agent(provider="perplexity", api_key=api_key, user_id=user_id)
