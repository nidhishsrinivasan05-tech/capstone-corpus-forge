"""
INTEGRATION CODE SNIPPETS
Copy-paste these exact snippets to integrate the new architecture into your app
"""

# ============================================================
# SNIPPET 1: Update app/__init__.py or main routes setup
# ============================================================

"""
File: app/__init__.py or routes setup section

WHERE TO ADD THIS:
After creating your Flask blueprint, add the ingestion routes.
"""

# Add this import at the top:
from .ingestion_routes import create_ingestion_routes
from .ingestion import IngestionPipeline, SourceType

# Add this in your blueprint registration section:
def init_app(app):
    # ... existing blueprint registration ...
    
    # NEW: Register ingestion routes
    from .main_bp import bp  # or whatever your blueprint is called
    ingestion_routes = create_ingestion_routes(bp, app.config)
    
    app.register_blueprint(bp)


# ============================================================
# SNIPPET 2: Flask Configuration
# ============================================================

"""
File: app/config.py or similar

Add these configuration settings to your Flask config
"""

import os

class Config:
    # File Upload Configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'txt', 'json', 'csv', 'html', 'py', 'js', 'java', 'cpp', 'go', 'rs'}
    
    # GitHub API Configuration
    GITHUB_API_TOKEN = os.environ.get('GITHUB_API_TOKEN')  # Optional
    GITHUB_MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB per file
    GITHUB_MAX_REPO_SIZE = 50 * 1024 * 1024  # 50MB total
    GITHUB_IGNORED_DIRS = {'node_modules', '.git', '__pycache__', '.venv', 'venv', '.github'}
    GITHUB_IGNORED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'zip', 'tar', 'gz', 'bin', 'exe', 'so', 'dll'}
    
    # Document Processing
    DOCUMENT_ENCODING = 'utf-8'
    DOCUMENT_CHUNK_SIZE = 10000  # characters
    
    # Logging
    LOG_LEVEL = 'DEBUG'  # or 'INFO' for production


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    LOG_LEVEL = 'INFO'


class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    UPLOAD_FOLDER = '/tmp/test_uploads'


# ============================================================
# SNIPPET 3: Update HTML Template - Imports
# ============================================================

"""
File: templates/base.html or templates/index.html

Add these two lines to the <head> section or before closing </body>
"""

<!-- Add to <head> for styling: -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/ingestion.css') }}">

<!-- Add before </body> for functionality: -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<script src="{{ url_for('static', filename='js/document-ingestion.js') }}"></script>


# ============================================================
# SNIPPET 4: Update HTML Template - Source Selector Markup
# ============================================================

"""
File: templates/index.html

Add this to your left panel where you have document upload.
Replace or add alongside your existing upload form.
"""

<!-- SOURCE SELECTOR -->
<div class="source-selector-container">
    <button class="source-toggle" id="source-toggle">
        <span id="source-label">Local</span>
    </button>
    <select id="source-select">
        <option value="local">Local Files</option>
        <option value="github">GitHub Repository</option>
    </select>
</div>

<!-- LOCAL FILE UPLOAD FORM -->
<form id="upload-form" class="form-section active-form upload-form">
    <div class="file-input-wrapper">
        <input type="file" id="file-input" name="file" accept="*" required>
        <label for="file-input" class="file-input-label">
            <span class="file-input-hint">
                Click or drag file here<br>
                <small>Supports: PDF, TXT, JSON, CSV, HTML, Code files</small>
            </span>
        </label>
    </div>
    <button type="submit" class="btn btn-primary">
        📤 Upload & Process
    </button>
</form>

