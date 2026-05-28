# Corpus Forge - 10x Upgrade Review

## 🔍 Critical assessment of the current project

The original project had a good base: Flask, SQLite, document upload, active document selection, retrieval, artifact generation, visualization, and tests. The problem was not feature quantity. The problem was depth.

Main weaknesses fixed:

1. Retrieval was too basic. The old scoring was raw keyword overlap, so long chunks and repeated words could dominate results.
2. Evidence was not auditable enough. The app returned chunks, but it did not show word ranges, matched terms, or confidence.
3. Failure handling was weak. If retrieval failed, the app mostly gave a generic message instead of diagnostics.
4. File validation was too light. Empty files, huge files, and scanned/low-text PDFs were not handled clearly.
5. Testing was too small. The test suite only checked the easiest happy path.
6. The report described trade-offs, but the implementation did not fully support those claims.

Where it looked student-level:

- simple keyword count retrieval
- generic code review recommendations
- no meaningful retrieval metrics
- weak malformed-input tests
- no confidence/failure analysis
- no clear distinction between evidence and generated text

## 🧠 Upgraded design & architecture

The upgraded version keeps the project realistic and local, but makes it more defensible.

```text
Browser UI
  -> Flask routes
      -> document_processing.py
          validates files and extracts normalized text
      -> retrieval.py
          BM25-style chunk/file retrieval + diagnostics
      -> generator.py
          grounded answers, quizzes, flashcards, code reports
      -> storage.py
          SQLite documents, artifacts, usage stats
  -> templates
      display answers, evidence, diagnostics, and visualization
```

Important design decisions:

- SQLite remains the right database because this is a local capstone product, not a multi-tenant SaaS.
- BM25-style retrieval is stronger than raw keyword counts while still explainable in a presentation.
- The app now returns confidence, matched terms, and source ranges so answers are auditable.
- The generation layer stays extractive because the project does not require paid API keys and should not fake LLM quality.

## ⚙️ Improved model / logic

### Step 1: Normalize and validate documents

The upload pipeline now checks file size, empty files, low-text extraction, and PDF page count. This prevents bad inputs from silently entering the corpus.

### Step 2: Split text into overlapping chunks

Each chunk stores:

- text
- chunk index
- start word
- end word

This makes retrieval explainable.

### Step 3: Score candidates with BM25-style logic

The retrieval now uses:

- tokenization
- stopword removal
- inverse document frequency
- candidate length normalization
- query-term frequency

This is not a toy model. It is a standard lexical retrieval approach adapted to a small local application.

### Step 4: Return diagnostics

Each query reports:

- selected document count
- indexed word count
- query terms
- result count
- top score
- failure reason when no result is found

### Step 5: Generate only from evidence

The answer generator now separates:

- direct answer
- evidence used
- retrieval diagnostics

That is much safer and easier to defend.

## 💻 High-quality code changes

Main files upgraded:

- `app/retrieval.py`
- `app/document_processing.py`
- `app/generator.py`
- `app/routes.py`
- `templates/index.html`
- `tests/test_retrieval.py`
- `docs/architecture.md`
- `docs/retrieval_experiment.md`

The code now uses clearer names, dataclasses for retrieval candidates, typed function signatures in the retrieval layer, explicit validation errors, and tests for failure cases.

## 📊 Evaluation & validation strategy

The upgraded test suite checks:

- chunking behavior
- correct document retrieval
- confidence labels
- compare-mode deduplication
- retrieval metadata
- no-answer diagnostics
- text normalization
- empty corpus behavior

Recommended capstone evaluation:

1. Create 20 test questions over 5 uploaded documents.
2. Mark the expected source document and expected answer type.
3. Measure top-1 and top-3 retrieval accuracy.
4. Add 5 no-answer questions and measure whether the system refuses correctly.
5. Record one failure case where lexical retrieval misses a synonym.
6. Explain why embeddings would be the next upgrade, but not required for this local version.

Edge cases to show during demo:

- query with no matching evidence
- empty upload
- scanned PDF with almost no extractable text
- long document where chunk retrieval beats file-level retrieval
- short document where file-level retrieval is enough

## Advanced improvements added

### 1. BM25-style retrieval

Why it matters: scoring is now more robust than raw keyword counts and can be explained academically.

### 2. Retrieval diagnostics and confidence labels

Why it matters: professors can see why the app returned a result instead of trusting a black box.

### 3. Stronger upload validation

Why it matters: real products must handle bad files, empty files, huge files, and unreadable PDFs.

### 4. Safer grounded generation

Why it matters: the app now refuses when evidence is missing instead of producing unsupported answers.

### 5. Better testing and failure analysis

Why it matters: capstone projects are judged on engineering reliability, not just screenshots.

## 🚀 Final capstone-ready version summary

The project is now a realistic local corpus assistant. It can ingest documents, retrieve evidence using explainable BM25-style scoring, generate grounded outputs, show diagnostics, save artifacts, visualize terms, and defend failure cases.

It is still simple enough to run on a student laptop, but it no longer looks like a basic Flask demo. The architecture, retrieval logic, validation, and evaluation story are now strong enough for a professor or industry engineer review.
