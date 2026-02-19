"""
Main Flask application module for the transcription game.
"""

from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import os
import logging
import time
from .config import config
from .text_processor import TextProcessor
from .font_manager import FontManager
from .validators import (
    InputValidator,
    FontValidator,
    create_error_response,
    create_success_response,
    ValidatorError as ValidationError,
)
from .error_handlers import (
    handle_application_errors,
    FontError,
    PDFGenerationError,
    ContentTooLargeError,
    with_validation_error_handling,
    with_font_error_handling,
    with_pdf_error_handling,
)
from .rate_limiter import pdf_rate_limit, api_rate_limit

logger = logging.getLogger(__name__)


def create_app(config_name=None):
    """Create and configure the Flask application."""
    app = Flask(__name__, template_folder="../templates", static_folder="static")

    # Load configuration
    config_name = config_name or os.environ.get("FLASK_ENV", "development")
    app.config.from_object(config[config_name])

    # Additional Flask configuration
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
    app.config["MAX_TEXT_LENGTH"] = 10000  # Maximum text length for processing
    app.config["PDF_TIMEOUT"] = 30  # PDF generation timeout in seconds

    # Configure static file serving
    app.static_url_path = "/static"

    # Initialize FontManager
    font_manager = FontManager()

    # Register error handlers
    handle_application_errors(app)

    @app.route("/")
    def index():
        """Main interface route that serves the handwriting practice sheet generator."""
        return render_template("index.html")

    @app.route("/api/fonts")
    @with_font_error_handling
    def get_fonts():
        """API endpoint to get available fonts with enhanced error handling."""
        try:
            fonts = font_manager.get_available_fonts()

            if not fonts:
                logger.warning("No fonts available from font manager, using fallback")
                raise FontError(
                    "No fonts available",
                    user_message="Font system unavailable, using fallback fonts",
                )

            return jsonify(create_success_response(fonts))

        except FontError:
            # Use fallback fonts for font-specific errors
            fallback_fonts = [
                {"name": "Helvetica", "display_name": "Helvetica", "type": "system"},
                {
                    "name": "Times-Roman",
                    "display_name": "Times Roman",
                    "type": "system",
                },
                {"name": "Courier", "display_name": "Courier", "type": "system"},
            ]

            response = create_success_response(
                fallback_fonts,
                warnings=[
                    {
                        "message": "Using fallback fonts due to font system error",
                        "code": "FONT_FALLBACK",
                    }
                ],
            )
            return jsonify(response)

        except Exception as e:
            logger.error(f"Unexpected error loading fonts: {e}")
            raise FontError(f"Font loading failed: {str(e)}")

    @app.route("/api/process-text", methods=["POST"])
    @api_rate_limit
    @with_validation_error_handling
    def process_text():
        print(f"request.data: {request.data}")
        """API endpoint to process text with various formatting options and comprehensive validation."""
        # Get and validate request data
        data = request.get_json()
        if not data:
            raise ValidationError(
                "Request data is required", user_message="No data provided in request"
            )

        text = data.get("text", "")
        options = data.get("options", {})

        # Validate text content
        text_validation = InputValidator.validate_text_content(text)
        if not text_validation.is_valid:
            return create_error_response(text_validation)

        # Validate formatting options
        options_validation = InputValidator.validate_formatting_options(options)
        if not options_validation.is_valid:
            return create_error_response(options_validation)

        # Use sanitized data
        sanitized_text = text_validation.sanitized_data["text"]
        sanitized_options = options_validation.sanitized_data

        try:
            # Process the text
            result = TextProcessor.process_text_with_options(
                sanitized_text, sanitized_options
            )

            # Combine warnings from validation
            all_warnings = text_validation.warnings + options_validation.warnings

            return jsonify(create_success_response(result, all_warnings))

        except Exception as e:
            logger.error(f"Text processing failed: {e}")
            raise ValidationError(
                f"Text processing failed: {str(e)}",
                user_message="Failed to process text. Please check your input and try again.",
            )

    @app.route("/api/remove-spaces", methods=["POST"])
    @with_validation_error_handling
    def remove_spaces():
        """API endpoint to remove spaces from text with enhanced validation."""
        data = request.get_json()
        if not data or "text" not in data:
            raise ValidationError("Text is required", field="text")

        text = data["text"]

        # Validate text content
        validation_result = InputValidator.validate_text_content(text)
        if not validation_result.is_valid:
            return create_error_response(validation_result)

        # Use sanitized text
        sanitized_text = validation_result.sanitized_data["text"]

        try:
            processed_text = TextProcessor.remove_spaces(sanitized_text)

            response_data = {
                "original_text": text,
                "processed_text": processed_text,
                "characters_removed": len(sanitized_text) - len(processed_text),
            }

            return jsonify(
                create_success_response(response_data, validation_result.warnings)
            )

        except Exception as e:
            logger.error(f"Space removal failed: {e}")
            raise ValidationError(
                f"Space removal failed: {str(e)}",
                user_message="Failed to remove spaces. Please try again.",
            )

    @app.route("/api/remove-line-breaks", methods=["POST"])
    @with_validation_error_handling
    def remove_line_breaks():
        """API endpoint to remove line breaks from text with enhanced validation."""
        data = request.get_json()
        if not data or "text" not in data:
            raise ValidationError("Text is required", field="text")

        text = data["text"]

        # Validate text content
        validation_result = InputValidator.validate_text_content(text)
        if not validation_result.is_valid:
            return create_error_response(validation_result)

        # Use sanitized text
        sanitized_text = validation_result.sanitized_data["text"]

        try:
            original_lines = len(sanitized_text.split("\n"))
            processed_text = TextProcessor.remove_line_breaks(sanitized_text)

            response_data = {
                "original_text": text,
                "processed_text": processed_text,
                "original_lines": original_lines,
                "final_lines": 1 if processed_text.strip() else 0,
            }

            return jsonify(
                create_success_response(response_data, validation_result.warnings)
            )

        except Exception as e:
            logger.error(f"Line break removal failed: {e}")
            raise ValidationError(
                f"Line break removal failed: {str(e)}",
                user_message="Failed to remove line breaks. Please try again.",
            )

    @app.route("/api/fonts/validate", methods=["POST"])
    @with_font_error_handling
    def validate_font():
        """API endpoint to validate if a font is available with comprehensive validation."""
        data = request.get_json()
        if not data or "font_name" not in data:
            raise ValidationError("Font name is required", field="font_name")

        font_name = data["font_name"]

        # Validate font using specialized validator
        validation_result = FontValidator.validate_font_availability(
            font_name, font_manager
        )

        if not validation_result.is_valid:
            return create_error_response(validation_result)

        # Get the actual loaded font name (may be different due to fallbacks)
        actual_font = validation_result.sanitized_data.get("font_name", font_name)

        response_data = {
            "font_name": font_name,
            "is_valid": True,
            "actual_font": actual_font,
            "is_fallback": actual_font != font_name,
        }

        return jsonify(
            create_success_response(response_data, validation_result.warnings)
        )

    @app.route("/api/fonts/preview", methods=["POST"])
    @with_font_error_handling
    def generate_font_preview():
        """API endpoint to generate font preview with enhanced validation."""
        data = request.get_json()
        if not data or "font_name" not in data:
            raise ValidationError("Font name is required", field="font_name")

        font_name = data["font_name"]
        preview_text = data.get(
            "preview_text", "The quick brown fox jumps over the lazy dog"
        )

        # Validate font name
        font_validation = InputValidator.validate_font_options(font_name, 12)
        if not font_validation.is_valid:
            return create_error_response(font_validation)

        # Validate preview text if provided
        if preview_text:
            text_validation = InputValidator.validate_text_content(preview_text)
            if not text_validation.is_valid:
                # Use default text if provided text is invalid
                preview_text = "The quick brown fox jumps over the lazy dog"
                logger.warning(
                    f"Invalid preview text provided, using default: {text_validation.errors}"
                )

        # Validate font availability
        font_availability = FontValidator.validate_font_availability(
            font_name, font_manager
        )
        if not font_availability.is_valid:
            return create_error_response(font_availability)

        try:
            # Limit preview text length
            preview_text = (
                preview_text[:100] if len(preview_text) > 100 else preview_text
            )

            preview_data = font_manager.generate_font_preview(font_name, preview_text)

            if not preview_data:
                raise FontError(
                    f"Failed to generate preview for font {font_name}",
                    font_name=font_name,
                    user_message="Font preview generation failed. The font may not be available.",
                )

            response_data = {
                "font_name": font_name,
                "preview_data": preview_data,
                "preview_text": preview_text,
            }

            return jsonify(
                create_success_response(response_data, font_availability.warnings)
            )

        except Exception as e:
            logger.error(f"Font preview generation failed: {e}")
            raise FontError(f"Preview generation failed: {str(e)}", font_name=font_name)

    @app.route("/api/fonts/preview-image", methods=["GET"])
    def get_font_preview_image():
        """API endpoint to generate a PNG image preview of a font.

        Uses GET with query parameters for easy use in <img> tags.
        """
        font_name = request.args.get("font_name", "")
        preview_text = request.args.get(
            "preview_text", "The quick brown fox jumps over the lazy dog"
        )
        font_size = request.args.get("font_size", 28, type=int)

        if not font_name:
            return jsonify(create_error_response(
                type("ValidationResult", (), {
                    "is_valid": False,
                    "errors": [{
                        "message": "Font name is required",
                        "field": "font_name",
                        "code": "REQUIRED_FIELD"
                    }],
                    "warnings": [],
                    "sanitized_data": {},
                })()
            )), 400

        # Clamp font size
        font_size = max(12, min(72, font_size))

        try:
            preview_data = font_manager.generate_font_preview_image(
                font_name, preview_text, font_size
            )

            if not preview_data:
                return jsonify({
                    "success": False,
                    "error": f"Failed to generate preview for font {font_name}"
                }), 500

            return jsonify({
                "success": True,
                "data": {
                    "font_name": font_name,
                    "preview_image": preview_data,
                    "preview_text": preview_text,
                }
            })

        except Exception as e:
            logger.error(f"Font preview image generation failed: {e}")
            return jsonify({
                "success": False,
                "error": f"Preview generation failed: {str(e)}"
            }), 500

    @app.route("/api/fonts/upload", methods=["POST"])
    def upload_font():
        """Handle custom font upload."""
        if "font_file" not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400

        file = request.files["font_file"]

        if file.filename == "":
            return jsonify({"success": False, "error": "No file selected"}), 400

        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1].lower()

        if file_ext not in InputValidator.VALID_FONT_EXTENSIONS:
            return jsonify({
                "success": False, 
                "error": f"Invalid file type. Allowed: {', '.join(InputValidator.VALID_FONT_EXTENSIONS)}"
            }), 400
            
        if len(file.read()) > InputValidator.MAX_FONT_FILE_SIZE:
             return jsonify({"success": False, "error": "File too large (max 10MB)"}), 400
        file.seek(0) # Reset pointer

        try:
            # Save file
            upload_folder = os.path.join(app.root_path, "static", "fonts", "custom")
            os.makedirs(upload_folder, exist_ok=True)

            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)

            # Register font
            font_info = font_manager.register_custom_font(file_path)

            if not font_info:
                # Clean up if registration fails
                try:
                    os.remove(file_path)
                except Exception:
                    pass
                return jsonify({
                    "success": False, 
                    "error": "Failed to load font file. It may be corrupted or unsupported."
                }), 400

            return jsonify({
                "success": True,
                "data": {
                    "font": {
                        "name": font_info.name,
                        "display_name": font_info.name,
                        "is_custom": True
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"Font upload failed: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/fonts/metrics", methods=["POST"])
    @with_font_error_handling
    def get_font_metrics():
        """API endpoint to get font metrics for layout calculations with enhanced validation."""
        data = request.get_json()
        if not data or "font_name" not in data:
            raise ValidationError("Font name is required", field="font_name")

        font_name = data["font_name"]
        font_size = data.get("font_size", 12)

        # Validate font options
        validation_result = InputValidator.validate_font_options(font_name, font_size)
        if not validation_result.is_valid:
            return create_error_response(validation_result)

        # Use sanitized values
        sanitized_font_name = validation_result.sanitized_data["font_name"]
        sanitized_font_size = validation_result.sanitized_data["font_size"]

        # Validate font availability
        font_availability = FontValidator.validate_font_availability(
            sanitized_font_name, font_manager
        )
        if not font_availability.is_valid:
            return create_error_response(font_availability)

        try:
            metrics = font_manager.get_font_metrics(
                sanitized_font_name, sanitized_font_size
            )

            if not metrics:
                raise FontError(
                    f"Failed to calculate metrics for font {sanitized_font_name}",
                    font_name=sanitized_font_name,
                    user_message="Font metrics calculation failed. The font may not be available.",
                )

            response_data = {
                "font_name": sanitized_font_name,
                "font_size": sanitized_font_size,
                "metrics": metrics,
            }

            # Combine warnings from both validations
            all_warnings = validation_result.warnings + font_availability.warnings

            return jsonify(create_success_response(response_data, all_warnings))

        except Exception as e:
            logger.error(f"Font metrics calculation failed: {e}")
            raise FontError(
                f"Metrics calculation failed: {str(e)}", font_name=sanitized_font_name
            )

    @app.route("/api/generate-pdf", methods=["POST"])
    @pdf_rate_limit
    @with_pdf_error_handling
    def generate_pdf():
        """API endpoint to generate and download PDF with comprehensive validation and error handling."""
        import tempfile
        import time
        from datetime import datetime
        from flask import make_response
        from .pdf_generator import PDFGenerator

        temp_file = None
        try:
            # Get and validate request data
            data = request.get_json()
            if not data:
                raise ValidationError("Request data is required")

            # Comprehensive validation of the entire request
            validation_result = InputValidator.validate_pdf_generation_request(data)
            if not validation_result.is_valid:
                response, status_code = create_error_response(validation_result)
                return jsonify(response), status_code

            # Use sanitized data
            sanitized_text = validation_result.sanitized_data["text"]
            sanitized_options = validation_result.sanitized_data["options"]

            # Additional font availability check and fallback
            if "font_name" in sanitized_options:
                font_availability = FontValidator.validate_font_availability(
                    sanitized_options["font_name"], font_manager
                )
                if not font_availability.is_valid:
                    # Use fallback font instead of failing
                    sanitized_options["font_name"] = "Helvetica"
                    validation_result.warnings.extend(
                        [
                            {
                                "message": f"Font '{sanitized_options.get('font_name', 'unknown')}' not available, using Helvetica",
                                "code": "FONT_FALLBACK",
                            }
                        ]
                    )
                    logger.warning(
                        f"Font validation failed, using fallback: {font_availability.errors}"
                    )

            # Check content size limits
            if len(sanitized_text) > app.config.get("MAX_TEXT_LENGTH", 10000):
                raise ContentTooLargeError(
                    f"Text content is too long: {len(sanitized_text)} characters",
                    max_size=app.config.get("MAX_TEXT_LENGTH", 10000),
                )

            # Log PDF generation request
            logger.info(
                f"Starting PDF generation for {len(sanitized_text)} characters of text"
            )
            start_time = time.time()

            # Create PDF generator
            pdf_generator = PDFGenerator()

            # Generate PDF with enhanced error handling
            try:
                pdf_bytes = pdf_generator.create_pdf(sanitized_text, sanitized_options)
                generation_time = time.time() - start_time
                logger.info(
                    f"PDF generated successfully in {generation_time:.2f} seconds"
                )

            except MemoryError as me:
                logger.error(f"PDF generation memory error: {me}")
                raise ContentTooLargeError("Content is too large for PDF generation")

            except Exception as pdf_error:
                logger.error(f"PDF generation engine failed: {pdf_error}")
                raise PDFGenerationError(
                    f"PDF generation engine failed: {str(pdf_error)}",
                    user_message="PDF generation failed. Please check your content and formatting options.",
                )

            # Validate PDF output
            if not pdf_bytes or len(pdf_bytes) == 0:
                logger.error("PDF generation produced empty output")
                raise PDFGenerationError(
                    "PDF generation produced empty output",
                    user_message="PDF generation failed to produce output. Please try again.",
                )

            # Validate PDF size (basic sanity check)
            if len(pdf_bytes) < 100:  # PDF should be at least 100 bytes
                logger.error(
                    f"PDF generation produced suspiciously small output: {len(pdf_bytes)} bytes"
                )
                raise PDFGenerationError(
                    f"PDF generation produced invalid output: {len(pdf_bytes)} bytes",
                    user_message="PDF generation failed. Please try again.",
                )

            # Create temporary file for cleanup tracking
            temp_file = tempfile.NamedTemporaryFile(
                suffix=".pdf", prefix="handwriting_practice_", delete=False
            )
            temp_file.write(pdf_bytes)
            temp_file.close()

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"handwriting_practice_{timestamp}.pdf"

            # Create response with proper headers
            response = make_response(pdf_bytes)
            response.headers["Content-Type"] = "application/pdf"
            response.headers["Content-Disposition"] = (
                f'attachment; filename="{filename}"'
            )
            response.headers["Content-Length"] = str(len(pdf_bytes))
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

            # Add validation warnings as custom headers (for debugging)
            if validation_result.warnings and app.debug:
                response.headers["X-Validation-Warnings"] = str(
                    len(validation_result.warnings)
                )

            # Schedule cleanup of temporary file
            @response.call_on_close
            def cleanup_temp_file():
                try:
                    if temp_file and os.path.exists(temp_file.name):
                        os.unlink(temp_file.name)
                        logger.debug(f"Cleaned up temporary file: {temp_file.name}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup temporary file: {cleanup_error}")

            logger.info(
                f"PDF download response created successfully: {filename} ({len(pdf_bytes)} bytes)"
            )
            return response

        except (ValidationError, FontError, PDFGenerationError, ContentTooLargeError):
            # These are handled by the error handlers
            raise

        except Exception as e:
            logger.error(f"Unexpected PDF generation error: {e}", exc_info=True)

            # Cleanup temp file on error
            if temp_file:
                try:
                    if os.path.exists(temp_file.name):
                        os.unlink(temp_file.name)
                        logger.debug(
                            f"Cleaned up temporary file after error: {temp_file.name}"
                        )
                except Exception as cleanup_error:
                    logger.warning(
                        f"Failed to cleanup temporary file after error: {cleanup_error}"
                    )

            raise PDFGenerationError(
                f"Unexpected error during PDF generation: {str(e)}"
            )

    @app.route("/api/pdf-status")
    def pdf_generation_status():
        """API endpoint to check PDF generation service status with comprehensive health checks."""
        try:
            from .pdf_generator import PDFGenerator

            health_status = {
                "status": "healthy",
                "service": "transcription-game",
                "timestamp": time.time(),
                "checks": {},
            }

            # Test font manager
            try:
                fonts = font_manager.get_available_fonts()
                health_status["checks"]["font_manager"] = {
                    "status": "operational",
                    "fonts_available": len(fonts) if fonts else 0,
                }
            except Exception as e:
                logger.warning(f"Font manager health check failed: {e}")
                health_status["checks"]["font_manager"] = {
                    "status": "degraded",
                    "error": str(e),
                }

            # Test PDF generation capability
            try:
                test_generator = PDFGenerator()
                test_options = {
                    "font_name": "Helvetica",
                    "font_size": 12,
                    "document_size": "A4",
                    "guidelines": False,
                    "guideline_type": "none",
                    "black_text": True,
                    "gray_text": False,
                    "blank_lines": False,
                }

                # Try to create a minimal PDF to verify functionality
                test_pdf = test_generator.create_pdf("Health Check Test", test_options)

                if test_pdf and len(test_pdf) > 100:
                    health_status["checks"]["pdf_generator"] = {
                        "status": "operational",
                        "test_pdf_size": len(test_pdf),
                    }
                else:
                    health_status["checks"]["pdf_generator"] = {
                        "status": "degraded",
                        "error": "PDF generation produced invalid output",
                    }

            except Exception as e:
                logger.warning(f"PDF service test failed: {e}")
                health_status["checks"]["pdf_generator"] = {
                    "status": "degraded",
                    "error": str(e),
                }

            # Test validation system
            try:
                test_validation = InputValidator.validate_text_content(
                    "Test validation"
                )
                health_status["checks"]["validator"] = {
                    "status": "operational" if test_validation.is_valid else "degraded",
                    "test_passed": test_validation.is_valid,
                }
            except Exception as e:
                logger.warning(f"Validator health check failed: {e}")
                health_status["checks"]["validator"] = {
                    "status": "degraded",
                    "error": str(e),
                }

            # Determine overall status
            degraded_services = [
                check
                for check in health_status["checks"].values()
                if check["status"] == "degraded"
            ]

            if degraded_services:
                health_status["status"] = "degraded"
                health_status["degraded_services"] = len(degraded_services)

            # Add configuration info
            health_status["config"] = {
                "max_text_length": app.config.get("MAX_TEXT_LENGTH", 10000),
                "pdf_timeout": app.config.get("PDF_TIMEOUT", 30),
                "max_content_length": app.config.get(
                    "MAX_CONTENT_LENGTH", 16 * 1024 * 1024
                ),
            }

            status_code = 200 if health_status["status"] == "healthy" else 503
            return jsonify(health_status), status_code

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return jsonify(
                {
                    "status": "unhealthy",
                    "service": "transcription-game",
                    "error": str(e),
                    "timestamp": time.time(),
                }
            ), 503

    @app.route("/health")
    def health_check():
        """Health check endpoint for monitoring."""
        return jsonify({"status": "healthy", "service": "transcription-game"})

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return render_template("index.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        return jsonify({"error": "Internal server error"}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5002)
