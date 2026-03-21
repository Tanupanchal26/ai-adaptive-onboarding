import os, warnings, logging
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
warnings.filterwarnings("ignore")
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)

import fitz  # PyMuPDF
import json
import urllib.request
import urllib.error
from config import PRIMARY_MODEL, FALLBACK_MODEL, OLLAMA_URL, REQUEST_TIMEOUT

# ── Prompts ───────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a precise resume parser. Return ONLY valid JSON, nothing else."""

EXTRACTION_PROMPT_TEMPLATE = """
Extract technical & soft skills mentioned in the following text.
Also estimate total relevant experience years and guessed main role.

Return ONLY this JSON structure, no explanation, no markdown:

{{
  "skills": ["Python", "SQL", "Team Leadership"],
  "experience_years": 4,
  "main_role": "Software Engineer",
  "education_level": "Bachelor's"
}}

Text:
{text}
"""

# ── Fuzzy matching (stretch — hour 11+) ──────────────────────────────────────
try:
    from sentence_transformers import SentenceTransformer, util
    _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False


def fuzzy_match_skills(raw_skills: list, standard_skills: set, threshold: float = 0.65) -> set:
    """
    Use cosine similarity to match raw skills to standard taxonomy.
    Falls back to exact lowercase match if sentence-transformers not available.
    """
    if not FUZZY_AVAILABLE:
        std_lower = {s.lower(): s for s in standard_skills}
        return {std_lower[s.lower()] for s in raw_skills if s.lower() in std_lower}

    std_list = list(standard_skills)
    matched = set()
    raw_embeddings = _embedder.encode(raw_skills,  convert_to_tensor=True)
    std_embeddings = _embedder.encode(std_list,    convert_to_tensor=True)

    for i, raw in enumerate(raw_skills):
        scores = util.cos_sim(raw_embeddings[i], std_embeddings)[0]
        best_idx = int(scores.argmax())
        if float(scores[best_idx]) >= threshold:
            matched.add(std_list[best_idx])

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


# ── Ollama call ───────────────────────────────────────────────────────────────
def _call_model(text: str, model: str) -> dict:
    prompt = EXTRACTION_PROMPT_TEMPLATE.format(text=text[:3000])
    payload = json.dumps({
        "model":  model,
        "system": SYSTEM_PROMPT,
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
            raise ValueError("No JSON block in response")
        return json.loads(raw[start:end])


def call_ollama(text: str) -> dict:
    """Try PRIMARY_MODEL, fall back to FALLBACK_MODEL on bad JSON."""
    for model in (PRIMARY_MODEL, FALLBACK_MODEL):
        try:
            result = _call_model(text, model)
            result["_model_used"] = model
            return result
        except urllib.error.URLError:
            return {"error": "Ollama not running — start with: ollama serve"}
        except (json.JSONDecodeError, ValueError):
            continue
        except Exception as e:
            return {"error": str(e)}
    return {"error": f"Both {PRIMARY_MODEL} and {FALLBACK_MODEL} returned invalid JSON"}


# ── Public API ────────────────────────────────────────────────────────────────
def parse_file(file_bytes: bytes, filename: str) -> dict:
    """Extract text → call LLM → return structured skill data."""
    text = extract_text(file_bytes, filename)
    if not text.strip():
        return {"error": "Could not extract text from file"}
    result = call_ollama(text)
    if "error" not in result:
        result["_raw_text"] = text[:500]
    return result
