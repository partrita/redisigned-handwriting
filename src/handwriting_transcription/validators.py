"""
Input validation module for comprehensive validation and error handling.
"""

import logging
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
from .exceptions import ApplicationError


logger = logging.getLogger(__name__)


class ValidatorError(ApplicationError):
    """Custom exception for validation errors."""

    def __init__(
        self,
        message: str,
        field: str = None,
        code: str = None,
        user_message: str = None,
    ):
        super().__init__(message)
        self.message = message
        self.field = field
        self.code = code
        self.user_message = user_message


class ErrorCode(Enum):
    """Error codes for different validation failures."""

    REQUIRED_FIELD = "REQUIRED_FIELD"
    INVALID_TYPE = "INVALID_TYPE"
    INVALID_LENGTH = "INVALID_LENGTH"
    INVALID_RANGE = "INVALID_RANGE"
    INVALID_FORMAT = "INVALID_FORMAT"
    INVALID_FONT = "INVALID_FONT"
    CONTENT_TOO_LARGE = "CONTENT_TOO_LARGE"
    UNSAFE_CONTENT = "UNSAFE_CONTENT"


@dataclass
class ValidationResult:
    """Result of validation with success status and errors."""

    is_valid: bool
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    sanitized_data: Optional[Dict[str, Any]] = None


