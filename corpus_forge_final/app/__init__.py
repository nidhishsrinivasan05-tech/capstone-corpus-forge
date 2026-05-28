import os
from flask import Flask
from .document_processing import MAX_FILE_SIZE_BYTES
from .routes import bp
from .storage import init_db


def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config["SECRET_KEY"] = os.environ.get("CORPUS_FORGE_SECRET", "corpus-forge-dev-key")
    app.config["UPLOAD_FOLDER"] = os.environ.get("CORPUS_FORGE_UPLOADS", "data/uploads")
    app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE_BYTES
    init_db()
    app.register_blueprint(bp)
    return app
