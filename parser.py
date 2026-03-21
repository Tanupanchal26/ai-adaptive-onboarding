import os, warnings, logging
os.environ["TRANSFORMERS_VERBOSITY"]       = "error"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"]        = "false"
warnings.filterwarnings("ignore")
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

import fitz  # PyMuPDF
import json
import urllib.request
import urllib.error
from config import PRIMARY_MODEL, FALLBACK_MODEL, OLLAMA_URL, REQUEST_TIMEOUT

# ── OpenAI client (optional — graceful if not installed / no key) ─────────────
try:
    from openai import OpenAI as _OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

def _get_openai_key() -> str | None:
    """Try Streamlit secrets first, then env var."""
    try:
        import streamlit as st
        key = st.secrets.get("OPENAI_API_KEY", "")
        if key and not key.startswith("sk-your"):
            return key
    except Exception:
        pass
    key = os.getenv("OPENAI_API_KEY", "")
    return key if (key and not key.startswith("sk-your")) else None

# ── JSON schema for extraction (used by both resume + JD) ────────────────────
_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "skills":           {"type": "array",  "items": {"type": "string"}},
        "experience_years": {"type": ["number", "null"]},
        "main_role":        {"type": "string"},
        "education_level":  {"type": "string"},
        "certifications":   {"type": "array",  "items": {"type": "string"}},
    },
    "required": ["skills", "main_role"],
    "additionalProperties": False
}

# ── OpenAI extraction ─────────────────────────────────────────────────────────
def _call_openai(text: str) -> dict:
    key = _get_openai_key()
    if not key:
        raise ValueError("No OpenAI API key configured")
    client = _OpenAI(api_key=key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise resume and job description parser. "
                    "Extract skills, experience years, main role, education level, and certifications. "
                    "Return ONLY valid JSON matching the schema. No extra text."
                )
            },
            {
                "role": "user",
                "content": f"Extract from this text:\n\n{text[:12000]}\n\nOutput only JSON."
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "skill_extraction",
                "strict": True,
                "schema": _EXTRACTION_SCHEMA
            }
        },
        temperature=0.0,
        max_tokens=600
    )
    result = json.loads(response.choices[0].message.content)
    result["_model_used"] = "gpt-4o-mini"
    return result

# ── Ollama fallback ───────────────────────────────────────────────────────────
_OLLAMA_PROMPT = """
Extract technical & soft skills, experience years, and main role from the text below.
Return ONLY this JSON, no explanation, no markdown:

{{
  "skills": ["Python", "SQL"],
  "experience_years": 4,
  "main_role": "Software Engineer",
  "education_level": "Bachelor's",
  "certifications": []
}}

Text:
{text}
"""

def _call_ollama(text: str) -> dict:
    for model in (PRIMARY_MODEL, FALLBACK_MODEL):
        try:
            payload = json.dumps({
                "model":  model,
                "system": "You are a precise parser. Return ONLY valid JSON, nothing else.",
                "prompt": _OLLAMA_PROMPT.format(text=text[:3000]),
                "stream": False
            }).encode("utf-8")
            req = urllib.request.Request(
                OLLAMA_URL, data=payload,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                raw = json.loads(resp.read().decode()).get("response", "")
                s, e = raw.find("{"), raw.rfind("}") + 1
                if s == -1 or e <= s:
                    raise ValueError("No JSON in response")
                result = json.loads(raw[s:e])
                result["_model_used"] = model
                return result
        except urllib.error.URLError:
            return {"error": "Ollama not running — start with: ollama serve"}
        except (json.JSONDecodeError, ValueError):
            continue
        except Exception as ex:
            return {"error": str(ex)}
    return {"error": f"Both {PRIMARY_MODEL} and {FALLBACK_MODEL} returned invalid JSON"}

# ── Fuzzy skill matching ──────────────────────────────────────────────────────
try:
    from sentence_transformers import SentenceTransformer, util
    _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False

def fuzzy_match_skills(raw_skills: list, standard_skills: set, threshold: float = 0.65) -> set:
    if not FUZZY_AVAILABLE:
        std_lower = {s.lower(): s for s in standard_skills}
        return {std_lower[s.lower()] for s in raw_skills if s.lower() in std_lower}
    std_list = list(standard_skills)
    matched = set()
    raw_emb = _embedder.encode(raw_skills, convert_to_tensor=True)
    std_emb = _embedder.encode(std_list,   convert_to_tensor=True)
    for i in range(len(raw_skills)):
        scores  = util.cos_sim(raw_emb[i], std_emb)[0]
        best    = int(scores.argmax())
        if float(scores[best]) >= threshold:
            matched.add(std_list[best])
    return matched

# ── Text extraction ───────────────────────────────────────────────────────────
def extract_text(file_bytes: bytes, filename: str) -> str:
    try:
        if filename.lower().endswith(".pdf"):
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            return "\n".join(page.get_text() for page in doc)
        return file_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return ""

# ── Public API ────────────────────────────────────────────────────────────────
def parse_file(file_bytes: bytes, filename: str) -> dict:
    """Extract text → OpenAI (if key set) → Ollama fallback → return structured data."""
    text = extract_text(file_bytes, filename)
    if not text.strip():
        return {"error": "Could not extract text from file"}

    # Try OpenAI first
    if OPENAI_AVAILABLE:
        try:
            result = _call_openai(text)
            result["_raw_text"] = text[:500]
            return result
        except ValueError:
            pass  # no key → fall through to Ollama
        except Exception as e:
            # API error → fall through to Ollama
            pass

    # Ollama fallback
    result = _call_ollama(text)
    if "error" not in result:
        result["_raw_text"] = text[:500]
    return result
