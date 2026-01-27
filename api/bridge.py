import os
import threading
import json
from agents.workspace_agent import get_agent
from database import save_msg, get_history

class ApiBridge:
    def __init__(self):
        # Load keys from environment
        self.keys = {
            "openai": os.environ.get("OPENAI_API_KEY"),
            "groq": os.environ.get("GROQ_API_KEY"),
            "openrouter": os.environ.get("OPENROUTER_API_KEY"),
            "perplexity": os.environ.get("PERPLEXITY_API_KEY")
        }
        # Default provider
        self.current_provider = os.environ.get("DEFAULT_PROVIDER", "perplexity")
        self.window = None

    def set_window(self, window):
        self.window = window

    def set_api_key(self, key, provider="perplexity"):
        self.keys[provider] = key
        env_var = f"{provider.upper()}_API_KEY"
        os.environ[env_var] = key
        return f"{provider.title()} key saved"

    def set_provider(self, provider):
        if provider in self.keys:
            self.current_provider = provider
            return f"Provider switched to {provider}"
        return "Invalid provider"

    def load_history(self):
        return get_history()

    def start_chat_stream(self, user_text, target_id=None):
        api_key = self.keys.get(self.current_provider)
        if not api_key:
            self.window.evaluate_js(f"receiveError('Please set your {self.current_provider.title()} API Key first.')")
            return
         
        if not target_id:
            save_msg("user", user_text)

        thread = threading.Thread(target=self._run_agent, args=(user_text, target_id))
        thread.daemon = True
        thread.start()

    def _run_agent(self, user_text, target_id):
        try:
            provider = self.current_provider
            api_key = self.keys.get(provider)
            
            agent = get_agent(provider=provider, api_key=api_key, user_id="default_user")
            full_response = ""
            run_response = agent.run(user_text, stream=True)
            
            if target_id:
                self.window.evaluate_js(f"clearBubble('{target_id}')")

            for chunk in run_response:
                content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                if content:
                    full_response += content
                    self.window.evaluate_js(f"receiveChunk({json.dumps(content)}, '{target_id or ''}')")

            save_msg("bot", full_response)
            self.window.evaluate_js("streamComplete()")
        except Exception as e:
            self.window.evaluate_js(f"receiveError({json.dumps(str(e))})")
