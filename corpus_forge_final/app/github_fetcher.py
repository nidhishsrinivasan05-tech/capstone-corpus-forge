import os
import re
import logging
from typing import List, Dict, Optional, Set

import requests

# Configure logging
logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
RAW_BASE = "https://raw.githubusercontent.com"

# Directories to exclude from repo traversal
EXCLUDED_DIRS: Set[str] = {
    'node_modules', '.git', '__pycache__', '.pytest_cache', '.venv', 'venv',
    'env', '.env', 'dist', 'build', '.idea', '.vscode', 'target', 'bin', 'obj',
    '.sass-cache', '.npm', '.yarn', 'coverage', '.tox', '.eggs', '*.egg-info'
}

# File extensions to exclude (binary files)
BINARY_EXTENSIONS: Set[str] = {
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg', '.webp', '.tiff',
    '.zip', '.tar', '.gz', '.rar', '.7z', '.bz2',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods',
    '.exe', '.dll', '.so', '.dylib', '.app', '.deb', '.rpm',
    '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm', '.ogg',
    '.ttf', '.otf', '.woff', '.woff2', '.eot', '.map',
    '.pyc', '.pyo', '.class', '.jar', '.war',
    '.sqlite', '.db', '.mdb',
    '.img', '.iso', '.dmg', '.cdr',
    '.lock', '.sum'
}

# Max file size to fetch (5MB like upload limit)
MAX_FILE_SIZE = 5 * 1024 * 1024

# Large file warning threshold (500KB)
LARGE_FILE_WARNING = 500 * 1024


class GitHubFetchError(RuntimeError):
    pass


class RateLimitError(GitHubFetchError):
    """Raised when GitHub API rate limit is exceeded."""
    pass


class RepoNotFoundError(GitHubFetchError):
    """Raised when repository cannot be found or accessed."""
    pass


class InvalidURLError(GitHubFetchError):
    """Raised when GitHub URL format is invalid."""
    pass


def parse_github_url(url: str) -> Optional[Dict[str, str]]:
    """
    Parse GitHub URL and extract owner, repo, branch, and path.

    Supports formats:
    - https://github.com/owner/repo
    - https://github.com/owner/repo/tree/branch
    - https://github.com/owner/repo/tree/branch/path/to/folder
    """
    # Clean up URL
    url = url.strip().rstrip('/')

    # Main pattern: github.com/owner/repo[/tree/branch[/path]]
    pattern = r"https?://github\.com/([^/]+)/([^/]+)(?:/tree/([^/]+))?(?:/(.*))?$"
    m = re.match(pattern, url)

    if not m:
        # Alternative patterns for URLs without tree/branch prefix
        alt_pattern = r"https?://github\.com/([^/]+)/([^/]+)(?:/.*)?$"
        m2 = re.match(alt_pattern, url)
        if m2:
            owner, repo = m2.groups()
            return {"owner": owner, "repo": repo, "branch": "main", "path": ""}
        return None

    owner, repo, branch, path = m.groups()
    return {
        "owner": owner,
        "repo": repo,
        "branch": branch or "main",
        "path": path or ""
    }


def _is_excluded_path(path: str) -> bool:
    """Check if path should be excluded based on directory or filename patterns."""
    parts = path.split('/')

    # Check if any directory in path is excluded
    for part in parts[:-1]:  # Don't check the file itself as a dir
        if part in EXCLUDED_DIRS:
            return True

    # Check if file matches excluded patterns
    filename = parts[-1]
    if filename in EXCLUDED_DIRS:
        return True

    # Check file extension
    ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
    if ext in BINARY_EXTENSIONS:
        return True

    return False


