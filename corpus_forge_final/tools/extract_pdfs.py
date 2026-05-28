from pypdf import PdfReader
from pathlib import Path

pdfs = [
    ("corpus_forge_final/Project Corpuse Forge - Executive Summary.pdf", "corpus_forge_final/pdf_exec_summary.txt"),
    ("corpus_forge_final/AI For Software Development_Course - w14 - course 16 - Capstone Project - Kick-Off.pdf", "corpus_forge_final/pdf_kickoff.txt"),
]

for src, out in pdfs:
    try:
        reader = PdfReader(src)
        text_parts = []
        for page in reader.pages:
            try:
                txt = page.extract_text()
            except Exception:
                txt = ''
            if txt:
                text_parts.append(txt)
        Path(out).write_text('\n\n'.join(text_parts), encoding='utf-8')
        print(f"WROTE: {out}")
    except Exception as e:
        print(f"ERROR processing {src}: {e}")
