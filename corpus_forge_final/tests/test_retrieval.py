from app.retrieval import chunk_text, retrieve, retrieval_diagnostics, top_terms
from app.document_processing import extract_text, normalize_code_text, normalize_text


def test_chunk_text_keeps_content():
    text = " ".join(["word"] * 320)
    chunks = chunk_text(text, size=100, overlap=20)
    assert len(chunks) >= 3
    assert "word" in chunks[0]


def test_fixed_retrieval_finds_relevant_document():
    documents = [
        {"filename": "a.txt", "text": "Python Flask routing and templates"},
        {"filename": "b.txt", "text": "Bananas and apples"},
    ]
    results = retrieve(documents, "Flask templates", "fixed")
    assert results[0]["document"] == "a.txt"
    assert results[0]["confidence"] == "high"
    assert "flask" in results[0]["matched_terms"]


def test_compare_strategy_deduplicates_and_returns_metadata():
    documents = [{"filename": "capstone.md", "text": "retrieval architecture evaluation testing " * 50}]
    results = retrieve(documents, "retrieval evaluation", "compare")
    assert results
    assert all("start_word" in item and "end_word" in item for item in results)
    assert len({(item["document"], item["strategy"], item["chunk_index"]) for item in results}) == len(results)


def test_no_match_returns_diagnostic_failure_reason():
    documents = [{"filename": "fruit.txt", "text": "banana orange apple"}]
    results = retrieve(documents, "database transaction isolation", "fixed")
    diagnostics = retrieval_diagnostics(documents, "database transaction isolation", results)
    assert results == []
    assert diagnostics["failure_reason"]


def test_generic_overview_question_returns_selected_document_fallback():
    documents = [{"filename": "storage.py", "text": "import sqlite3\n\ndef init_db():\n    return sqlite3.connect('data.db')"}]

    results = retrieve(documents, "what does this file do", "fixed")

    assert results
    assert results[0]["document"] == "storage.py"
    assert results[0]["strategy"] == "selected document overview"
    assert results[0]["confidence"] == "low"


def test_stopword_only_overview_question_still_returns_fallback():
    documents = [{"filename": "notes.md", "text": "Corpus Forge stores uploaded files and generated artifacts."}]

    results = retrieve(documents, "what is this about", "fixed")

    assert results
    assert results[0]["document"] == "notes.md"
    assert results[0]["strategy"] == "selected document overview"


def test_empty_corpus_returns_empty_terms():
    assert top_terms([], 10) == []


def test_normalize_text_removes_empty_lines_and_nulls():
    assert normalize_text("hello\n\n\x00 world") == "hello\nworld"


def test_extract_text_handles_utf16_source_files(tmp_path):
    source = tmp_path / "Example.java"
    source.write_text(
        "public class Example { public static void main(String[] args) { System.out.println(\"hello\"); } }",
        encoding="utf-16",
    )

    extracted = extract_text(str(source))

    assert "public class Example" in extracted
    assert "p u b l i c" not in extracted


def test_code_normalization_preserves_python_indentation():
    text = "\nclass Repository:\n    def save(self, value):\n        return value\n"

    normalized = normalize_code_text(text)

    assert "    def save" in normalized
    assert "        return value" in normalized
