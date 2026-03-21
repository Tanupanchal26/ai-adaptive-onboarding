# ⚙️ Complete Setup Guide

## Step 1 — Install Ollama
Download from https://ollama.com and install.
Then open a terminal and run:
```bash
ollama serve                  # keep this running in background
ollama pull llama3.2          # primary model (~2GB)
ollama pull phi4:mini         # fallback if llama3.2 gives bad JSON
```

## Step 2 — Python Environment
```bash
python -m venv venv
venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

## Step 3 — Run the App
```bash
streamlit run app.py
```
Open → http://localhost:8501

## Step 4 — Test Models (optional)
```bash
ollama run llama3.2
# type: Return JSON with skills: ["Python","SQL"] and exit
```

## Model Decision Guide
| Machine RAM | Use This Model |
|-------------|---------------|
| 8GB         | llama3.2:1b   |
| 16GB        | llama3.2:3b ✅ (default) |
| 32GB+       | mistral:7b    |

## Troubleshooting
- **Bad JSON from LLM** → app auto-retries with phi4:mini
- **Slow responses** → switch to `llama3.2:1b` in config.py
- **Ollama not found** → make sure `ollama serve` is running
- **Port conflict** → `ollama serve --port 11435` and update OLLAMA_URL in config.py
