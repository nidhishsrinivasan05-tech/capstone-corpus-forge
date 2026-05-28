#!/usr/bin/env python3
"""
INTEGRATION HELPER: Quick setup for production architecture

Usage:
  python integrate.py

This script helps integrate the new production-grade components into your Corpus Forge app.
"""

import os
import sys
import shutil
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_step(num, text):
    print(f"[{num}] {text}")

def check_file_exists(path):
    return os.path.exists(path)

def integrate():
    print_header("CORPUS FORGE PRODUCTION ARCHITECTURE INTEGRATION")
    
    base_dir = Path(__file__).parent / "corpus_forge_final"
    app_dir = base_dir / "app"
    static_dir = base_dir / "static"
    templates_dir = base_dir / "templates"
    
    print("📍 Base Directory:", base_dir)
    
    if not app_dir.exists():
        print("❌ Error: corpus_forge_final/app not found")
        return False
    
    print("\n✅ Directory structure verified\n")
    
    # Check new files exist
    print_step(1, "Checking new component files...")
    
    new_files = {
        "app/ingestion.py": "Unified ingestion pipeline",
        "app/github_fetcher_v2.py": "Enhanced GitHub fetcher",
        "app/ingestion_routes.py": "API endpoints",
        "static/js/document-ingestion.js": "Frontend component",
        "static/css/ingestion.css": "Stylesheet",
        "templates/index_v2.html": "Updated HTML template",
    }
    
    missing = []
    for rel_path, desc in new_files.items():
        full_path = base_dir / rel_path
        if check_file_exists(full_path):
            print(f"  ✅ {rel_path:40} ({desc})")
        else:
            print(f"  ❌ {rel_path:40} MISSING")
            missing.append(rel_path)
    
    if missing:
        print(f"\n⚠️  Missing files: {', '.join(missing)}")
        print("   Make sure all new files are in place before integrating.")
        return False
    
    # Integration instructions
    print_step(2, "Integration Instructions")
    
    instructions = """
    
    🔧 MANUAL STEPS REQUIRED:
    
    1. UPDATE routes.py:
       ─────────────────
       Add these imports:
       
       from .ingestion_routes import create_ingestion_routes
       from .ingestion import IngestionPipeline, SourceType
       
       In your route blueprints setup, add:
       
       ingestion_routes = create_ingestion_routes(bp, current_app.config)
       
       This replaces the old /upload_file and /import_repo endpoints.
    
    
    2. UPDATE HTML TEMPLATE:
       ──────────────────────
       Option A: Replace templates/index.html with templates/index_v2.html
       
       Option B: Add to your existing template:
       
       <link rel="stylesheet" href="{{ url_for('static', filename='css/ingestion.css') }}">
       <script src="{{ url_for('static', filename='js/document-ingestion.js') }}"></script>
    
    
    3. UPDATE Document List in template:
       ──────────────────────────────────
       Replace your document display section with the markup from index_v2.html:
       - Source selector (lines 20-31)
       - Upload form (lines 34-78)
       - Document preview cards (lines 109-142)
    
    
    4. CONFIGURE Flask:
       ─────────────────
       Ensure your Flask app config has:
       
       UPLOAD_FOLDER = 'uploads'
       MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    
    
    5. TEST INTEGRATION:
       ──────────────────
       $ python run.py
       
       Then:
       - Test local file upload
       - Test GitHub repo import
       - Check error handling
       - Verify document preview works
    
    
    📚 DOCUMENTATION:
    ─────────────────
    Read these files for details:
    - ARCHITECTURE.md - System design & integration guide
    - IMPLEMENTATION_SUMMARY.md - What changed & why
    
    
    🚀 DEPLOYMENT:
    ──────────────
    When ready for production:
    1. Backup existing database
    2. Test on staging environment
    3. Monitor logs for errors
    4. Optionally add GitHub token to environment
    """
    
    print(instructions)
    
    # Configuration template
    print_step(3, "Configuration Template")
    
    config_template = """
    
    Add to your Flask app configuration (app/config.py or similar):
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'txt', 'json', 'csv', 'html', 'py', 'js', 'java', 'cpp'}
    
    # GitHub API Configuration
    GITHUB_API_TOKEN = os.environ.get('GITHUB_API_TOKEN')  # Optional
    GITHUB_MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB per file
    GITHUB_MAX_REPO_SIZE = 50 * 1024 * 1024  # 50MB total
    GITHUB_IGNORED_DIRS = {'node_modules', '.git', '__pycache__', '.venv', 'venv'}
    GITHUB_IGNORED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'zip', 'tar', 'gz'}
    
    # Document Processing
    DOCUMENT_ENCODING = 'utf-8'
    DOCUMENT_CHUNK_SIZE = 10000  # chars
    """
    
    print(config_template)
    
    # Testing instructions
    print_step(4, "Testing Checklist")
    
    tests = """
    
    Before deploying, verify:
    
    □ Local file upload works (small file)
    □ Local file upload works (large file)
    □ PDF parsing works
    □ JSON parsing works
    □ Code file parsing works
    □ GitHub repo import works (public repo)
    □ GitHub repo import works (with token for private)
    □ Invalid GitHub URL shows error
    □ Non-existent repo shows error
    □ Document preview shows short text
    □ "View more" expands full text
    □ "Show less" collapses
    □ Toast notifications appear
    □ Loading states show
    □ Source toggle switches forms
    □ Drag & drop file upload works
    """
    
    print(tests)
    
    print_step(5, "Next Steps")
    
    next_steps = """
    
    1. Read ARCHITECTURE.md for system design details
    2. Review the integration steps above
    3. Update your routes.py file
    4. Update your HTML template
    5. Test thoroughly in development
    6. Deploy to staging
    7. Monitor logs
    8. Deploy to production
    
    Questions? Check:
    - IMPLEMENTATION_SUMMARY.md for what changed
    - app/ingestion.py for pipeline logic
    - static/js/document-ingestion.js for frontend logic
    """
    
    print(next_steps)
    
    print_header("INTEGRATION READY")
    print("✅ All files present and ready for integration")
    print("\nNext: Follow the manual steps above to integrate into your app.")
    print("📖 Read ARCHITECTURE.md for complete documentation.\n")
    
    return True

if __name__ == "__main__":
    try:
        success = integrate()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
