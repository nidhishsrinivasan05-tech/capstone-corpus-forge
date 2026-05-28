"""
UPDATED ROUTES using unified ingestion pipeline
Drop-in replacement for key upload/import endpoints
"""

from flask import request, jsonify, flash, redirect, url_for
import logging
from werkzeug.utils import secure_filename
import os

logger = logging.getLogger(__name__)


def create_ingestion_routes(bp, app_config):
    """
    Factory function to create routes using ingestion pipeline
    
    Usage in main routes.py:
        from .ingestion_routes import create_ingestion_routes
        create_ingestion_routes(bp, current_app.config)
    """
    from .ingestion import IngestionPipeline, SourceType
    from .storage import get_connection, now, add_usage
    from .document_processing import estimate_tokens
    
    pipeline = IngestionPipeline()
    
    @bp.route("/upload_file", methods=["POST"])
    def upload_file():
        """Handle local file upload with ingestion pipeline"""
        
        # Check if file in request
        if "file" not in request.files:
            error_msg = "No file provided"
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"status": "error", "error": error_msg}), 400
            flash(error_msg, "error")
            return redirect(url_for("main.index"))
        
        file = request.files["file"]
        
        if not file or file.filename == "":
            error_msg = "No file selected"
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"status": "error", "error": error_msg}), 400
            flash(error_msg, "error")
            return redirect(url_for("main.index"))
        
        try:
            # Save uploaded file temporarily
            filename = secure_filename(file.filename)
            upload_dir = os.path.join(app_config["UPLOAD_FOLDER"])
            os.makedirs(upload_dir, exist_ok=True)
            
            temp_path = os.path.join(upload_dir, filename)
            file.save(temp_path)
            
            # Ingest using pipeline
            result = pipeline.ingest(SourceType.FILE, {
                "path": temp_path,
                "filename": filename
            })
            
            # Handle result
            if not result.success:
                os.remove(temp_path) if os.path.exists(temp_path) else None
                error_msg = result.error or "File processing failed"
                
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return jsonify({"status": "error", "error": error_msg}), 400
                
                flash(error_msg, "error")
                return redirect(url_for("main.index"))
            
            # Store in database
            with get_connection() as db:
                for file_data in result.files:
                    db.execute(
                        "INSERT INTO documents (filename, filetype, text, created_at) VALUES (?, ?, ?, ?)",
                        (file_data["filename"], file_data["filetype"], file_data["text"], now())
                    )
                    db.commit()
                    
                    # Update usage stats
                    add_usage(estimate_tokens(file_data["text"]))
            
            # Cleanup temp file
            os.remove(temp_path) if os.path.exists(temp_path) else None
            
            success_msg = f"Successfully uploaded and processed '{filename}'"
            
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({
                    "status": "ok",
                    "count": result.count,
                    "message": success_msg
                }), 200
            
            flash(success_msg, "success")
            return redirect(url_for("main.index"))
        
        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            os.remove(temp_path) if os.path.exists(temp_path) else None
            
            error_msg = f"Upload failed: {str(e)}"
            
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"status": "error", "error": error_msg}), 500
            
            flash(error_msg, "error")
            return redirect(url_for("main.index"))
    
    @bp.route("/import_repo", methods=["POST"])
    def import_repo():
        """Handle GitHub repository import with ingestion pipeline"""
        
        repo_url = request.form.get("repo_url", "").strip()
        github_token = request.form.get("github_token", "").strip() or None
        
        if not repo_url:
            error_msg = "Repository URL is required"
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"status": "error", "error": error_msg}), 400
            flash(error_msg, "error")
            return redirect(url_for("main.index"))
        
        try:
            # Ingest using pipeline
            result = pipeline.ingest(SourceType.GITHUB, {
                "url": repo_url,
                "token": github_token
            })
            
            # Handle result
            if not result.success:
                error_msg = result.error or "Repository import failed"
                
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return jsonify({"status": "error", "error": error_msg}), 400
                
                flash(error_msg, "error")
                return redirect(url_for("main.index"))
            
            # Store in database
            with get_connection() as db:
                for file_data in result.files:
                    # Use path as display name if available
                    display_name = f"{repo_url.split('/')[-1]}/{file_data['filename']}"
                    
                    db.execute(
                        "INSERT INTO documents (filename, filetype, text, created_at) VALUES (?, ?, ?, ?)",
                        (display_name, file_data["filetype"], file_data["text"], now())
                    )
                    db.commit()
                    
                    # Update usage stats
                    add_usage(estimate_tokens(file_data["text"]))
            
            success_msg = f"Successfully imported {result.count} files from repository"
            
            # Log warnings if any
            for warning in result.warnings:
                logger.warning(f"Import warning: {warning}")
            
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({
                    "status": "ok",
                    "count": result.count,
                    "message": success_msg,
                    "warnings": result.warnings if result.warnings else None
                }), 200
            
            flash(success_msg, "success")
            return redirect(url_for("main.index"))
        
        except Exception as e:
            logger.error(f"GitHub import error: {str(e)}")
            
            error_msg = f"Import failed: {str(e)}"
            
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"status": "error", "error": error_msg}), 500
            
            flash(error_msg, "error")
            return redirect(url_for("main.index"))
    
    return {
        "upload_file": upload_file,
        "import_repo": import_repo
    }
