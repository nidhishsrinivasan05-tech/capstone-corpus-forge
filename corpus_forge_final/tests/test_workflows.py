from io import BytesIO
import sqlite3

from app import create_app
from app.generator import generate_quiz, unique_evidence_text


def make_client(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client(), tmp_path / "data" / "corpus_forge.db"


def test_upload_generate_and_stats_workflow(tmp_path, monkeypatch):
    client, db_path = make_client(tmp_path, monkeypatch)
    content = (
        "Corpus Forge uses retrieval architecture evaluation and grounded evidence. "
        "The retrieval workflow creates flashcards and quizzes from selected documents."
    )

    upload_response = client.post(
        "/upload",
        data={"document": (BytesIO(content.encode("utf-8")), "notes.md")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert upload_response.status_code == 200
    assert b"notes.md was added to the corpus." in upload_response.data
    assert b"1</strong" in upload_response.data

    with sqlite3.connect(db_path) as db:
        document_id = db.execute("SELECT id FROM documents WHERE filename = ?", ("notes.md",)).fetchone()[0]

    generate_response = client.post(
        "/generate",
        data={
            "active_documents": str(document_id),
            "task": "flashcards",
            "query": "retrieval architecture",
            "strategy": "fixed",
            "audience": "beginner student",
            "tone": "clear and direct",
            "output_format": "structured bullets",
            "creativity": "low",
            "instructions": "",
        },
        follow_redirects=True,
    )

    assert generate_response.status_code == 200
    assert b"Flashcards was generated and saved." in generate_response.data
    assert b"Generated artifacts" in generate_response.data

    stats_response = client.get("/api/stats")
    payload = stats_response.get_json()

    assert stats_response.status_code == 200
    assert payload["stats"]["document_count"] == 1
    assert payload["stats"]["artifact_count"] == 1
    assert payload["usage"]["request_count"] == 1
    assert payload["usage"]["token_count"] > 0


def test_unsupported_upload_shows_feedback_without_insert(tmp_path, monkeypatch):
    client, db_path = make_client(tmp_path, monkeypatch)

    response = client.post(
        "/upload",
        data={"document": (BytesIO(b"not allowed"), "malware.exe")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Unsupported" in response.data or b"file type" in response.data
    with sqlite3.connect(db_path) as db:
        count = db.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    assert count == 0


def test_high_creativity_quiz_changes_question_style():
    quiz = generate_quiz(
        [
            {
                "chunk": (
                    "Corpus Forge uses BM25 retrieval diagnostics, confidence labels, "
                    "matched terms, and grounded evidence to make generated answers auditable."
                )
            }
        ],
        {
            "audience": "capstone examiner",
            "tone": "polished academic",
            "output_format": "structured quiz",
            "creativity": "high",
            "instructions": "make the questions challenging but grounded",
        },
    )

    assert "Creativity: high" in quiz
    assert "Question style: scenario-based" in quiz
    assert "Scenario: a reviewer" in quiz
    assert "unsupported assumptions" in quiz


def test_artifact_generation_deduplicates_compare_evidence():
    chunks = [
        {"chunk": "Repeated retrieval evidence supports grounded quiz generation."},
        {"chunk": "Repeated retrieval evidence supports grounded quiz generation."},
    ]

    assert unique_evidence_text(chunks) == "Repeated retrieval evidence supports grounded quiz generation."


def test_dashboard_counts_all_artifacts_not_only_recent_ten(tmp_path, monkeypatch):
    client, db_path = make_client(tmp_path, monkeypatch)
    with sqlite3.connect(db_path) as db:
        for index in range(12):
            db.execute(
                "INSERT INTO artifacts (title, kind, content, created_at) VALUES (?, ?, ?, ?)",
                (f"Artifact {index}", "test", "content", "2026-05-22 00:00:00"),
            )
        db.commit()

    payload = client.get("/api/stats").get_json()

    assert payload["stats"]["artifact_count"] == 12
