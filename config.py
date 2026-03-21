# ── Model Configuration ───────────────────────────────────────────────────────
# Primary: llama3.2:3b — fast, reliable JSON, good instruction following
# Fallback: phi4:mini   — if llama3.2 gives bad JSON
# Heavy:    mistral:7b  — only if you have 16GB+ RAM

PRIMARY_MODEL  = "llama3.2"
FALLBACK_MODEL = "phi4:mini"
OLLAMA_URL     = "http://localhost:11434/api/generate"
REQUEST_TIMEOUT = 60  # seconds — increase to 120 on slow machines
