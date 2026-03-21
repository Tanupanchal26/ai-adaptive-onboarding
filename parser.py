import fitz  # PyMuPDF
import json
import urllib.request
import urllib.error

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"

PROMPT_TEMPLATE = """Extract skills and experience from the text below. Return ONLY valid JSON, no explanation:
{{
  "skills": ["Python", "Leadership", "SQL"],
  "experience_years": 3,
  "role": "Software Engineer"
}}
Skills must be exact words only.

TEXT:
{text}
"""


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Extract text from PDF or TXT bytes."""
    try:
        if filename.lower().endswith(".pdf"):
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            return "\n".join(page.get_text() for page in doc)
        else:
            return file_bytes.decode("utf-8", errors="ignore")
    except Exception as e:
        return ""


def call_ollama(text: str) -> dict:
    """Send text to Ollama and return parsed JSON."""
    prompt = PROMPT_TEMPLATE.format(text=text[:3000])
    payload = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            OLLAMA_URL,
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode())
            raw = result.get("response", "")
            # Extract JSON block from response
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(raw[start:end])
    except urllib.error.URLError:
        return {"error": "Ollama not running. Start with: ollama serve"}
    except json.JSONDecodeError:
        return {"error": "LLM returned invalid JSON"}
    except Exception as e:
        return {"error": str(e)}

    return {"error": "No response from Ollama"}


def parse_file(file_bytes: bytes, filename: str) -> dict:
    """Full pipeline: extract text → call LLM → return structured data."""
    text = extract_text(file_bytes, filename)
    if not text.strip():
        return {"error": "Could not extract text from file"}
    result = call_ollama(text)
    result["_raw_text"] = text[:500]  # preview only
    return result
