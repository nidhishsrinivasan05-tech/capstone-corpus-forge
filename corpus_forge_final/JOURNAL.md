# Project Journal - Corpus Forge

## Entry 1 - Understanding the assignment

Goal: build a local web application that can import different document types, organize them, retrieve relevant information, generate useful outputs, and persist results.

Important requirements noted:

- at least three file types including text/Markdown, PDF, and source code;
- add, remove, browse, and select active documents;
- retrieval-grounded chat;
- flashcards and quizzes;
- code review and architecture/control-flow reports for source code;
- prompt steering;
- persistence;
- usage tracking;
- two engineering challenges.

## Entry 2 - Architecture choice

I chose Flask because it is simple to run locally and easy to explain. I chose SQLite because the project needs persistence but does not need a heavy database server.

The application was split into small modules: routes, storage, document processing, retrieval, and generation.

## Entry 3 - Retrieval experimentation

Two retrieval strategies were implemented:

- fixed-size overlapping chunks;
- file-level retrieval.

Fixed chunks gave more precise context. File-level retrieval was easier but less precise for long files. A comparison option was added to show both results.

## Entry 4 - Generation features

The first generated outputs were grounded answers, flashcards, and quizzes. Then code review and architecture reports were added for source code files.

Prompt steering options were added so the user can change audience, tone, format, creativity, and task instructions.

## Entry 5 - Persistence and usage tracking

Documents and artifacts are stored in SQLite. Uploaded files are saved in `data/uploads`. The application also stores request count and estimated token count.

## Entry 6 - Visualization

An interactive term-frequency visualization was added. It uses the words extracted from the corpus and displays the most common terms. A slider lets the user change the number of visible terms.

## Entry 7 - Testing

Basic tests were added for chunking, retrieval, and empty corpus behavior. More tests could be added later for PDF files and malformed uploads.
