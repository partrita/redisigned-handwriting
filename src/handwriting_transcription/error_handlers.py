"""
Error handling module for comprehensive error management and user-friendly messages.
"""

import logging
import traceback
from typing import Dict, Any
from functools import wraps
from flask import jsonify, request


logger = logging.getLogger(__name__)


from .exceptions import ApplicationError


class ValidationError(ApplicationError):
    """Validation-specific error."""

    def __init__(self, message: str, field: str = None, user_message: str = None):
        super().__init__(
            message=message,
            user_message=user_message or f"Invalid input: {message}",
            error_code="VALIDATION_ERROR",
            status_code=400,
        )
        self.field = field


class FontError(ApplicationError):
    """Font-related error."""

    def __init__(self, message: str, font_name: str = None, user_message: str = None):
        super().__init__(
            message=message,
            user_message=user_message
            or "Font loading failed. Please try a different font.",
            error_code="FONT_ERROR",
            status_code=400,
        )
        self.font_name = font_name


class PDFGenerationError(ApplicationError):
    """PDF generation error."""

    def __init__(self, message: str, user_message: str = None):
        super().__init__(
            message=message,
            user_message=user_message
            or "PDF generation failed. Please check your input and try again.",
            error_code="PDF_GENERATION_ERROR",
            status_code=500,
        )


class PreviewGenerationError(ApplicationError):
    """Preview generation error."""

    def __init__(self, message: str, user_message: str = None):
        super().__init__(
            message=message,
            user_message=user_message
            or "Preview generation failed. Please check your input.",
            error_code="PREVIEW_ERROR",
            status_code=500,
        )


class RateLimitError(ApplicationError):
    """Rate limiting error."""

    def __init__(self, message: str = "Too many requests"):
        super().__init__(
            message=message,
            user_message="Too many requests. Please wait a moment and try again.",
            error_code="RATE_LIMIT_ERROR",
            status_code=429,
        )


class ContentTooLargeError(ApplicationError):
    """Content size error."""

    def __init__(self, message: str, max_size: int = None):
        user_msg = (
            "Content is too large. Please reduce the amount of text and try again."
        )
        if max_size:
            user_msg = f"Content is too large (maximum {max_size} characters). Please reduce the text and try again."

        super().__init__(
            message=message,
            user_message=user_msg,
            error_code="CONTENT_TOO_LARGE",
            status_code=413,
        )


def handle_application_errors(app):
    """Register error handlers with the Flask application."""

    @app.errorhandler(ApplicationError)
    def handle_application_error(error):
        """Handle custom application errors."""
        logger.error(f"Application error: {error.message}", exc_info=True)

        response = {
            "success": False,
            "error": error.user_message,
            "error_code": error.error_code,
            "details": error.message if app.debug else None,
        }

        # Add field information for validation errors
        if isinstance(error, ValidationError) and error.field:
            response["field"] = error.field

        # Add font information for font errors
        if isinstance(error, FontError) and error.font_name:
            response["font_name"] = error.font_name

        return jsonify(response), error.status_code

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Handle validation errors specifically."""
        logger.warning(f"Validation error: {error.message}")

        response = {
            "success": False,
            "error": error.user_message,
            "error_code": "VALIDATION_ERROR",
            "field": error.field,
        }

        return jsonify(response), 400

    @app.errorhandler(FontError)
    def handle_font_error(error):
        """Handle font-related errors."""
        logger.warning(f"Font error: {error.message}")

        response = {
            "success": False,
            "error": error.user_message,
            "error_code": "FONT_ERROR",
            "font_name": error.font_name,
            "suggestion": "Please try selecting a different font from the dropdown.",
        }

        return jsonify(response), 400

    @app.errorhandler(PDFGenerationError)
    def handle_pdf_error(error):
        """Handle PDF generation errors."""
        logger.error(f"PDF generation error: {error.message}", exc_info=True)

        response = {
            "success": False,
            "error": error.user_message,
            "error_code": "PDF_GENERATION_ERROR",
            "suggestions": [
                "Check that your text content is not too long",
                "Try using a different font",
                "Ensure your formatting options are valid",
            ],
        }

        return jsonify(response), 500

    @app.errorhandler(PreviewGenerationError)
    def handle_preview_error(error):
        """Handle preview generation errors."""
        logger.warning(f"Preview generation error: {error.message}")

        response = {
            "success": False,
            "error": error.user_message,
            "error_code": "PREVIEW_ERROR",
            "fallback": True,
        }

        return jsonify(response), 500

    @app.errorhandler(RateLimitError)
    def handle_rate_limit_error(error):
        """Handle rate limiting errors."""
        logger.warning(f"Rate limit exceeded: {request.remote_addr}")

        response = {
            "success": False,
            "error": error.user_message,
            "error_code": "RATE_LIMIT_ERROR",
            "retry_after": 60,  # seconds
        }

        return jsonify(response), 429

    @app.errorhandler(ContentTooLargeError)
    def handle_content_too_large_error(error):
        """Handle content size errors."""
        logger.warning(f"Content too large: {error.message}")

        response = {
            "success": False,
            "error": error.user_message,
            "error_code": "CONTENT_TOO_LARGE",
        }

        return jsonify(response), 413

    @app.errorhandler(400)
    def handle_bad_request(error):
        """Handle generic bad request errors."""
        logger.warning(f"Bad request: {error}")

        response = {
            "success": False,
            "error": "Invalid request. Please check your input and try again.",
            "error_code": "BAD_REQUEST",
        }

        return jsonify(response), 400

    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle not found errors."""
        # For API endpoints, return JSON
        if request.path.startswith("/api/"):
            response = {
                "success": False,
                "error": "API endpoint not found",
                "error_code": "NOT_FOUND",
            }
            return jsonify(response), 404

        # For web pages, render the main page
        from flask import render_template

        return render_template("index.html"), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Handle method not allowed errors."""
        response = {
            "success": False,
            "error": "HTTP method not allowed for this endpoint",
            "error_code": "METHOD_NOT_ALLOWED",
        }

        return jsonify(response), 405

    @app.errorhandler(413)
    def handle_payload_too_large(error):
        """Handle payload too large errors."""
        response = {
            "success": False,
            "error": "Request payload is too large. Please reduce the content size.",
            "error_code": "PAYLOAD_TOO_LARGE",
        }

        return jsonify(response), 413

    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle internal server errors."""
        logger.error(f"Internal server error: {error}", exc_info=True)

        response = {
            "success": False,
            "error": "An internal server error occurred. Please try again later.",
            "error_code": "INTERNAL_ERROR",
        }

        # Include error details in debug mode
        if app.debug:
            response["details"] = str(error)

        return jsonify(response), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle unexpected errors."""
        logger.error(f"Unexpected error: {error}", exc_info=True)

        response = {
            "success": False,
            "error": "An unexpected error occurred. Please try again.",
            "error_code": "UNEXPECTED_ERROR",
        }

        # Include traceback in debug mode
        if app.debug:
            response["traceback"] = traceback.format_exc()

        return jsonify(response), 500


def with_error_handling(error_type: type = ApplicationError):
    """
    Decorator for wrapping functions with error handling.

    Args:
        error_type: Type of error to catch and convert
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except error_type:
                # Re-raise application errors as-is
                raise
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
                # Convert to application error
                raise error_type(f"Operation failed: {str(e)}")

        return wrapper

    return decorator


