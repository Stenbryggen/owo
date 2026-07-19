from typing import Callable, Dict, Protocol


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


_PROVIDERS: Dict[str, Callable[[], AIProvider]] = {
    "stub": StubAIProvider,
}


def get_provider(name: str) -> AIProvider:
    try:
        provider_cls = _PROVIDERS[name]
    except KeyError:
        raise ValueError(f"Unknown AI provider: {name!r}")
    return provider_cls()
