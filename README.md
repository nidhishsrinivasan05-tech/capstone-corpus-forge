# Corpus Forge

Corpus Forge is a local web application that turns a small document collection into useful study and engineering outputs.

It can ingest text, Markdown, PDF, and source code files. Users can select active documents, ask grounded questions, generate flashcards, generate quizzes, create code review reports, create architecture/control-flow reports, view saved outputs, and monitor estimated AI usage.

## Features

- Upload documents: `.txt`, `.md`, `.pdf`, `.py`, `.js`, `.html`, `.css`, `.java`, `.c`, `.cpp`, `.json`, `.xml`
- Browse and remove documents
- Select active documents for each AI interaction
- Retrieval-grounded chat and question answering
- Flashcard generation
- Quiz generation
- Source-code review report
- Architecture and control-flow report
- Prompt steering: audience, tone, output format, creativity, and custom instructions
- Persistence with SQLite
- Cost observability: request count and estimated token usage
- Two retrieval strategies: fixed-size chunk retrieval and file-level retrieval
- Interactive term-frequency visualization
- Basic tests for retrieval and failure cases

## Setup

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
python run.py
```

Open this address in your browser:

```text
http://127.0.0.1:5000
```

## How to use

1. Upload at least one document.
2. Select one or more active documents.
3. Ask a question or generate an artifact.
4. Open the Artifacts page to view saved flashcards, quizzes, and reports.
5. Open the Visualization page to inspect frequent terms in the corpus.

## Run tests

```bash
pytest
```

## Project structure

```text
app/                    Flask application code
app/document_processing.py  File validation and text extraction
app/retrieval.py            Chunking, BM25-style retrieval, diagnostics, token estimates
app/generator.py            Grounded output generation and code reports
app/storage.py              SQLite database setup and usage tracking
app/routes.py               Web routes and form handling
templates/              HTML templates
static/                 CSS and JavaScript
data/uploads/           Uploaded files, ignored by Git
docs/                   Generated project documentation and presentation PDFs
tests/                  Pytest tests
```

## Notes

This version uses local retrieval and local generation logic so it can run without paid API keys. The token count is an estimate based on the text processed by the application. A future version could connect the retrieval output to Google GenAI for stronger natural-language generation.
