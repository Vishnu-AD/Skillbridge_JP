import os
from PyPDF2 import PdfReader

def read_resume_text(filepath: str) -> str:
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".pdf":
        reader = PdfReader(filepath)
        out = []
        for page in reader.pages:
            out.append(page.extract_text() or "")
        return "\n".join(out).strip()
    # fallback for .txt
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()