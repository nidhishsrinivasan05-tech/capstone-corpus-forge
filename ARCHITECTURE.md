# CORPUS FORGE: PRODUCTION ARCHITECTURE & INTEGRATION GUIDE

## 📋 Overview

This document describes the clean, production-grade architecture implemented for Corpus Forge. The system now separates concerns properly with a unified ingestion pipeline that supports multiple source types (Local Files, GitHub).

---

## 🏗️ ARCHITECTURE LAYERS

### 1. **Ingestion Pipeline** (`app/ingestion.py`)
- **Purpose**: Unified entry point for all document ingestion
- **Interface**: `IngestionPipeline.ingest(source_type: SourceType, data: dict)`
- **Returns**: `IngestResult` dataclass with structured success/count/files/error/warnings

**Supports**:
- `SourceType.FILE` - Local file upload
- `SourceType.GITHUB` - GitHub repository import

### 2. **GitHub Fetcher** (`app/github_fetcher_v2.py`)
- **Purpose**: Enhanced GitHub API client with enterprise-grade error handling
- **Capabilities**:
  - Recursive tree traversal
  - File filtering and size limits
  - Authenticated & unauthenticated access
  - Comprehensive error handling

### 3. **Document Processing** (`app/document_processing.py`)
- **Purpose**: Parse documents of various types
- **Supported Formats**: TXT, PDF, JSON, CSV, HTML, Code files
- **Features**: Encoding detection, graceful fallback, detailed logging

### 4. **Storage Layer** (`app/storage.py`)
- **Purpose**: Database abstraction for documents and usage tracking
- **Database**: SQLite with proper connection management

### 5. **API Routes** (`app/routes.py` + `app/ingestion_routes.py`)
- **Purpose**: HTTP endpoints for ingestion
- **Endpoints**:
  - `POST /upload_file` - Upload local file
  - `POST /import_repo` - Import GitHub repository

### 6. **Frontend** (`templates/index_v2.html` + `static/js/document-ingestion.js`)
- **Purpose**: User interface and client-side logic
- **Features**:
  - Source toggle (Local/GitHub)
  - Form validation
  - Real-time feedback (toasts, status messages)
  - Document preview with expand/collapse

---

## 🔧 INTEGRATION CHECKLIST

### Step 1: Update Main Routes File

Replace the old `/upload_file` and `/import_repo` endpoints in `app/routes.py` with calls to `ingestion_routes.py`:

```python
# In app/__init__.py or main routes setup:

from .ingestion_routes import create_ingestion_routes

# Register new endpoints:
ingestion_endpoints = create_ingestion_routes(bp, current_app.config)

# The old endpoints will be replaced by:
# - ingestion_endpoints['upload_file']
# - ingestion_endpoints['import_repo']
```

### Step 2: Update HTML Template

The new UI template is in `templates/index_v2.html`.

**Option A**: Replace `templates/index.html` with `index_v2.html`
**Option B**: Copy UI improvements into existing template

Key sections to copy:
- Source selector markup (lines 20-31)
- Form sections (lines 34-78)
- Document preview (lines 109-142)
- Script includes (lines 154-156)

### Step 3: Add CSS Stylesheet

Link the new stylesheet in your base template:

```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/ingestion.css') }}">
```

### Step 4: Add JavaScript Component

Include the new JavaScript component:

```html
<script src="{{ url_for('static', filename='js/document-ingestion.js') }}"></script>
```

### Step 5: Configure Flask App

Ensure your Flask app has:

```python
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
```

---

## 📊 DATA FLOW

### LOCAL FILE UPLOAD FLOW

```
1. User selects file (drag & drop or click)
   ↓
2. DocumentIngestionComponent.handleFileUpload()
   ↓
3. POST /upload_file with FormData
   ↓
4. ingestion_routes.upload_file()
   ├─ Validate file exists
   ├─ Save temporarily
   ├─ Call IngestionPipeline.ingest(SourceType.FILE, {...})
   │  ├─ DocumentProcessor.parse_file()
   │  ├─ Detect format dynamically
   │  ├─ Extract text
   │  └─ Return IngestResult
   ├─ Store in SQLite (documents table)
   ├─ Update usage stats
   └─ Return JSON response
   ↓
5. Frontend: Show toast, reload
   ↓
6. Right panel updates with new document
```

### GITHUB REPOSITORY FLOW

```
1. User enters repo URL and clicks "Fetch Repository"
   ↓
2. DocumentIngestionComponent.validateGitHubUrl()
   ├─ Validate format (regex)
   ├─ Extract owner/repo
   └─ Show status
   ↓
3. POST /import_repo with URL and optional token
   ↓
4. ingestion_routes.import_repo()
   ├─ Validate URL
   ├─ Call IngestionPipeline.ingest(SourceType.GITHUB, {...})
   │  ├─ GitHubFetcher.fetch_repository()
   │  ├─ _parse_repo_url() → extract owner/repo
   │  ├─ _get_default_branch()
   │  ├─ _traverse_tree() → recursive file listing
   │  ├─ Filter files (ignore node_modules, binary, large)
   │  ├─ Fetch content via GitHub API
   │  ├─ Pass to DocumentProcessor.parse_file()
   │  └─ Return IngestResult
   ├─ Store in SQLite
   ├─ Update usage stats
   └─ Return JSON response
   ↓
5. Frontend: Show count, reload on success
   ↓
6. Right panel shows all imported files
```

