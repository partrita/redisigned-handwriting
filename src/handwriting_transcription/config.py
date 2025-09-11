"""
Configuration module for transcription-game application.
"""

import os


class Config:
    """Base configuration class."""

    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    MAX_TEXT_LENGTH = 10000  # Maximum text length for processing
    PDF_TIMEOUT = 30  # PDF generation timeout in seconds

    # Font configuration
    FONT_CACHE_TTL = 3600  # Font cache TTL in seconds (1 hour)
    MAX_FONT_CACHE_SIZE = 1000  # Maximum number of cached font items

    # Rate limiting configuration
    PDF_RATE_LIMIT = 5  # PDFs per minute
    PREVIEW_RATE_LIMIT = 30  # Previews per minute
    API_RATE_LIMIT = 100  # API calls per minute
    RATE_LIMIT_WINDOW = 60  # Rate limit window in seconds


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing configuration."""

    DEBUG = False
    TESTING = True
    WTF_CSRF_ENABLED = False
    MAX_TEXT_LENGTH = 1000  # Smaller limit for testing
    PDF_TIMEOUT = 10  # Shorter timeout for testing


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    TESTING = False

    # More restrictive limits for production
    MAX_TEXT_LENGTH = 5000
    PDF_TIMEOUT = 20

    # Tighter rate limits for production
    PDF_RATE_LIMIT = 3
    PREVIEW_RATE_LIMIT = 20
    API_RATE_LIMIT = 50


# Configuration mapping
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
