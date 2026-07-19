import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from src.api.n8n_provider import N8nAIProvider
from src.owo.core.ai_provider import get_provider


class _FakeN8nHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers["Content-Length"])
        body = json.loads(self.rfile.read(length))

        response = {"action": "echo", "received_type": body["type"]}
        payload = json.dumps(response).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass  # keep test output quiet


@pytest.fixture
def fake_webhook():
    server = HTTPServer(("127.0.0.1", 0), _FakeN8nHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/webhook/owo-ai"
    finally:
        server.shutdown()
        thread.join()


def test_generate_npc_decision_posts_context_and_parses_response(fake_webhook):
    provider = N8nAIProvider(webhook_url=fake_webhook)

    result = provider.generate_npc_decision({"entity": "Birk"})

    assert result == {"action": "echo", "received_type": "npc_decision"}


def test_generate_content_posts_request_and_parses_response(fake_webhook):
    provider = N8nAIProvider(webhook_url=fake_webhook)

    result = provider.generate_content({"kind": "quest"})

    assert result == {"action": "echo", "received_type": "content"}


def test_get_provider_dispatches_to_n8n_by_config():
    provider = get_provider({"ai_provider": "n8n", "n8n_webhook_url": "http://example.invalid"})
    assert isinstance(provider, N8nAIProvider)