class InputValidator:
    """Comprehensive input validator for all API endpoints."""

    # Configuration constants
    MAX_TEXT_LENGTH = 10000
    MIN_TEXT_LENGTH = 1
    MIN_FONT_SIZE = 6
    MAX_FONT_SIZE = 72
    VALID_DOCUMENT_SIZES = ["A4", "Letter", "Legal"]
    VALID_GUIDELINE_TYPES = ["none", "ruled", "dotted"]
    VALID_COLORS = ["black", "gray"]

    # Allowed characters pattern (printable ASCII + common Unicode)
    SAFE_TEXT_PATTERN = re.compile(
        r"^[\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\"\'\/\\@#\$%\^&\*\+\=\|`~\n\r\t]*$"
    )

    # Font name validation pattern
    FONT_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9\s\-_\.]+$")

    @classmethod
    def validate_text_content(cls, text: Any) -> ValidationResult:
        """
        Validate text content input.

        Args:
            text: Text content to validate

        Returns:
            ValidationResult with validation status and sanitized text
        """
        errors = []
        warnings = []

        # Type validation
        if not isinstance(text, str):
            errors.append(
                {
                    "field": "text",
                    "message": "Text content must be a string",
                    "code": ErrorCode.INVALID_TYPE.value,
                    "received_type": type(text).__name__,
                }
            )
            return ValidationResult(False, errors, warnings)

        # Length validation
        if len(text) < cls.MIN_TEXT_LENGTH:
            errors.append(
                {
                    "field": "text",
                    "message": "Text content cannot be empty",
                    "code": ErrorCode.REQUIRED_FIELD.value,
                    "min_length": cls.MIN_TEXT_LENGTH,
                }
            )

        if len(text) > cls.MAX_TEXT_LENGTH:
            errors.append(
                {
                    "field": "text",
                    "message": f"Text content is too long (maximum {cls.MAX_TEXT_LENGTH} characters)",
                    "code": ErrorCode.CONTENT_TOO_LARGE.value,
                    "max_length": cls.MAX_TEXT_LENGTH,
                    "actual_length": len(text),
                }
            )

        # Content safety validation
        if not cls.SAFE_TEXT_PATTERN.match(text):
            warnings.append(
                {
                    "field": "text",
                    "message": "Text contains potentially unsafe characters that will be removed",
                    "code": ErrorCode.UNSAFE_CONTENT.value,
                }
            )

        # Sanitize text if no critical errors
        sanitized_text = text
        if not errors:
            sanitized_text = cls._sanitize_text(text)

            # Check if sanitization removed too much content
            if len(sanitized_text.strip()) == 0 and len(text.strip()) > 0:
                errors.append(
                    {
                        "field": "text",
                        "message": "Text content contains only invalid characters",
                        "code": ErrorCode.UNSAFE_CONTENT.value,
                    }
                )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_data={"text": sanitized_text} if not errors else None,
        )

    @classmethod
    def validate_font_options(cls, font_name: Any, font_size: Any) -> ValidationResult:
        """
        Validate font selection and size.

        Args:
            font_name: Font name to validate
            font_size: Font size to validate

        Returns:
            ValidationResult with validation status
        """
        errors = []
        warnings = []

        # Font name validation
        if not isinstance(font_name, str):
            errors.append(
                {
                    "field": "font_name",
                    "message": "Font name must be a string",
                    "code": ErrorCode.INVALID_TYPE.value,
                    "received_type": type(font_name).__name__,
                }
            )
        elif not font_name.strip():
            errors.append(
                {
                    "field": "font_name",
                    "message": "Font name cannot be empty",
                    "code": ErrorCode.REQUIRED_FIELD.value,
                }
            )
        elif not cls.FONT_NAME_PATTERN.match(font_name):
            errors.append(
                {
                    "field": "font_name",
                    "message": "Font name contains invalid characters",
                    "code": ErrorCode.INVALID_FORMAT.value,
                    "allowed_pattern": "Letters, numbers, spaces, hyphens, underscores, and dots only",
                }
            )

        # Font size validation
        if not isinstance(font_size, (int, float)):
            try:
                font_size = float(font_size)
            except (ValueError, TypeError):
                errors.append(
                    {
                        "field": "font_size",
                        "message": "Font size must be a number",
                        "code": ErrorCode.INVALID_TYPE.value,
                        "received_type": type(font_size).__name__,
                    }
                )

        if isinstance(font_size, (int, float)):
            if font_size < cls.MIN_FONT_SIZE:
                errors.append(
                    {
                        "field": "font_size",
                        "message": f"Font size must be at least {cls.MIN_FONT_SIZE}",
                        "code": ErrorCode.INVALID_RANGE.value,
                        "min_value": cls.MIN_FONT_SIZE,
                        "received_value": font_size,
                    }
                )
            elif font_size > cls.MAX_FONT_SIZE:
                errors.append(
                    {
                        "field": "font_size",
                        "message": f"Font size cannot exceed {cls.MAX_FONT_SIZE}",
                        "code": ErrorCode.INVALID_RANGE.value,
                        "max_value": cls.MAX_FONT_SIZE,
                        "received_value": font_size,
                    }
                )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_data={
                "font_name": font_name.strip()
                if isinstance(font_name, str)
                else font_name,
                "font_size": int(font_size)
                if isinstance(font_size, (int, float)) and not errors
                else font_size,
            }
            if not errors
            else None,
        )

    @classmethod
    def validate_document_options(
        cls, document_size: Any, guideline_type: Any
    ) -> ValidationResult:
        """
        Validate document formatting options.

        Args:
            document_size: Document size to validate
            guideline_type: Guideline type to validate

        Returns:
            ValidationResult with validation status
        """
        errors = []
        warnings = []

        # Document size validation
        if not isinstance(document_size, str):
            errors.append(
                {
                    "field": "document_size",
                    "message": "Document size must be a string",
                    "code": ErrorCode.INVALID_TYPE.value,
                    "received_type": type(document_size).__name__,
                }
            )
        elif document_size not in cls.VALID_DOCUMENT_SIZES:
            errors.append(
                {
                    "field": "document_size",
                    "message": "Invalid document size",
                    "code": ErrorCode.INVALID_FORMAT.value,
                    "valid_options": cls.VALID_DOCUMENT_SIZES,
                    "received_value": document_size,
                }
            )

        # Guideline type validation
        if not isinstance(guideline_type, str):
            errors.append(
                {
                    "field": "guideline_type",
                    "message": "Guideline type must be a string",
                    "code": ErrorCode.INVALID_TYPE.value,
                    "received_type": type(guideline_type).__name__,
                }
            )
        elif guideline_type not in cls.VALID_GUIDELINE_TYPES:
            errors.append(
                {
                    "field": "guideline_type",
                    "message": "Invalid guideline type",
                    "code": ErrorCode.INVALID_FORMAT.value,
                    "valid_options": cls.VALID_GUIDELINE_TYPES,
                    "received_value": guideline_type,
                }
            )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_data={
                "document_size": document_size,
                "guideline_type": guideline_type,
            }
            if not errors
            else None,
        )

    @classmethod
    def validate_formatting_options(cls, options: Dict[str, Any]) -> ValidationResult:
        """
        Validate text formatting options.

        Args:
            options: Dictionary of formatting options

        Returns:
            ValidationResult with validation status
        """
        errors = []
        warnings = []

        if not isinstance(options, dict):
            errors.append(
                {
                    "field": "options",
                    "message": "Formatting options must be an object",
                    "code": ErrorCode.INVALID_TYPE.value,
                    "received_type": type(options).__name__,
                }
            )
            return ValidationResult(False, errors, warnings)

        # Boolean option validation
        boolean_options = ["black_text", "gray_text", "blank_lines", "guidelines"]
        for option in boolean_options:
            if option in options and not isinstance(options[option], bool):
                try:
                    # Try to convert to boolean
                    options[option] = bool(options[option])
                    warnings.append(
                        {
                            "field": option,
                            "message": f"{option} was converted to boolean",
                            "code": ErrorCode.INVALID_TYPE.value,
                        }
                    )
                except (ValueError, TypeError):
                    errors.append(
                        {
                            "field": option,
                            "message": f"{option} must be a boolean value",
                            "code": ErrorCode.INVALID_TYPE.value,
                            "received_type": type(options[option]).__name__,
                        }
                    )

        # Validate color options logic
        if options.get("black_text") is False and options.get("gray_text") is False:
            warnings.append(
                {
                    "field": "text_colors",
                    "message": "No text color selected, defaulting to black text",
                    "code": ErrorCode.INVALID_FORMAT.value,
                }
            )
            options["black_text"] = True

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_data=options if not errors else None,
        )

    @classmethod
    def validate_pdf_generation_request(cls, data: Dict[str, Any]) -> ValidationResult:
        """
        Comprehensive validation for PDF generation requests.

        Args:
            data: Complete request data dictionary

        Returns:
            ValidationResult with validation status and sanitized data
        """
        all_errors = []
        all_warnings = []
        sanitized_data = {}

        # Validate text content
        text = data.get("text", "")
        text_result = cls.validate_text_content(text)
        all_errors.extend(text_result.errors)
        all_warnings.extend(text_result.warnings)
        if text_result.sanitized_data:
            sanitized_data.update(text_result.sanitized_data)

        # Validate options
        options = data.get("options", {})
        if not isinstance(options, dict):
            all_errors.append(
                {
                    "field": "options",
                    "message": "Options must be an object",
                    "code": ErrorCode.INVALID_TYPE.value,
                    "received_type": type(options).__name__,
                }
            )
            return ValidationResult(False, all_errors, all_warnings)

        # Validate font options
        font_result = cls.validate_font_options(
            options.get("font_name", ""), options.get("font_size", 12)
        )
        all_errors.extend(font_result.errors)
        all_warnings.extend(font_result.warnings)
        if font_result.sanitized_data:
            sanitized_data.setdefault("options", {}).update(font_result.sanitized_data)

        # Validate document options
        doc_result = cls.validate_document_options(
            options.get("document_size", "A4"), options.get("guideline_type", "none")
        )
        all_errors.extend(doc_result.errors)
        all_warnings.extend(doc_result.warnings)
        if doc_result.sanitized_data:
            sanitized_data.setdefault("options", {}).update(doc_result.sanitized_data)

        # Validate formatting options
        format_result = cls.validate_formatting_options(options)
        all_errors.extend(format_result.errors)
        all_warnings.extend(format_result.warnings)
        if format_result.sanitized_data:
            sanitized_data.setdefault("options", {}).update(
                format_result.sanitized_data
            )

        return ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings,
            sanitized_data=sanitized_data if len(all_errors) == 0 else None,
        )

    @classmethod
    def _sanitize_text(cls, text: str) -> str:
        """
        Sanitize text content by removing unsafe characters.

        Args:
            text: Raw text input

        Returns:
            Sanitized text
        """
        if not text:
            return ""

        # Remove HTML entities and potential XSS content
        from html import escape

        text = escape(text)

        # Remove potentially dangerous characters but keep common punctuation
        # Allow: letters, numbers, spaces, basic punctuation, line breaks
        sanitized = re.sub(
            r"[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\"\'\/\\@#\$%\^&\*\+\=\|`~\n\r\t]",
            "",
            text,
        )

        # Normalize line endings
        sanitized = re.sub(r"\r\n|\r", "\n", sanitized)

        # Limit consecutive line breaks
        sanitized = re.sub(r"\n{4,}", "\n\n\n", sanitized)

        # Trim whitespace
        sanitized = sanitized.strip()

        return sanitized


