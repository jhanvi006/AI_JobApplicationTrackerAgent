"""
utils.py — Data storage, file parsing, and helper functions
for the AI Job Application Assistant.
"""

import json
import os
import io

# ---------------------------------------------------------------------------
# Data Schema
# ---------------------------------------------------------------------------

EMPTY_SCHEMA = {
    "original_profile": "",
    "current_profile_state": {
        "strengths": [],
        "weaknesses": [],
        "skills": [],
        "experience": [],
        "improvement_areas": []
    },
    "applications": [],
    "global_insights": ""
}

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/output.json")

# ---------------------------------------------------------------------------
# JSON Persistence
# ---------------------------------------------------------------------------

def get_empty_schema() -> dict:
    """Return a deep copy of the empty data schema."""
    return json.loads(json.dumps(EMPTY_SCHEMA))


def load_data() -> dict:
    """Load data from data.json. Create with empty schema if missing."""
    if not os.path.exists(DATA_FILE):
        save_data(get_empty_schema())
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        data = get_empty_schema()
        save_data(data)
    return data


def save_data(data: dict) -> None:
    """Atomically write data to data.json."""
    tmp_path = DATA_FILE + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    # Atomic replace (Windows: os.replace is atomic on same volume)
    os.replace(tmp_path, DATA_FILE)


# ---------------------------------------------------------------------------
# File Parsers
# ---------------------------------------------------------------------------

def parse_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF using pdfplumber."""
    import pdfplumber
    text_parts = []
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
    except Exception:
        # If pdfplumber fails, try to decode as plain text
        return file_bytes.decode("utf-8", errors="replace")
    return "\n\n".join(text_parts)


def parse_docx(file_bytes: bytes) -> str:
    """Extract text from a .docx file."""
    from docx import Document
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def parse_txt(file_bytes: bytes) -> str:
    """Decode plain text bytes."""
    return file_bytes.decode("utf-8", errors="replace")


def extract_text(uploaded_file) -> str:
    """
    Dispatcher: given a Streamlit UploadedFile, extract its text
    based on extension.
    """
    name = uploaded_file.name.lower()
    raw = uploaded_file.read()
    if name.endswith(".pdf"):
        return parse_pdf(raw)
    elif name.endswith(".docx"):
        return parse_docx(raw)
    elif name.endswith(".txt"):
        return parse_txt(raw)
    else:
        return parse_txt(raw)