def list_repo_files(
    owner: str,
    repo: str,
    branch: str = "main",
    token: Optional[str] = None
) -> List[Dict]:
    """
    List all files in repository using GitHub Trees API.

    Returns list of dicts with path, size, type info.
    Raises appropriate errors for rate limits, not found, etc.
    """
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    logger.info(f"Listing files for {owner}/{repo} branch {branch}")

    # First get the branch to find the tree SHA
    branch_url = f"{GITHUB_API}/repos/{owner}/{repo}/branches/{branch}"
    r = requests.get(branch_url, headers=headers, timeout=20)

    if r.status_code == 404:
        # Try default branch
        repo_url = f"{GITHUB_API}/repos/{owner}/{repo}"
        r2 = requests.get(repo_url, headers=headers, timeout=20)
        if r2.status_code == 404:
            raise RepoNotFoundError(
                f"Repository '{owner}/{repo}' not found or not accessible."
            )
        if r2.status_code == 403:
            raise RateLimitError("GitHub API rate limit exceeded. Try again later or provide a token.")
        data = r2.json()
        branch = data.get("default_branch", "main")
        logger.info(f"Using default branch: {branch}")

        r = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}/branches/{branch}", headers=headers, timeout=20)
        if r.status_code == 403:
            raise RateLimitError("GitHub API rate limit exceeded. Try again later or provide a token.")
        if r.status_code == 404:
            raise RepoNotFoundError(f"Branch '{branch}' not found in {owner}/{repo}.")

    if r.status_code == 403:
        raise RateLimitError("GitHub API rate limit exceeded. Try again later or provide a token.")

    if r.status_code != 200:
        raise GitHubFetchError(
            f"Failed to access repository: HTTP {r.status_code}"
        )

    tree_sha = r.json()["commit"]["commit"]["tree"]["sha"]

    # Fetch recursive tree
    tree_url = f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/{tree_sha}?recursive=1"
    tr = requests.get(tree_url, headers=headers, timeout=60)

    if tr.status_code == 403:
        raise RateLimitError("GitHub API rate limit exceeded. Try again later or provide a token.")

    if tr.status_code != 200:
        raise GitHubFetchError(f"Failed to list repository tree: HTTP {tr.status_code}")

    tree_data = tr.json()

    if tree_data.get('truncated'):
        logger.warning("Repository tree was truncated - some files may be missing")

    # Filter to only blobs (files)
    files = [item for item in tree_data.get("tree", []) if item.get("type") == "blob"]

    # Filter excluded paths
    filtered_files = []
    skipped_binary = 0
    skipped_large = 0
    skipped_excluded = 0

    for f in files:
        path = f.get("path", "")

        if _is_excluded_path(path):
            skipped_excluded += 1
            continue

        size = f.get("size", 0)
        if size > MAX_FILE_SIZE:
            skipped_large += 1
            continue

        # Check extension for binary
        ext = '.' + path.split('.')[-1].lower() if '.' in path else ''
        if ext in BINARY_EXTENSIONS:
            skipped_binary += 1
            continue

        filtered_files.append(f)

    logger.info(
        f"Found {len(files)} files, "
        f"filtered: {skipped_excluded} excluded, {skipped_binary} binary, {skipped_large} too large"
    )

    return filtered_files


def fetch_raw_file(
    owner: str,
    repo: str,
    path: str,
    branch: str = "main",
    token: Optional[str] = None
) -> bytes:
    """
    Fetch raw file content from GitHub.
    """
    # Encode path for URL
    from urllib.parse import quote

    url = f"{RAW_BASE}/{owner}/{repo}/{branch}/{quote(path)}"
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"

    r = requests.get(url, headers=headers, timeout=30)

    if r.status_code == 403:
        raise RateLimitError("GitHub API rate limit exceeded. Try again later or provide a token.")

    if r.status_code == 404:
        raise GitHubFetchError(f"File not found: {path}")

    if r.status_code != 200:
        raise GitHubFetchError(f"Failed to fetch {path}: HTTP {r.status_code}")

    return r.content


def fetch_repository(
    url: str,
    token: Optional[str] = None,
    allowed_extensions=None
) -> List[Dict]:
    """
    Fetch repository and return list of supported files with content.

    Args:
        url: GitHub repository URL
        token: Optional GitHub token for private repos or higher rate limits
        allowed_extensions: Optional set of allowed extensions (if None, all text files allowed)

    Returns:
        List of dicts with path, content (bytes), size, and path info
    """
    parsed = parse_github_url(url)
    if not parsed:
        raise InvalidURLError(
            "Invalid GitHub URL. Use format: https://github.com/owner/repo"
        )

    owner = parsed["owner"]
    repo = parsed["repo"]
    branch = parsed.get("branch", "main")
    base_path = parsed.get("path", "")

    logger.info(f"Fetching {owner}/{repo} branch={branch} path={base_path}")

    try:
        files = list_repo_files(owner, repo, branch, token=token)
    except (RateLimitError, RepoNotFoundError, GitHubFetchError):
        raise

    # Filter by base_path if specified
    if base_path:
        files = [f for f in files if f['path'].startswith(base_path)]

    if not files:
        raise GitHubFetchError("No files found in repository or specified path.")

    results = []
    fetch_errors = []

    for item in files:
        path = item.get("path")
        size = item.get("size", 0)

        # Check if it's a large file (warn but don't skip)
        is_large = size > LARGE_FILE_WARNING

        try:
            content = fetch_raw_file(owner, repo, path, branch, token=token)

            # Verify we got expected size (content-length check)
            if len(content) != size:
                logger.warning(f"Size mismatch for {path}: expected {size}, got {len(content)}")

            results.append({
                "path": path,
                "content": content,
                "size": size,
                "is_large": is_large
            })

            if is_large:
                logger.warning(f"Large file: {path} ({size / 1024:.1f}KB)")

        except GitHubFetchError as e:
            fetch_errors.append(f"{path}: {e}")
            logger.warning(f"Skipping {path}: {e}")
            continue

    if not results and fetch_errors:
        raise GitHubFetchError(
            f"Failed to fetch any files. Errors: {'; '.join(fetch_errors[:3])}"
        )

    logger.info(f"Successfully fetched {len(results)} files")

    return results