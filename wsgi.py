"""
WSGI Entrypoint for CertChain Blockchain Certificate Verification System.
Compatible with Gunicorn, Waitress, uWSGI, and cloud platforms (Render, Railway, Heroku, AWS, Docker).
"""

import os
from app import app

# Ensure app is accessible as 'app' or 'application'
application = app

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))
    app.run(host=host, port=port)
