import os
import threading
import json
import base64
from agents.workspace_agent import get_agent
from agents.rag_service import RagService
from agents.multi_agent import MultiAgentOrchestrator
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
        # Default provider and model
        self.current_provider = os.environ.get("DEFAULT_PROVIDER", "perplexity")
        self.current_model = os.environ.get("DEFAULT_MODEL", None)
        self.window = None
        self.rag_service = RagService()
        self.multi_agent_mode = False
        self.uploaded_filenames = []

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

    def set_model(self, model_id):
        self.current_model = model_id if model_id else None
        return f"Model set to {model_id if model_id else 'default'}"

    def toggle_multi_agent(self, enabled):
        self.multi_agent_mode = enabled
        return f"Multi-Agent mode: {'Enabled' if enabled else 'Disabled'}"

    def load_history(self):
        return get_history()

    def clear_rag_context(self):
        self.rag_service.clear_context()
        self.uploaded_filenames = []
        return "RAG context cleared"

    def upload_files(self, files_json):
        try:
            files_data = json.loads(files_json) if isinstance(files_json, str) else files_json
            processed_files = []
            for f in files_data:
                name = f["name"]
                content_b64 = f["content"]
                if "," in content_b64:
                    content_b64 = content_b64.split(",")[1]
                data = base64.b64decode(content_b64)
                processed_files.append({"name": name, "data": data})
                self.uploaded_filenames.append(name)
            
            success = self.rag_service.ingest_files(processed_files)
            if success:
                return {"status": "success", "files": list(set(self.uploaded_filenames))}
            return {"status": "error", "message": "Failed to ingest files"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def start_chat_stream(self, user_text, target_id=None):
        api_key = self.keys.get(self.current_provider)
        if not api_key:
            self.window.evaluate_js(f"receiveError('Please set your {self.current_provider.title()} API Key first.')")
            return
         
        if not target_id:
            save_msg("user", user_text)

        thread = threading.Thread(target=self._run_logic, args=(user_text, target_id))
        thread.daemon = True
        thread.start()

    def _run_logic(self, user_text, target_id):
        if self.multi_agent_mode:
            self._run_multi_agent(user_text, target_id)
        else:
            self._run_single_agent(user_text, target_id)

    def _run_single_agent(self, user_text, target_id):
        try:
            provider = self.current_provider
            api_key = self.keys.get(provider)
            model_id = self.current_model
            
            agent = get_agent(provider=provider, api_key=api_key, model_id=model_id, user_id="default_user")
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

    def _run_multi_agent(self, user_text, target_id):
        try:
            provider = self.current_provider
            api_key = self.keys.get(provider)
            orchestrator = MultiAgentOrchestrator(provider, api_key)
            
            if target_id:
                self.window.evaluate_js(f"clearBubble('{target_id}')")
            else:
                target_id = 'multi-' + str(threading.get_ident())
                self.window.evaluate_js(f"createBotBubble('{target_id}')")

            full_history_text = ""
            for step in orchestrator.run_cycle(user_text):
                role = step["role"]
                content = step["content"]
                formatted_step = f"\n\n**[{role}]**\n{content}"
                full_history_text += formatted_step
                self.window.evaluate_js(f"receiveChunk({json.dumps(formatted_step)}, '{target_id}')")
            
            save_msg("bot", full_history_text)
            self.window.evaluate_js("streamComplete()")
        except Exception as e:
            self.window.evaluate_js(f"receiveError({json.dumps(str(e))})")
