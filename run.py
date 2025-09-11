#!/usr/bin/env python3
"""
Entry point for running the transcription game Flask application.
"""

from src.handwriting_transcription.app import create_app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5001)
