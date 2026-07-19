from typing import Protocol


class AIProvider(Protocol):
    """Everything the simulation needs from an AI backend. The core only ever
    talks to this interface, never to a concrete SDK or workflow tool."""

    def generate_npc_decision(self, context: dict) -> dict: ...
    def generate_content(self, request: dict) -> dict: ...


class StubAIProvider:
    """Deterministic, network-free provider. Lets the rest of the system be
    built and tested without a real AI backend (e.g. n8n) running."""

    def generate_npc_decision(self, context: dict) -> dict:
        return {"action": "idle", "context": context}

    def generate_content(self, request: dict) -> dict:
        return {"status": "not_implemented", "request": request}


def get_provider(config: dict) -> AIProvider:
    """Picks the AIProvider implementation named by config["ai_provider"].
    New providers are added as new files (e.g. src/api/n8n_provider.py) and
    a new branch here - the rest of the simulation never changes."""
    name = config.get("ai_provider", "stub")

    if name == "stub":
        return StubAIProvider()

    if name == "n8n":
        from src.api.n8n_provider import N8nAIProvider

        return N8nAIProvider(webhook_url=config["n8n_webhook_url"])

    raise ValueError(f"Unknown AI provider: {name!r}")
