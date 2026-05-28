"""
INGESTION SERVICE - Unified pipeline for all data sources
Clean architecture for handling "file" | "github" sources
"""

import logging
import os
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class SourceType(Enum):
    """Supported ingestion sources"""
    FILE = "file"
    GITHUB = "github"


@dataclass
class IngestResult:
    """Result of ingestion operation"""
    success: bool
    count: int
    files: List[Dict] = None
    error: Optional[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.files is None:
            self.files = []
        if self.warnings is None:
            self.warnings = []


class IngestionPipeline:
    """
    Main ingestion service - unified interface for all sources
    
    Usage:
        pipeline = IngestionPipeline()
        result = pipeline.ingest(SourceType.GITHUB, {"url": "https://github.com/owner/repo"})
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def ingest(self, source_type: SourceType, data: Dict) -> IngestResult:
        """
        Unified ingestion interface
        
        Args:
            source_type: SourceType.FILE or SourceType.GITHUB
            data: Dict with source-specific parameters
                - For FILE: {"path": str, "filename": str}
                - For GITHUB: {"url": str, "token": Optional[str]}
        
        Returns:
            IngestResult with success status and file list
        """
        try:
            if source_type == SourceType.FILE:
                return self._ingest_file(data)
            elif source_type == SourceType.GITHUB:
                return self._ingest_github(data)
            else:
                return IngestResult(success=False, count=0, error="Unknown source type")
        except Exception as e:
            self.logger.error(f"Ingestion failed: {str(e)}")
            return IngestResult(success=False, count=0, error=str(e))
    
    def _ingest_file(self, data: Dict) -> IngestResult:
        """Process local file upload"""
        from .document_processing import extract_text, allowed_file, DocumentProcessingError
        
        try:
            file_path = data.get("path")
            filename = data.get("filename")
            
            if not file_path or not os.path.exists(file_path):
                return IngestResult(success=False, count=0, error="File path not found")
            
            if not allowed_file(filename):
                return IngestResult(success=False, count=0, error=f"Unsupported file type: {filename}")
            
            # Extract text from file
            text = extract_text(file_path)
            
            # Prepare for storage
            file_data = {
                "filename": filename,
                "filetype": os.path.splitext(filename)[1].lstrip('.').lower() or "unknown",
                "text": text,
                "source": "local_upload"
            }
            
            self.logger.info(f"Successfully ingested file: {filename}")
            return IngestResult(success=True, count=1, files=[file_data])
        
        except Exception as e:
            error_msg = f"File processing error: {str(e)}"
            self.logger.error(error_msg)
            return IngestResult(success=False, count=0, error=error_msg)
    
    def _ingest_github(self, data: Dict) -> IngestResult:
        """Process GitHub repository import"""
        from .github_fetcher import GitHubFetcher, GitHubFetchError
        
        try:
            repo_url = data.get("url", "").strip()
            token = data.get("token", "").strip() or None
            
            if not repo_url:
                return IngestResult(success=False, count=0, error="Repository URL is required")
            
            # Validate and parse URL
            if not self._validate_github_url(repo_url):
                return IngestResult(success=False, count=0, error="Invalid GitHub URL format")
            
            # Fetch repository
            fetcher = GitHubFetcher(token=token)
            files = fetcher.fetch_repository(repo_url)
            
            if not files:
                return IngestResult(
                    success=False,
                    count=0,
                    error="No supported files found in repository"
                )
            
            # Process each file through extraction pipeline
            processed_files = []
            warnings = []
            
            for file_data in files:
                try:
                    processed = self._process_github_file(file_data)
                    if processed:
                        processed_files.append(processed)
                except Exception as e:
                    warnings.append(f"Skipped {file_data.get('name')}: {str(e)}")
                    self.logger.warning(f"Failed to process GitHub file: {str(e)}")
            
            self.logger.info(f"Successfully ingested {len(processed_files)} files from GitHub")
            
            return IngestResult(
                success=True,
                count=len(processed_files),
                files=processed_files,
                warnings=warnings
            )
        
        except Exception as e:
            error_msg = f"GitHub ingestion error: {str(e)}"
            self.logger.error(error_msg)
            return IngestResult(success=False, count=0, error=error_msg)
    
    def _process_github_file(self, file_data: Dict) -> Optional[Dict]:
        """
        Process a single file from GitHub into standard format
        
        Returns:
            Dict with filename, filetype, text, source
            or None if file should be skipped
        """
        from .document_processing import normalize_code_text, normalize_text, is_code_file
        
        name = file_data.get("name", "")
        content = file_data.get("content", "")
        
        if not content or len(content.strip()) < 20:
            return None
        
        # Detect file type and normalize
        ext = os.path.splitext(name)[1].lower()
        filetype = ext.lstrip(".") or "unknown"
        
        # Apply appropriate normalization
        if is_code_file(name):
            normalized_content = normalize_code_text(content)
        else:
            normalized_content = normalize_text(content)
        
        if len(normalized_content) < 20:
            return None
        
        return {
            "filename": name,
            "filetype": filetype,
            "text": normalized_content,
            "source": "github_import"
        }
    
    @staticmethod
    def _validate_github_url(url: str) -> bool:
        """Validate GitHub URL format"""
        import re
        pattern = r"^https://github\.com/[\w\-]+/[\w\-\.]+/?(?:/tree/[\w\-]+)?$"
        return bool(re.match(pattern, url))
