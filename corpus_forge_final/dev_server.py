import os

from app import create_app


port = int(os.environ.get("CORPUS_FORGE_PORT", "5000"))
create_app().run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
