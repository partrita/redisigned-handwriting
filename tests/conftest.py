"""
Pytest configuration and fixtures for transcription-game tests.
"""

import pytest
import tempfile
import os
import sys
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from handwriting_transcription.app import create_app
from handwriting_transcription.font_manager import FontManager
from handwriting_transcription.pdf_generator import PDFGenerator
from handwriting_transcription.text_processor import TextProcessor


@pytest.fixture
def app():
    """Create and configure a test Flask app."""
    app = create_app("testing")
    app.config.update(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "MAX_TEXT_LENGTH": 1000,  # Smaller limit for testing
            "PDF_TIMEOUT": 10,
        }
    )

    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    """Create a test client for the Flask app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test runner for the Flask app."""
    return app.test_cli_runner()


@pytest.fixture
def font_manager():
    """Create a FontManager instance for testing."""
    return FontManager()


@pytest.fixture
def pdf_generator():
    """Create a PDFGenerator instance for testing."""
    return PDFGenerator()


@pytest.fixture
def text_processor():
    """Create a TextProcessor instance for testing."""
    return TextProcessor()


@pytest.fixture
def sample_text():
    """Sample text for testing."""
    return "The quick brown fox jumps over the lazy dog.\nThis is a second line.\nAnd a third line."


@pytest.fixture
def sample_options():
    """Sample options for testing."""
    return {
        "font_name": "Helvetica",
        "font_size": 12,
        "document_size": "A4",
        "guidelines": True,
        "guideline_type": "ruled",
        "black_text": True,
        "gray_text": False,
        "blank_lines": False,
    }


@pytest.fixture
def temp_pdf_file():
    """Create a temporary PDF file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        yield f.name
    # Cleanup
    try:
        os.unlink(f.name)
    except FileNotFoundError:
        pass


@pytest.fixture
def mock_font_loading():
    """Mock font loading to avoid system dependencies in tests."""
    with patch("handwriting_transcription.font_manager.pdfmetrics.registerFont"):
        with patch("handwriting_transcription.font_manager.TTFont"):
            yield


@pytest.fixture
def mock_canvas():
    """Mock ReportLab canvas for testing."""
    mock = Mock()
    mock._pagesize = (595.276, 841.89)  # A4 size in points
    mock.stringWidth.return_value = 100.0
    return mock


class TestConfig:
    """Test configuration."""

    TESTING = True
    SECRET_KEY = "test-secret-key"
    WTF_CSRF_ENABLED = False
    MAX_TEXT_LENGTH = 1000
    PDF_TIMEOUT = 10
