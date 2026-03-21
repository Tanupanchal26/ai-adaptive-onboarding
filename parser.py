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

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import pytesseract
    from pdf2image import convert_from_bytes
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

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
        for attempt in range(2):   # retry once on bad JSON
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
                    if "skills" not in result or "main_role" not in result:
                        raise ValueError("Missing required fields")
                    result["_model_used"] = model
                    return result
            except urllib.error.URLError:
                return _regex_fallback(text)   # Ollama not running → regex parse
            except (json.JSONDecodeError, ValueError):
                continue
            except Exception:
                return _regex_fallback(text)
    return _regex_fallback(text)


# ── Regex fallback — works with zero LLM, zero internet ──────────────────────
_KNOWN_SKILLS = [
    "Python", "SQL", "JavaScript", "Java", "React", "AWS", "Docker", "Git",
    "Agile", "Machine Learning", "Data Analysis", "Tableau", "Power BI",
    "Leadership", "Communication", "Excel", "Marketing", "Sales", "CRM",
    "Public Speaking", "Project Management", "HTML", "CSS", "Node.js",
    "TypeScript", "Kubernetes", "Azure", "GCP", "Terraform", "Linux",
    "MongoDB", "PostgreSQL", "Redis", "Spark", "Hadoop", "Tableau",
    "SEO", "Content Marketing", "Brand Management", "Negotiation",
    "Recruitment", "Training", "Coaching", "Strategy", "HR",
    "Safety Compliance", "Quality Control", "Supply Chain",
    "Documentation", "Time Management", "Troubleshooting",
    "Equipment Maintenance", "Inventory Management", "Forklift Operation",
    "Scrum", "Kanban", "JIRA", "Confluence", "Figma", "Photoshop",
    "Deep Learning", "NLP", "Computer Vision", "PyTorch", "TensorFlow",
    "scikit-learn", "Pandas", "NumPy", "R", "MATLAB", "C++", "C#", "Go",
    "Ruby", "PHP", "Swift", "Kotlin", "Flutter", "Django", "FastAPI",
    "Flask", "Spring Boot", "Microservices", "REST API", "GraphQL",
    "System Design", "DevOps", "CI/CD", "Jenkins", "GitHub Actions",
]

_ROLE_PATTERNS = [
    r"(?:current(?:ly)?\s+(?:working\s+as|role[:\s]+)|position[:\s]+|title[:\s]+|job\s+title[:\s]+)([\w\s]+)",
    r"(?:senior|junior|lead|principal|staff)?\s*(?:software|data|ml|ai|product|project|sales|marketing|hr|field|warehouse)\s*(?:engineer|developer|manager|analyst|scientist|executive|associate|technician|lead|specialist)",
]

def _regex_fallback(text: str) -> dict:
    """Extract skills and role from raw text using keyword matching — no LLM needed."""
    import re
    text_lower = text.lower()

    # Skill extraction — case-insensitive keyword scan
    found_skills = [
        skill for skill in _KNOWN_SKILLS
        if re.search(r'\b' + re.escape(skill.lower()) + r'\b', text_lower)
    ]

    # Role extraction
    main_role = "Professional"
    for pattern in _ROLE_PATTERNS:
        m = re.search(pattern, text_lower)
        if m:
            main_role = m.group(0).strip().title()
            break

    # Experience years
    exp_match = re.search(r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)', text_lower)
    experience_years = int(exp_match.group(1)) if exp_match else 0

    return {
        "skills":           found_skills if found_skills else ["Communication"],
        "experience_years": experience_years,
        "main_role":        main_role,
        "education_level":  "",
        "certifications":   [],
        "_model_used":      "regex-fallback"
    }

# ── Fuzzy skill matching ──────────────────────────────────────────────────────
# Thin shim — delegates to semantic_engine (single shared model instance).
def fuzzy_match_skills(raw_skills: list, standard_skills: set, threshold: float = 0.65) -> set:
    from semantic_engine import normalize_to_taxonomy
    return normalize_to_taxonomy(raw_skills, standard_skills, threshold)

# ── Text extraction ───────────────────────────────────────────────────────────
def _extract_pdf(file_bytes: bytes) -> str:
    """Try PyMuPDF → pdfplumber → OCR. Raises ValueError if password-protected."""
    import io

    # 1. PyMuPDF — try multiple text extraction modes
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        if doc.is_encrypted:
            raise ValueError("PDF is password-protected")
        # try plain text first, then blocks mode for complex layouts
        for mode in ("text", "blocks"):
            try:
                parts = []
                for page in doc:
                    raw = page.get_text(mode)
                    if isinstance(raw, list):   # blocks returns list of tuples
                        parts.append(" ".join(str(b[4]) for b in raw if len(b) > 4))
                    else:
                        parts.append(raw)
                text = "\n".join(parts)
                if text.strip():
                    return text
            except Exception:
                continue
    except ValueError:
        raise
    except Exception:
        pass

    # 2. pdfplumber fallback
    if PDFPLUMBER_AVAILABLE:
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                text = "\n".join(p.extract_text() or "" for p in pdf.pages)
            if text.strip():
                return text
        except Exception:
            pass

    # 3. OCR fallback for scanned PDFs
    if OCR_AVAILABLE:
        try:
            images = convert_from_bytes(file_bytes)
            return "\n".join(pytesseract.image_to_string(img) for img in images)
        except Exception:
            pass

    return ""


def extract_text(file_bytes: bytes, filename: str) -> str:
    fname = filename.lower()
    try:
        if fname.endswith(".pdf"):
            return _extract_pdf(file_bytes)
        if fname.endswith(".docx"):
            if not DOCX_AVAILABLE:
                return file_bytes.decode("utf-8", errors="ignore")
            import io
            doc = DocxDocument(io.BytesIO(file_bytes))
            return "\n".join(p.text for p in doc.paragraphs)
        # Plain text / TXT
        return file_bytes.decode("utf-8", errors="ignore")
    except ValueError as e:
        return f"__ERROR__: {e}"
    except Exception:
        return ""

# ── Public API ────────────────────────────────────────────────────────────────
def parse_file(file_bytes: bytes, filename: str) -> dict:
    """Extract text → OpenAI (if key set) → Ollama fallback → return structured data."""
    text = extract_text(file_bytes, filename)
    if text.startswith("__ERROR__:"):
        return {"error": text.replace("__ERROR__: ", "")}
    if not text.strip():
        # Last resort: try decoding raw bytes and regex-scanning for skills
        raw = file_bytes.decode("utf-8", errors="ignore")
        if raw.strip():
            result = _regex_fallback(raw)
            result["_raw_text"] = raw[:500]
            return result
        return {"error": "Could not extract text from file. Ensure the file is a valid, non-encrypted PDF, DOCX, or TXT."}

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

    # Ollama fallback → regex fallback if Ollama unavailable
    result = _call_ollama(text)
    result["_raw_text"] = text[:500]
    return result