---

## 🔑 KEY CLASSES & INTERFACES

### IngestionPipeline

```python
class IngestionPipeline:
    def ingest(self, source_type: SourceType, data: dict) -> IngestResult:
        """
        Unified ingestion interface
        
        Args:
            source_type: SourceType.FILE or SourceType.GITHUB
            data: dict with source-specific parameters
            
        Returns:
            IngestResult with success bool, file count, file list, errors, warnings
        """
```

### IngestResult

```python
@dataclass
class IngestResult:
    success: bool
    count: int = 0
    files: list = None  # [{"filename": str, "filetype": str, "text": str}, ...]
    error: str = None
    warnings: list = None  # ["warning1", "warning2", ...]
```

### GitHubFetcher

```python
class GitHubFetcher:
    def fetch_repository(self, repo_url: str, token: str = None) -> dict:
        """
        Fetch repository contents recursively
        
        Returns:
            {
                "readme": "README content or None",
                "files": [
                    {
                        "path": "src/main.py",
                        "content": "file contents"
                    },
                    ...
                ]
            }
        """
```

---

## ⚙️ CONFIGURATION

### Environment Variables

```bash
GITHUB_API_TOKEN=ghp_xxx...  # Optional: For authenticated requests
UPLOAD_FOLDER=uploads        # Where to store temp uploads
MAX_FILE_SIZE=1048576        # 1MB per file limit
MAX_REPO_SIZE=52428800       # 50MB total repo limit
```

### GitHub API Rate Limits

**Without token**:
- 60 requests/hour per IP
- Limited to public repos

**With token**:
- 5,000 requests/hour per user
- Access to private repos

For production, use a dedicated GitHub service account token.

---

## 🐛 DEBUGGING

### Enable Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
```

### Common Issues

1. **GitHub API Rate Limit**
   - Solution: Add token to request or wait 1 hour
   - Check: `X-RateLimit-Remaining` response header

2. **Large File Processing**
   - Solution: Implement chunking in DocumentProcessor
   - Check: File size validation before processing

3. **Encoding Issues**
   - Solution: Already handled with utf-8 fallback
   - Check: Review encoding in document_processing.py

4. **Network Timeout**
   - Solution: Add timeout parameter to requests
   - Check: Timeout configuration in github_fetcher_v2.py

---

## 📈 PERFORMANCE CONSIDERATIONS

### File Processing

- **Chunking**: For very large files (>10MB), implement streaming
- **Caching**: Store processed documents to avoid re-processing
- **Async**: Use async tasks (Celery) for slow operations

### GitHub API

- **Pagination**: Implement for repos with many files
- **Caching**: Cache API responses for 1 hour
- **Rate Limiting**: Track requests and queue overages

### Database

- **Indexing**: Add index on (filetype, created_at) for queries
- **Cleanup**: Remove old documents periodically
- **Backup**: Regular SQLite backups

---

## 🚀 DEPLOYMENT CHECKLIST

- [ ] Update all routes to use IngestionPipeline
- [ ] Test local file upload (small and large files)
- [ ] Test GitHub import (public and private repos)
- [ ] Verify error handling for edge cases
- [ ] Add GitHub token to environment (if needed)
- [ ] Configure rate limiting (if applicable)
- [ ] Set up logging/monitoring
- [ ] Test on production-like environment
- [ ] Update documentation for users
- [ ] Backup existing database before deploying

---

## 📝 FUTURE EXTENSIONS

The unified `ingest(source_type, data)` interface makes it easy to add new sources:

### Google Drive
```python
class GoogleDriveIngester:
    def ingest(self, folder_id: str, token: str) -> IngestResult:
        # Fetch files from Google Drive
        # Use same DocumentProcessor
        # Return IngestResult
```

### AWS S3
```python
class S3Ingester:
    def ingest(self, bucket: str, prefix: str) -> IngestResult:
        # Fetch files from S3
        # Use same DocumentProcessor
        # Return IngestResult
```

### GitLab, Bitbucket
```python
# Follow same pattern as GitHub fetcher
```

---

## 📞 SUPPORT

For issues or questions, check:
1. Log files for errors
2. GitHub API documentation
3. Document processing implementation
4. Network connectivity

---

## 📄 FILES SUMMARY

| File | Purpose | Status |
|------|---------|--------|
| `app/ingestion.py` | Unified pipeline | ✅ Created |
| `app/github_fetcher_v2.py` | GitHub API client | ✅ Created |
| `app/ingestion_routes.py` | HTTP endpoints | ✅ Created |
| `templates/index_v2.html` | UI template | ✅ Created |
| `static/js/document-ingestion.js` | Frontend logic | ✅ Created |
| `static/css/ingestion.css` | Styles | ✅ Created |
| `app/routes.py` | Main routes | ⏳ To be updated |

---

Generated: Production Architecture Implementation
Version: 1.0
