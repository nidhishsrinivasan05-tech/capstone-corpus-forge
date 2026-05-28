# Project Report - Corpus Forge

## Team members

- Omar Kahkahni - omar.kahkahni@epita.fr - GitHub: omarkahaa
- Teammate 2 - EPITA email - GitHub username
- Teammate 3 - EPITA email - GitHub username

Replace the two placeholder lines with the real team members before final submission.

## Initial design

The first design was a small local web application using Python and Flask. The goal was to keep the architecture simple enough to explain while still covering the required features: document ingestion, corpus management, retrieval, generation, persistence, usage tracking, and visualization.

The system is divided into clear modules:

- `routes.py` handles the web pages and form submissions.
- `document_processing.py` validates files and extracts text from text, Markdown, PDF, and source code files.
- `retrieval.py` chunks documents and searches the active corpus.
- `generator.py` creates grounded answers, flashcards, quizzes, and code reports.
- `storage.py` manages SQLite persistence.

The main assumption was that the application must run locally on a student machine without complex setup. For that reason, SQLite was chosen instead of a separate database server.

## Technical choices

Flask was selected because it is lightweight and easy to run locally. SQLite was selected because it persists documents, metadata, generated artifacts, and usage statistics without requiring installation of MySQL or PostgreSQL. PDF extraction is handled with `pypdf` because it is simple and works for standard text-based PDFs.

The generation layer currently uses retrieval-grounded local generation instead of a paid AI API. This makes the project runnable in class without API keys. The design still separates retrieval and generation, so an external model can be added later.

## Engineering decisions

### Retrieval strategy

Two retrieval strategies were implemented.

The first strategy is fixed-size chunk retrieval. Documents are split into overlapping word chunks, and the query is matched against each chunk. This usually gives more precise context because the answer is based on a smaller part of the document.

The second strategy is file-level retrieval. The query is matched against the whole document, and the beginning of the most relevant file is returned. This is easier to understand and sometimes works better for short files, but it can return too much irrelevant text for longer files.

A comparison mode runs both strategies together. This was added because the project requires experimentation and trade-off evaluation.

### Persistence

The first possible option was to keep all documents in memory, but this would lose everything when the server stops. SQLite was chosen so uploads, generated artifacts, and usage statistics survive between runs.

### Prompt steering

The user can steer generation with audience level, tone, output format, creativity, and task instructions. These parameters are included in the generated answer so the effect is visible and easy to explain during the demo.

### Cost observability

The application tracks request count and estimated token usage. The token value is not exact because no paid model is called, but it gives a useful approximation of how much text is being processed.

## Engineering challenges selected

### Challenge 1 - Retrieval experimentation

The application compares fixed-size chunk retrieval and file-level retrieval. Fixed chunks are better for precise questions. File-level retrieval is simpler and useful when files are short. The comparison mode shows that retrieval strategy changes the evidence shown to the user.

### Challenge 2 - Visualization

The application includes an interactive term-frequency visualization. It extracts common terms from the corpus and displays them in a bar chart. The user can move a slider to change how many terms are shown.

## Who did what

Initial planned division:

- Omar: Flask structure, document upload, retrieval, and README.
- Teammate 2: UI improvement, visualization, and testing.
- Teammate 3: report, presentation, and demo scenario.

This section must be updated by the team with the real work distribution before submission.

## AI collaboration

AI assistance was used as a learning and debugging support tool. The main use was to break the project into smaller tasks, clarify architecture choices, and check whether the implemented features match the assignment requirements.

AI suggestions were not accepted blindly. The project was checked against the course requirements: at least three file types, document management, active document selection, retrieval-grounded workflows, prompt steering, persistence, usage tracking, and engineering challenges.

## Failures and iterations

The first issue was scope. A full AI platform with real embeddings and paid generation would require API keys and more setup time. The design was reduced to a local version that still demonstrates the main architecture.

The second issue was PDF handling. Some PDFs may not contain extractable text. The current version handles normal text PDFs, but scanned PDFs would require OCR in a future version.

The third issue was retrieval quality. File-level retrieval was too broad for long documents, so fixed-size chunk retrieval was added.

## When AI failed or was wrong

Some AI-style suggestions were too large for the project deadline, such as adding a full vector database, user accounts, and complex frontend frameworks. These ideas were rejected because they would make the project harder to run and explain.

Another limitation was that generated quiz questions can be basic when the retrieved context is short. This was handled by grounding every output in selected documents and saving the result as an artifact for review.

## Lessons learned

The project shows that RAG is not only about calling an AI model. The quality depends first on ingestion, chunking, selection of active documents, retrieval strategy, and clear prompts.

The main technical lesson is that a simple architecture is easier to test and explain. The main workflow lesson is that small commits and small features reduce confusion. The main AI lesson is that AI tools are useful for acceleration, but the developer still has to verify the design and decide what is realistic.
