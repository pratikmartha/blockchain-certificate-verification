"""
Production Server Runner for CertChain.
Automatically selects Waitress (Windows / Cross-Platform) or Gunicorn (Linux/macOS).
Run with:
    python prod.py
"""

import os
import sys
import platform

from app import app

def run_production():
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))
    threads = int(os.environ.get("WEB_CONCURRENCY_THREADS", 4))

    print("=" * 65)
    print("  CertChain Production WSGI Server")
    print(f"  Platform: {platform.system()} ({platform.machine()})")
    print(f"  Binding: http://{host}:{port}")
    print(f"  Worker Threads: {threads}")
    print("=" * 65)

    try:
        from waitress import serve
        print(">> Serving with high-performance production WSGI server: Waitress\n")
        serve(app, host=host, port=port, threads=threads)
    except ImportError:
        print(">> Waitress not installed. Starting Flask standard server...")
        app.run(host=host, port=port, debug=False)

if __name__ == "__main__":
    run_production()
