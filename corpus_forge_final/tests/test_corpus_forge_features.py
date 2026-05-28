import pytest
import json
from io import BytesIO
from app import create_app
from app.document_processing import (
    extract_text, allowed_file, is_code_file, is_binary_file,
    SUPPORTED_EXTENSIONS, CODE_EXTENSIONS
)
from app.github_fetcher import (
    parse_github_url, RateLimitError, RepoNotFoundError, InvalidURLError
)
from app.processor import ingest, process_uploaded_file

@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()


# ===== TEST DOCUMENT PROCESSING =====

class TestAllowedFile:
    def test_supported_extensions(self):
        for ext in [".txt", ".md", ".pdf", ".py", ".js", ".html", ".css", ".java", ".json", ".csv"]:
            assert allowed_file(f"test{ext}") == True, f"Extension {ext} should be allowed"

    def test_unsupported_extensions(self):
        for ext in [".exe", ".png", ".jpg", ".zip", ".mp4"]:
            assert allowed_file(f"test{ext}") == False, f"Extension {ext} should NOT be allowed"

    def test_case_insensitive(self):
        assert allowed_file("test.TXT") == True
        assert allowed_file("test.Py") == True
        assert allowed_file("test.JS") == True


class TestCodeFileDetection:
    def test_code_files_detected(self):
        for ext in [".py", ".js", ".ts", ".java", ".c", ".cpp", ".go", ".rb"]:
            assert is_code_file(f"test{ext}") == True, f"{ext} should be detected as code"

    def test_non_code_files_not_detected(self):
        for ext in [".txt", ".md", ".json", ".csv"]:
            assert is_code_file(f"test{ext}") == False, f"{ext} should NOT be detected as code"


# ===== TEST GITHUB FETCHER =====

class TestParseGitHubUrl:
    def test_valid_urls(self):
        test_cases = [
            ("https://github.com/owner/repo", {"owner": "owner", "repo": "repo", "branch": "main", "path": ""}),
            ("https://github.com/owner/repo/tree/main", {"owner": "owner", "repo": "repo", "branch": "main", "path": ""}),
            ("https://github.com/owner/repo/tree/develop/src", {"owner": "owner", "repo": "repo", "branch": "develop", "path": "src"}),
            ("https://github.com/microsoft/vscode", {"owner": "microsoft", "repo": "vscode", "branch": "main", "path": ""}),
        ]
        for url, expected in test_cases:
            result = parse_github_url(url)
            assert result == expected, f"URL {url} should parse to {expected}, got {result}"

    def test_invalid_urls(self):
        for url in [
            "https://github.com/owner",
            "https://gitlab.com/owner/repo",
            "not a url",
            ""
        ]:
            result = parse_github_url(url)
            assert result is None, f"Invalid URL {url} should return None"


# ===== TEST ERROR HANDLING =====

class TestErrorClasses:
    def test_rate_limit_error_exists(self):
        error = RateLimitError("Rate limit exceeded")
        assert str(error) == "Rate limit exceeded"

    def test_repo_not_found_error_exists(self):
        error = RepoNotFoundError("Repo not found")
        assert str(error) == "Repo not found"

    def test_invalid_url_error_exists(self):
        error = InvalidURLError("Invalid URL")
        assert str(error) == "Invalid URL"


# ===== TEST ROUTES =====

class TestIndexRoute:
    def test_index_loads(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert b"Corpus Forge" in response.data

    def test_source_selector_present(self, client):
        response = client.get("/")
        assert b"source-select" in response.data or b"Local" in response.data

    def test_upload_form_present(self, client):
        response = client.get("/")
        assert b"upload-form" in response.data


class TestUploadRoute:
    def test_upload_txt_file(self, client):
        response = client.post(
            "/upload",
            data={"document": (BytesIO(b"Hello World Content"), "test.txt")},
            content_type="multipart/form-data",
            follow_redirects=True
        )
        assert response.status_code == 200

    def test_upload_md_file(self, client):
        response = client.post(
            "/upload",
            data={"document": (BytesIO(b"# Markdown Content"), "readme.md")},
            content_type="multipart/form-data",
            follow_redirects=True
        )
        assert response.status_code == 200

    def test_upload_json_file(self, client):
        json_content = json.dumps({"name": "test", "version": "1.0"}).encode()
        response = client.post(
            "/upload",
            data={"document": (BytesIO(json_content), "config.json")},
            content_type="multipart/form-data",
            follow_redirects=True
        )
        assert response.status_code == 200

    def test_upload_unsupported_file(self, client):
        response = client.post(
            "/upload",
            data={"document": (BytesIO(b"binary content"), "file.exe")},
            content_type="multipart/form-data",
            follow_redirects=True
        )
        assert b"Unsupported" in response.data

    def test_upload_empty_file_rejected(self, client):
        response = client.post(
            "/upload",
            data={"document": (BytesIO(b""), "empty.txt")},
            content_type="multipart/form-data",
            follow_redirects=True
        )
        assert b"empty" in response.data.lower() or b"could not process" in response.data.lower()


class TestAPIStats:
    def test_stats_endpoint(self, client):
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.get_json()
        assert "stats" in data
        assert "usage" in data
        assert "document_count" in data["stats"]
        assert "artifact_count" in data["stats"]


class TestIngestAPI:
    def test_ingest_missing_source_type(self, client):
        response = client.post("/api/ingest",
            data=json.dumps({"data": {}}),
            content_type="application/json"
        )
        assert response.status_code == 400

    def test_ingest_invalid_source_type(self, client):
        response = client.post("/api/ingest",
            data=json.dumps({"source_type": "invalid", "data": {}}),
            content_type="application/json"
        )
        assert response.status_code == 400


# ===== TEST VIEWS PAGE =====

class TestArtifactsRoute:
    def test_artifacts_page_loads(self, client):
        response = client.get("/artifacts")
        assert response.status_code == 200
        assert b"artifacts" in response.data.lower()


class TestVisualizationRoute:
    def test_visualization_page_loads(self, client):
        response = client.get("/visualization")
        assert response.status_code == 200
        assert b"visualization" in response.data.lower() or b"term" in response.data.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
