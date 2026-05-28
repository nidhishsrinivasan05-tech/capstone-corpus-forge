import os
from pathlib import Path
from app.document_processing import extract_text, is_code_file
from app import create_app
from app import retrieval, generator
from pypdf import PdfWriter

BASE = Path(__file__).resolve().parents[1]
UPLOADS = BASE / 'data' / 'uploads'
DOCS = BASE / 'docs'
DOCS.mkdir(exist_ok=True)

# Collect documents
documents = []
for p in UPLOADS.iterdir():
    if p.is_file() and p.name not in ('storage.py', 'config.json'):
        try:
            text = extract_text(str(p))
        except Exception:
            # fallback: read raw
            text = p.read_text(encoding='utf-8', errors='ignore')
        documents.append({'filename': p.name, 'text': text})

if not documents:
    print('No documents found in uploads to generate artifacts.')
    raise SystemExit(0)

# Generate retrieval-backed flashcards/quiz for a simple query
query = 'summary'
strategy = 'compare'
results = retrieval.retrieve(documents, query, strategy=strategy)

def write_artifact(name, content):
    out = DOCS / name
    out.write_text(content, encoding='utf-8')
    print('WROTE', out)

# Flashcards
flash = generator.generate_flashcards(results, {
    'audience': 'student', 'tone': 'informal', 'output_format': 'text', 'creativity': 'low', 'instructions': ''
})
write_artifact('flashcards.txt', flash)

# Quiz
quiz = generator.generate_quiz(results, {
    'audience': 'student', 'tone': 'neutral', 'output_format': 'text', 'creativity': 'medium', 'instructions': ''
})
write_artifact('quiz.txt', quiz)

# Code review + architecture
code_docs = [d for d in documents if is_code_file(d['filename'])]
code_review = generator.code_review(code_docs, {
    'audience': 'developer', 'tone': 'technical', 'output_format': 'text', 'creativity': 'low', 'instructions': ''
})
write_artifact('code_review.txt', code_review)

architecture = generator.architecture_report(code_docs, {
    'audience': 'developer', 'tone': 'technical', 'output_format': 'text', 'creativity': 'low', 'instructions': ''
})
write_artifact('architecture.txt', architecture)

# top terms
terms = retrieval.top_terms(documents, limit=40)
write_artifact('top_terms.txt', '\n'.join([f"{t}: {c}" for t, c in terms]))

# Create placeholder PDFs for slides
writer = PdfWriter()
writer.add_blank_page(width=595, height=842)
with open(DOCS / 'group_presentation.pdf', 'wb') as fh:
    writer.write(fh)
print('WROTE', DOCS / 'group_presentation.pdf')

writer2 = PdfWriter()
writer2.add_blank_page(width=595, height=842)
with open(DOCS / 'individual_presentation_student_name.pdf', 'wb') as fh:
    writer2.write(fh)
print('WROTE', DOCS / 'individual_presentation_student_name.pdf')

print('Done generating docs in', DOCS)
