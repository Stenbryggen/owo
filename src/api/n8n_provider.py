import json
import urllib.request

from src.owo.core.ai_provider import AIProvider  # noqa: F401 - documents the contract satisfied


class N8nAIProvider:
    """Calls an n8n webhook that internally routes to whichever LLM (Hermes,
    Claude, GPT, a local model...) the workflow is configured with. The
    simulation core never knows which model answered, or that n8n is even
    involved - it only ever talks to the AIProvider interface (see
    src/owo/core/ai_provider.py). Selected via config["ai_provider"] = "n8n"
    and config["n8n_webhook_url"].

    Expected webhook contract: POST {"type": "npc_decision"|"content",
    "context"|"request": {...}} -> JSON body used as the return value as-is.
    """

    def __init__(self, webhook_url: str, timeout: float = 10.0):
        self._webhook_url = webhook_url
        self._timeout = timeout

    def _post(self, payload: dict) -> dict:
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self._webhook_url, data=data, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(request, timeout=self._timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def generate_npc_decision(self, context: dict) -> dict:
        return self._post({"type": "npc_decision", "context": context})

    def generate_content(self, request: dict) -> dict:
        return self._post({"type": "content", "request": request})
