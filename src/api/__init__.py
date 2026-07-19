"""HTTP/webhook contract that lets an external AI workflow (e.g. n8n) drive
NPC decisions and content generation through AIProvider. See
n8n_provider.py for the client, and src/owo/core/ai_provider.py for the
interface it satisfies (selected via config["ai_provider"] = "n8n").
"""
