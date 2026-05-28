"""
GITHUB FETCHER - Enhanced GitHub API client with proper error handling
"""

import logging
import requests
from typing import List, Dict, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"
SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".scss", ".less",
    ".java", ".c", ".cpp", ".h", ".hpp", ".go", ".rs", ".rb", ".php",
    ".json", ".yaml", ".yml", ".xml", ".sql", ".md", ".txt", ".sh", ".bash"
}
IGNORED_DIRS = {"node_modules", ".git", ".venv", "venv", "env", "__pycache__"}
MAX_FILE_SIZE = 1024 * 1024  # 1 MB per file


class GitHubFetchError(Exception):
    """Custom exception for GitHub fetching errors"""
    pass


class GitHubFetcher:
    """
    Fetch files from public (and private with token) GitHub repositories
    
    Usage:
        fetcher = GitHubFetcher(token="ghp_...")
        files = fetcher.fetch_repository("https://github.com/owner/repo")
    """
    
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.session = requests.Session()
        if token:
            self.session.headers.update({"Authorization": f"token {token}"})
        self.session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CorpusForge-Client/1.0"
        })
        self.logger = logging.getLogger(__name__)
    
    def fetch_repository(self, repo_url: str) -> List[Dict]:
        """
        Fetch all supported files from a GitHub repository
        
        Args:
            repo_url: GitHub repository URL (https://github.com/owner/repo)
        
        Returns:
            List of dicts with keys: name, path, content
        
        Raises:
            GitHubFetchError: If repository cannot be fetched
        """
        try:
            owner, repo, branch = self._parse_repo_url(repo_url)
            
            # Fetch repository metadata to confirm it exists
            self._verify_repository_exists(owner, repo)
            
            # Get default branch if not specified
            if not branch:
                branch = self._get_default_branch(owner, repo)
            
            # Traverse and collect files
            files = []
            self._traverse_tree(owner, repo, branch, "", files)
            
            self.logger.info(f"Successfully fetched {len(files)} files from {owner}/{repo}")
            return files
        
        except GitHubFetchError as e:
            self.logger.error(f"GitHub fetch error: {str(e)}")
            raise
        except Exception as e:
            error_msg = f"Unexpected error fetching repository: {str(e)}"
            self.logger.error(error_msg)
            raise GitHubFetchError(error_msg)
    
    def _parse_repo_url(self, url: str) -> tuple:
        """Parse GitHub URL to extract owner, repo, and optional branch"""
        url = url.rstrip("/")
        parts = url.replace("https://github.com/", "").split("/")
        
        if len(parts) < 2:
            raise GitHubFetchError("Invalid GitHub URL format")
        
        owner = parts[0]
        repo = parts[1].replace(".git", "")
        
        branch = None
        if len(parts) >= 4 and parts[2] == "tree":
            branch = "/".join(parts[3:])
        
        if not owner or not repo:
            raise GitHubFetchError("Could not parse owner and repo from URL")
        
        return owner, repo, branch
    
    def _verify_repository_exists(self, owner: str, repo: str) -> None:
        """Verify repository exists and is accessible"""
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
        response = self.session.get(url)
        
        if response.status_code == 404:
            raise GitHubFetchError("Repository not found")
        elif response.status_code == 403:
            raise GitHubFetchError("Access forbidden (rate limit or private repo)")
        elif response.status_code >= 400:
            raise GitHubFetchError(f"GitHub API error: {response.status_code}")
    
    def _get_default_branch(self, owner: str, repo: str) -> str:
        """Get the default branch of a repository"""
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
        response = self.session.get(url)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("default_branch", "main")
        
        return "main"  # Fallback
    
    def _traverse_tree(self, owner: str, repo: str, branch: str, path: str, files: List) -> None:
        """Recursively traverse repository tree and collect files"""
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}?ref={branch}"
        
        try:
            response = self.session.get(url)
            
            if response.status_code == 404:
                self.logger.warning(f"Path not found: {path}")
                return
            elif response.status_code >= 400:
                self.logger.warning(f"Cannot fetch path {path}: {response.status_code}")
                return
            
            items = response.json() if isinstance(response.json(), list) else [response.json()]
            
            for item in items:
                # Skip ignored directories
                if item["type"] == "dir":
                    if item["name"] not in IGNORED_DIRS:
                        self._traverse_tree(owner, repo, branch, item["path"], files)
                    continue
                
                # Process files
                if item["type"] == "file":
                    if self._should_include_file(item["name"], item.get("size", 0)):
                        self._fetch_file_content(owner, repo, branch, item, files)
        
        except Exception as e:
            self.logger.warning(f"Error traversing {path}: {str(e)}")
    
    def _should_include_file(self, filename: str, size: int) -> bool:
        """Determine if a file should be included"""
        # Check file size
        if size > MAX_FILE_SIZE:
            return False
        
        # Check extension
        ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
        if ext in SUPPORTED_EXTENSIONS:
            return True
        
        # Special cases: README, LICENSE, etc without extension
        if filename.upper() in {"README", "LICENSE", "CHANGELOG", "AUTHORS"}:
            return True
        
        return False
    
    def _fetch_file_content(self, owner: str, repo: str, branch: str, item: Dict, files: List) -> None:
        """Fetch content of a single file"""
        try:
            url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{item['path']}?ref={branch}"
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                # Get raw content
                if "content" in data:
                    # Small files: content is base64 encoded
                    import base64
                    content = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
                else:
                    # Large files: use raw URL
                    raw_response = self.session.get(item.get("download_url", ""))
                    if raw_response.status_code == 200:
                        content = raw_response.text
                    else:
                        return
                
                files.append({
                    "name": item["name"],
                    "path": item["path"],
                    "content": content
                })
                
                self.logger.debug(f"Fetched: {item['path']}")
        
        except Exception as e:
            self.logger.warning(f"Could not fetch {item['path']}: {str(e)}")