<!-- GITHUB REPOSITORY FORM -->
<form id="repo-form" class="form-section repo-form">
    <div class="form-group">
        <label class="form-label">GitHub Repository URL</label>
        <input
            type="text"
            id="repo_url"
            name="repo_url"
            class="form-input"
            placeholder="https://github.com/owner/repository"
            required
        >
        <small class="form-hint">
            Public or private (requires personal access token)
        </small>
    </div>

    <div class="form-group">
        <label class="form-label">
            GitHub Personal Access Token (Optional)
        </label>
        <input
            type="password"
            id="github_token"
            name="github_token"
            class="form-input"
            placeholder="Leave blank for public repos"
        >
        <small class="form-hint">
            Only sent to GitHub API, never stored
        </small>
    </div>

    <div id="repo-status"></div>

    <button type="button" id="fetch-repo-btn" class="btn btn-primary">
        🔗 Fetch Repository
    </button>
</form>


# ============================================================
# SNIPPET 5: Update HTML Template - Document Cards
# ============================================================

"""
File: templates/index.html (right panel)

Replace your document display section with this.
This shows the new expandable preview cards.
"""

<!-- DOCUMENTS LIST (RIGHT PANEL) -->
<div class="documents-list">
    {% for doc in documents %}
        <div class="doc-row" data-doc-id="{{ doc.id }}">
            <div class="doc-header">
                <div class="doc-info">
                    <div class="doc-name">
                        {{ doc.filename }}
                    </div>
                    <div class="doc-meta">
                        <span class="doc-type">{{ doc.filetype }}</span>
                        <span class="doc-size">{{ (doc.text|length) }} chars</span>
                        <span class="doc-date">{{ doc.created_at }}</span>
                    </div>
                </div>
                <button class="btn-actions" title="Document actions">⋮</button>
            </div>

            <!-- SHORT PREVIEW (Always visible) -->
            <div class="doc-preview-short">
                {{ doc.text[:100] }}{% if doc.text|length > 100 %}...{% endif %}
            </div>

            <!-- FULL PREVIEW (Expandable) -->
            <div class="doc-full-preview" style="display: none;">
                <pre><code>{{ doc.text }}</code></pre>
            </div>

            <!-- ACTIONS -->
            <div class="doc-actions">
                <button class="btn-view-more" data-expanded="false">
                    View more
                </button>
                <form method="POST" action="{{ url_for('main.delete_document', doc_id=doc.id) }}" style="display: inline;">
                    <button type="submit" class="btn btn-danger" 
                            onclick="return confirm('Delete this document?')">
                        🗑️ Delete
                    </button>
                </form>
            </div>
        </div>
    {% endfor %}
</div>

<!-- EMPTY STATE -->
{% if not documents %}
    <div class="empty-state">
        <p>📭 No documents loaded yet.</p>
        <p>Start by uploading files or importing a GitHub repository.</p>
    </div>
{% endif %}


# ============================================================
# SNIPPET 6: Toast Notification System (Optional Enhancement)
# ============================================================

"""
Add this to your template to show toast notifications.
Already included in document-ingestion.js, but you can customize.
"""

<!-- Toast Container (add to template) -->
<div class="toast-container" id="toast-container"></div>

<!-- Toast JavaScript (add to template, before other scripts) -->
<script>
    class ToastNotifier {
        constructor() {
            this.container = document.getElementById('toast-container');
            document.addEventListener('show-toast', (e) => this.show(e.detail));
        }

        show(options) {
            const { message, type = 'info', duration = 4000 } = options;
            
            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            toast.textContent = message;
            toast.setAttribute('role', 'alert');

            this.container.appendChild(toast);

            setTimeout(() => {
                toast.classList.add('exit');
                setTimeout(() => toast.remove(), 300);
            }, duration);
        }
    }

    new ToastNotifier();
</script>


# ============================================================
# SNIPPET 7: Programmatic Usage (Python)
# ============================================================

"""
If you want to use the pipeline directly in your code (not via HTTP)
"""

from app.ingestion import IngestionPipeline, SourceType

# Initialize
pipeline = IngestionPipeline()

# Ingest local file
result = pipeline.ingest(SourceType.FILE, {
    "path": "/path/to/file.txt",
    "filename": "file.txt"
})