class FontValidator:
    """Specialized validator for font-related operations."""

    @classmethod
    def validate_font_availability(
        cls, font_name: str, font_manager
    ) -> ValidationResult:
        """
        Validate if a font is available and can be loaded.

        Args:
            font_name: Name of the font to validate
            font_manager: FontManager instance

        Returns:
            ValidationResult with availability status
        """
        errors = []
        warnings = []

        try:
            # Basic name validation first
            name_result = InputValidator.validate_font_options(font_name, 12)
            if not name_result.is_valid:
                return name_result

            # Check if font can be loaded
            loaded_font = font_manager.load_font(font_name)
            if not loaded_font:
                errors.append(
                    {
                        "field": "font_name",
                        "message": f'Font "{font_name}" is not available',
                        "code": ErrorCode.INVALID_FONT.value,
                        "font_name": font_name,
                    }
                )
            elif loaded_font != font_name:
                # Font was substituted with fallback
                warnings.append(
                    {
                        "field": "font_name",
                        "message": f'Font "{font_name}" was substituted with "{loaded_font}"',
                        "code": ErrorCode.INVALID_FONT.value,
                        "requested_font": font_name,
                        "actual_font": loaded_font,
                    }
                )

        except Exception as e:
            logger.error(f"Font validation error: {e}")
            errors.append(
                {
                    "field": "font_name",
                    "message": f"Font validation failed: {str(e)}",
                    "code": ErrorCode.INVALID_FONT.value,
                    "font_name": font_name,
                }
            )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_data={"font_name": loaded_font} if len(errors) == 0 else None,
        )


def create_error_response(
    validation_result: ValidationResult, status_code: int = 400
) -> Tuple[Dict[str, Any], int]:
    """
    Create a standardized error response from validation result.

    Args:
        validation_result: ValidationResult with errors
        status_code: HTTP status code

    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {
        "success": False,
        "errors": validation_result.errors,
        "warnings": validation_result.warnings,
    }

    # Add user-friendly error message
    if validation_result.errors:
        primary_error = validation_result.errors[0]
        response["message"] = primary_error["message"]
        response["error_code"] = primary_error.get("code")

    return response, status_code


def create_success_response(
    data: Any, warnings: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a standardized success response.

    Args:
        data: Response data
        warnings: Optional list of warnings

    Returns:
        Response dictionary
    """
    response = {"success": True, "data": data}

    if warnings:
        response["warnings"] = warnings

    return response