def with_validation_error_handling(func):
    """Decorator specifically for validation error handling."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Validation error in {func.__name__}: {e}", exc_info=True)
            raise ValidationError(f"Validation failed: {str(e)}")

    return wrapper


def with_font_error_handling(func):
    """Decorator specifically for font error handling."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FontError:
            raise
        except Exception as e:
            logger.error(f"Font error in {func.__name__}: {e}", exc_info=True)
            raise FontError(f"Font operation failed: {str(e)}")

    return wrapper


def with_pdf_error_handling(func):
    """Decorator specifically for PDF generation error handling."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except PDFGenerationError:
            raise
        except MemoryError as e:
            logger.error(f"PDF generation memory error: {e}")
            raise ContentTooLargeError("Content is too large for PDF generation")
        except Exception as e:
            logger.error(f"PDF generation error in {func.__name__}: {e}", exc_info=True)
            raise PDFGenerationError(f"PDF generation failed: {str(e)}")

    return wrapper


def with_preview_error_handling(func):
    """Decorator specifically for preview generation error handling."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except PreviewGenerationError:
            raise
        except Exception as e:
            logger.error(
                f"Preview generation error in {func.__name__}: {e}", exc_info=True
            )
            raise PreviewGenerationError(f"Preview generation failed: {str(e)}")

    return wrapper


class ErrorContext:
    """Context manager for handling errors with additional context."""

    def __init__(self, operation: str, error_type: type = ApplicationError):
        self.operation = operation
        self.error_type = error_type

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type and not issubclass(exc_type, ApplicationError):
            logger.error(f"Error in {self.operation}: {exc_val}", exc_info=True)
            raise self.error_type(f"{self.operation} failed: {str(exc_val)}")
        return False


def log_error_details(error: Exception, context: Dict[str, Any] = None):
    """
    Log detailed error information for debugging.

    Args:
        error: Exception that occurred
        context: Additional context information
    """
    error_details = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context or {},
    }

    if hasattr(error, "error_code"):
        error_details["error_code"] = error.error_code

    logger.error(f"Error details: {error_details}", exc_info=True)


def create_user_friendly_message(error: Exception) -> str:
    """
    Create a user-friendly error message from an exception.

    Args:
        error: Exception to convert

    Returns:
        User-friendly error message
    """
    if isinstance(error, ApplicationError):
        return error.user_message

    error_type = type(error).__name__

    # Map common error types to user-friendly messages
    error_messages = {
        "ValueError": "Invalid input provided. Please check your data and try again.",
        "TypeError": "Invalid data type provided. Please check your input format.",
        "KeyError": "Required information is missing. Please check your input.",
        "FileNotFoundError": "Required file not found. Please contact support.",
        "PermissionError": "Permission denied. Please contact support.",
        "MemoryError": "Content is too large to process. Please reduce the size and try again.",
        "TimeoutError": "Operation timed out. Please try again.",
        "ConnectionError": "Connection failed. Please check your internet connection.",
    }

    return error_messages.get(
        error_type, "An unexpected error occurred. Please try again."
    )