if result.success:
    print(f"Processed {result.count} files")
    for file in result.files:
        print(f"  - {file['filename']} ({file['filetype']})")
else:
    print(f"Error: {result.error}")
    if result.warnings:
        for w in result.warnings:
            print(f"  Warning: {w}")

# Ingest GitHub repo
result = pipeline.ingest(SourceType.GITHUB, {
    "url": "https://github.com/owner/repo",
    "token": "ghp_xxx..."  # Optional
})

if result.success:
    print(f"Imported {result.count} files from GitHub")
else:
    print(f"Error: {result.error}")


# ============================================================
# SNIPPET 8: Error Handling (Optional - for custom handling)
# ============================================================

"""
Add this to handle errors gracefully in your custom code
"""

from app.ingestion import IngestionPipeline, SourceType, GitHubFetchError

pipeline = IngestionPipeline()

try:
    result = pipeline.ingest(SourceType.GITHUB, {
        "url": "https://github.com/owner/repo",
        "token": None
    })
    
    if not result.success:
        # Handle application error
        log_error(f"Ingestion failed: {result.error}")
        for warning in result.warnings or []:
            log_warning(warning)
    else:
        # Success
        save_documents(result.files)
        
except GitHubFetchError as e:
    # Handle GitHub-specific error
    log_error(f"GitHub error: {str(e)}")
    notify_user("GitHub API error. Please check URL and try again.")
    
except Exception as e:
    # Handle unexpected error
    log_error(f"Unexpected error: {str(e)}")
    notify_user("An unexpected error occurred. Please try again.")


# ============================================================
# SNIPPET 9: Environment Setup for GitHub Tokens
# ============================================================

"""
Bash/Shell script to set up GitHub token for local development

Save as: setup_github_token.sh
Run: source setup_github_token.sh
"""

#!/bin/bash

# Generate a token at: https://github.com/settings/tokens
# With scope: "repo" (for private repos) or "public_repo" (for public only)

read -p "Enter your GitHub Personal Access Token: " token

export GITHUB_API_TOKEN="$token"

echo "✓ GitHub token set in environment"
echo "  To make it permanent, add to ~/.bashrc or ~/.zshrc:"
echo "  export GITHUB_API_TOKEN=\"$token\""


# ============================================================
# SNIPPET 10: Database Migration (if needed)
# ============================================================

"""
If you're adding new columns to documents table,
run this migration (one-time only)
"""

import sqlite3

conn = sqlite3.connect('corpus.db')
cursor = conn.cursor()

# Add new columns if they don't exist (safe operation)
try:
    cursor.execute("ALTER TABLE documents ADD COLUMN source_type TEXT DEFAULT 'file'")
    cursor.execute("ALTER TABLE documents ADD COLUMN source_url TEXT")
    cursor.execute("ALTER TABLE documents ADD COLUMN processed_at TIMESTAMP")
    conn.commit()
    print("✓ Database migration complete")
except sqlite3.OperationalError as e:
    print(f"✓ Columns already exist or error: {e}")
finally:
    conn.close()


# ============================================================
# All snippets end here
# ============================================================

"""
USAGE INSTRUCTIONS:

1. SNIPPET 1: Copy to app/__init__.py (register ingestion routes)
2. SNIPPET 2: Copy to app/config.py (add configuration)
3. SNIPPET 3: Add to base HTML template (imports)
4. SNIPPET 4: Add to left panel in HTML (source selector & forms)
5. SNIPPET 5: Replace document display in HTML (expandable cards)
6. SNIPPET 6: Add to HTML (toast notifications)
7. SNIPPET 7: Optional - use in your Python code
8. SNIPPET 8: Optional - custom error handling
9. SNIPPET 9: Optional - GitHub token setup script
10. SNIPPET 10: Optional - database migration

After integrating:
1. Test local file upload
2. Test GitHub import
3. Check that source toggle works
4. Verify document preview expands/collapses
5. Confirm error messages show properly

IMPORTANT: Make sure all 6 new files are copied to your app directory first!
"""
