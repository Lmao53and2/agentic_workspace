import os
import threading
import json
from agents.workspace_agent import get_perplexity_agent
from database import save_msg, get_history

class ApiBridge:
    def __init__(self):
        self._api_key = os.environ.get("PERPLEXITY_API_KEY")
        self.window = None

    def set_window(self, window):
        self.window = window

    def set_api_key(self, key):
        self._api_key = key
        os.environ["PERPLEXITY_API_KEY"] = key
        return "Key saved"

    def load_history(self):
        return get_history()

    def start_chat_stream(self, user_text, target_id=None):
        if not self._api_key:
            self.window.evaluate_js("receiveError('Please set your API Key first.')")
            return
         
        if not target_id:
            save_msg("user", user_text)

        thread = threading.Thread(target=self._run_agent, args=(user_text, target_id))
        thread.daemon = True
        thread.start()

    def _run_agent(self, user_text, target_id):
        try:
            agent = get_perplexity_agent(self._api_key, user_id="default_user")
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
