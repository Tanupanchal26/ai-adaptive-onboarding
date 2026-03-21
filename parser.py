import fitz  # PyMuPDF
import json
import urllib.request
import urllib.error
from config import PRIMARY_MODEL, FALLBACK_MODEL, OLLAMA_URL, REQUEST_TIMEOUT

# Strict prompt — works reliably with llama3.2 and phi4:mini
PROMPT_TEMPLATE = """Extract skills and experience from the text below.
Return ONLY valid JSON, no explanation, no markdown, no extra text:
{{
  "skills": ["Python", "Leadership", "SQL"],
  "experience_years": 3,
  "role": "Software Engineer"
}}
Skills must be exact words only. Do not add any text outside the JSON.

TEXT:
{text}
"""


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Extract text from PDF or TXT bytes."""
    try:
        if filename.lower().endswith(".pdf"):
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            return "\n".join(page.get_text() for page in doc)
        return file_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _call_model(prompt: str, model: str) -> dict:
    """Send prompt to a specific Ollama model, return parsed JSON or raise."""
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False
    }).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        raw = json.loads(resp.read().decode()).get("response", "")
        start, end = raw.find("{"), raw.rfind("}") + 1
        if start == -1 or end <= start:
            raise ValueError("No JSON block found in response")
        return json.loads(raw[start:end])


def call_ollama(text: str) -> dict:
    """
    Try PRIMARY_MODEL first; fall back to FALLBACK_MODEL on bad JSON.
    Returns parsed dict or error dict.
    """
    prompt = PROMPT_TEMPLATE.format(text=text[:3000])

    for model in (PRIMARY_MODEL, FALLBACK_MODEL):
        try:
            result = _call_model(prompt, model)
            result["_model_used"] = model
            return result
        except urllib.error.URLError:
            return {"error": "Ollama not running. Start with: ollama serve"}
        except (json.JSONDecodeError, ValueError):
            continue  # try fallback
        except Exception as e:
            return {"error": str(e)}

    return {"error": f"Both {PRIMARY_MODEL} and {FALLBACK_MODEL} returned invalid JSON. Try: ollama pull {PRIMARY_MODEL}"}


def parse_file(file_bytes: bytes, filename: str) -> dict:
    """Full pipeline: extract text → call LLM → return structured data."""
    text = extract_text(file_bytes, filename)
    if not text.strip():
        return {"error": "Could not extract text from file"}
    result = call_ollama(text)
    result["_raw_text"] = text[:500]
    return result
