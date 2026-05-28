import os
import logging
from typing import List, Dict, Optional

from .document_processing import (
    DocumentProcessingError,
    extract_text,
    allowed_file,
    is_code_file
)
from .github_fetcher import (
    fetch_repository,
    GitHubFetchError,
    RateLimitError,
    RepoNotFoundError,
    InvalidURLError
)

logger = logging.getLogger(__name__)


def process_uploaded_file(saved_path: str) -> Dict:
    """
    Process a single saved uploaded file into standardized document dict.

    Args:
        saved_path: Path to the saved file on disk

    Returns:
        Dict with filename, text, filetype, path, and metadata
    """
    logger.info(f"Processing uploaded file: {saved_path}")

    filename = os.path.basename(saved_path)
    filetype = os.path.splitext(filename)[1].lower()

    if not allowed_file(filename):
        raise DocumentProcessingError(f"Unsupported file type: {filetype}")

    try:
        text = extract_text(saved_path)
    except DocumentProcessingError:
        raise

    return {
        "filename": filename,
        "text": text,
        "filetype": filetype,
        "path": saved_path,
        "source": "upload"
    }


def process_github_repo(
    url: str,
    token: Optional[str] = None,
    upload_folder: str = "data/uploads"
) -> List[Dict]:
    """
    Unified function to fetch and process a GitHub repository.

    Args:
        url: GitHub repository URL
        token: Optional GitHub token for private repos
        upload_folder: Where to save downloaded files temporarily

    Returns:
        List of document dicts ready for storage

    Raises:
        InvalidURLError: If URL format is invalid
        RepoNotFoundError: If repository cannot be found
        RateLimitError: If GitHub API rate limit is exceeded
        GitHubFetchError: For other GitHub-related errors
    """
    logger.info(f"Processing GitHub repository: {url}")

    os.makedirs(upload_folder, exist_ok=True)

    try:
        files = fetch_repository(url, token=token)
    except GitHubFetchError:
        raise

    documents = []
    errors = []

    for item in files:
        path = item["path"]
        content = item["content"]
        is_large = item.get("is_large", False)

        # Create safe filename for storage
        safe_name = f"github_{path.replace('/', '__')}"
        save_path = os.path.join(upload_folder, safe_name)

        try:
            # Write content to disk for processing
            with open(save_path, 'wb') as fh:
                fh.write(content)

            # Process through the same pipeline
            doc = process_uploaded_file(save_path)
            doc["source"] = "github"
            doc["github_path"] = path
            doc["is_large"] = is_large
            documents.append(doc)

            logger.info(f"Processed: {path} ({len(doc['text'])} chars)")

        except DocumentProcessingError as e:
            error_msg = f"{path}: {str(e)}"
            errors.append(error_msg)
            logger.warning(f"Skipping {path}: {e}")

            # Clean up failed file
            if os.path.exists(save_path):
                try:
                    os.remove(save_path)
                except OSError:
                    pass

        except Exception as e:
            error_msg = f"{path}: {str(e)}"
            errors.append(error_msg)
            logger.error(f"Unexpected error processing {path}: {e}")

            if os.path.exists(save_path):
                try:
                    os.remove(save_path)
                except OSError:
                    pass

    if not documents and errors:
        error_summary = "; ".join(errors[:5])
        if len(errors) > 5:
            error_summary += f" (+{len(errors) - 5} more)"
        raise GitHubFetchError(f"No files could be processed. Errors: {error_summary}")

    logger.info(f"GitHub import complete: {len(documents)} documents, {len(errors)} skipped")

    return documents


def ingest(source_type: str, data: Dict, upload_folder: str = "data/uploads") -> List[Dict]:
    """
    Unified ingestion pipeline for all document sources.

    Args:
        source_type: Type of source - "file" or "github"
        data: Data dict containing either:
            - For "file": {"path": saved_file_path}
            - For "github": {"url": repo_url, "token": optional_token}
        upload_folder: Folder for storing files

    Returns:
        List of processed document dicts

    Raises:
        ValueError: If source_type is invalid
        DocumentProcessingError: For file processing errors
        GitHubFetchError: For GitHub-related errors
    """
    if source_type == "file":
        path = data.get("path")
        if not path:
            raise ValueError("Missing 'path' for file ingestion")
        doc = process_uploaded_file(path)
        return [doc]

    elif source_type == "github":
        url = data.get("url")
        token = data.get("token")
        if not url:
            raise ValueError("Missing 'url' for github ingestion")
        return process_github_repo(url, token=token, upload_folder=upload_folder)

    else:
        raise ValueError(f"Unknown source_type: {source_type}. Use 'file' or 'github'.")