"""
PDF generation module using ReportLab.
"""

import logging
from io import BytesIO
from typing import Dict, List
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, LETTER, legal
from reportlab.lib.units import mm
from reportlab.lib.colors import black, Color
from .models import DocumentConfig, TextContent
from .font_manager import FontManager
from .text_processor import TextProcessor

logger = logging.getLogger(__name__)


class PDFGenerator:
    """Creates PDF documents with specified formatting and layout."""

    # Page size mappings
    PAGE_SIZES = {"A4": A4, "Letter": LETTER, "Legal": legal}

    # Color mappings
    COLORS = {
        "black": black,
        "gray": Color(0.5, 0.5, 0.5),  # 50% gray
        "light_gray": Color(0.7, 0.7, 0.7),  # Light gray for guidelines (more visible)
    }

    def __init__(self):
        """Initialize the PDF generator."""
        self.font_manager = FontManager()
        self.default_margins = {
            "top": 20 * mm,
            "bottom": 20 * mm,
            "left": 20 * mm,
            "right": 20 * mm,
        }

    def create_pdf(self, content: str, options: dict) -> bytes:
        """
        Generate PDF with custom fonts and sizes.

        Args:
            content: Text content to render
            options: Dictionary containing formatting options
                - font_name: str
                - font_size: int
                - document_size: str ('A4', 'Letter', etc.)
                - guidelines: bool
                - guideline_type: str ('ruled', 'dotted', 'none')
                - black_text: bool
                - gray_text: bool
                - blank_lines: bool
                - margins: dict (optional)

        Returns:
            PDF content as bytes
        """
        try:
            # Create document configuration
            doc_config = self._create_document_config(options)

            # Process text content
            text_content = self._process_text_content(content, options)

            # Create PDF buffer
            buffer = BytesIO()

            # Get page size
            page_size = self.PAGE_SIZES.get(doc_config.document_size, A4)

            # Create canvas
            pdf_canvas = canvas.Canvas(buffer, pagesize=page_size)

            # Calculate layout
            layout = self.calculate_layout(
                text_content.raw_text, page_size, doc_config.font_size
            )

            # Add guidelines if requested
            if doc_config.guidelines and doc_config.guideline_type != "none":
                self.add_guidelines(
                    pdf_canvas, page_size, doc_config.guideline_type, layout
                )

            # Render text with formatting
            self.render_text_with_formatting(
                pdf_canvas, text_content, doc_config, layout
            )

            # Save PDF
            pdf_canvas.save()

            # Return PDF bytes
            buffer.seek(0)
            return buffer.getvalue()

        except Exception as e:
            logger.error(f"Error creating PDF: {e}")
            raise Exception(f"PDF generation failed: {str(e)}")

    def add_guidelines(
        self, canvas, page_size: tuple, guideline_type: str, layout: dict = None
    ):
        """
        Add guidelines to the PDF (ruled lines, dotted lines).

        Args:
            canvas: ReportLab canvas object
            page_size: Tuple of (width, height) in points
            guideline_type: Type of guidelines ('ruled', 'dotted')
            layout: Layout information dictionary
        """
        try:
            width, height = page_size
            margins = (
                layout.get("margins", self.default_margins)
                if layout
                else self.default_margins
            )

            # Calculate content area
            left_margin = margins["left"]
            right_margin = width - margins["right"]
            top_margin = height - margins["top"]
            bottom_margin = margins["bottom"]

            # Set guideline color (lighter gray for better visibility)
            canvas.setStrokeColor(self.COLORS["light_gray"])

            if guideline_type == "ruled":
                self._add_ruled_lines(
                    canvas, left_margin, right_margin, top_margin, bottom_margin, layout
                )
            elif guideline_type == "dotted":
                self._add_dotted_lines(
                    canvas, left_margin, right_margin, top_margin, bottom_margin, layout
                )

        except Exception as e:
            logger.error(f"Error adding guidelines: {e}")
            # Continue without guidelines rather than failing

    def _add_ruled_lines(
        self, canvas, left: float, right: float, top: float, bottom: float, layout: dict
    ):
        """Add ruled (solid) lines to the PDF."""
        line_height = layout.get("line_height", 20)  # Default line height

        # Set line width for guidelines (thinner for better appearance)
        canvas.setLineWidth(0.3)

        # Start from the first line position (accounting for text baseline)
        y = top - (line_height * 0.8)  # Adjust for text baseline

        # Draw horizontal lines
        while y >= bottom:
            canvas.line(left, y, right, y)
            y -= line_height

    def _add_dotted_lines(
        self, canvas, left: float, right: float, top: float, bottom: float, layout: dict
    ):
        """Add dotted lines to the PDF."""
        line_height = layout.get("line_height", 20)  # Default line height

        # Set line width and dash pattern for dotted lines
        canvas.setLineWidth(0.2)
        canvas.setDash([1, 2])  # 1 point on, 2 points off for finer dots

        # Start from the first line position (accounting for text baseline)
        y = top - (line_height * 0.8)  # Adjust for text baseline

        # Draw horizontal dotted lines
        while y >= bottom:
            canvas.line(left, y, right, y)
            y -= line_height

        # Reset dash pattern
        canvas.setDash([])

    def render_text_with_formatting(
        self,
        canvas,
        text_content: TextContent,
        doc_config: DocumentConfig,
        layout: dict,
    ):
        """
        Render text with formatting options (colors, spacing).

        Args:
            canvas: ReportLab canvas object
            text_content: TextContent object with processed text
            doc_config: DocumentConfig object with formatting options
            layout: Layout information dictionary
        """
        try:
            # Load and set font
            font_name = self.font_manager.load_font(doc_config.font_name)
            if not font_name:
                font_name = "Helvetica"  # Fallback

            canvas.setFont(font_name, doc_config.font_size)

            # Get layout parameters
            margins = layout.get("margins", self.default_margins)
            line_height = layout.get("line_height", doc_config.font_size * 1.2)

            # Calculate starting position
            page_width, page_height = canvas._pagesize
            x_start = margins["left"]
            y_start = page_height - margins["top"] - doc_config.font_size

            # Render text based on color segments or plain text
            if text_content.color_segments:
                self._render_color_segments(
                    canvas,
                    text_content.color_segments,
                    x_start,
                    y_start,
                    line_height,
                    doc_config,
                )
            else:
                self._render_plain_text(
                    canvas,
                    text_content.processed_lines,
                    x_start,
                    y_start,
                    line_height,
                    doc_config,
                )

        except Exception as e:
            logger.error(f"Error rendering text: {e}")
            # Render basic text as fallback
            self._render_fallback_text(canvas, text_content.raw_text, doc_config)

    def _render_color_segments(
        self,
        canvas,
        color_segments: List[Dict[str, str]],
        x: float,
        y: float,
        line_height: float,
        doc_config: DocumentConfig,
    ):
        """Render text with color formatting."""
        current_y = y

        for segment in color_segments:
            text = segment.get("text", "")
            color = segment.get("color", "black")

            # Handle blank lines (empty text)
            if not text or not text.strip():
                current_y -= line_height
                continue

            # Set text color
            canvas.setFillColor(self.COLORS.get(color, black))

            # Calculate proper right margin from document config
            right_margin = (
                doc_config.margins.get("right", 20) * mm
                if isinstance(doc_config.margins.get("right", 20), (int, float))
                else doc_config.margins.get("right", 20 * mm)
            )
            max_width = canvas._pagesize[0] - x - right_margin

            # Handle line wrapping if text is too long
            lines = self._wrap_text(canvas, text, max_width)

            for line in lines:
                bottom_margin = (
                    doc_config.margins.get("bottom", 20) * mm
                    if isinstance(doc_config.margins.get("bottom", 20), (int, float))
                    else doc_config.margins.get("bottom", 20 * mm)
                )
                if current_y < bottom_margin:
                    # Start new page if needed
                    canvas.showPage()
                    canvas.setFont(
                        self.font_manager.load_font(doc_config.font_name)
                        or "Helvetica",
                        doc_config.font_size,
                    )
                    top_margin = (
                        doc_config.margins.get("top", 20) * mm
                        if isinstance(doc_config.margins.get("top", 20), (int, float))
                        else doc_config.margins.get("top", 20 * mm)
                    )
                    current_y = canvas._pagesize[1] - top_margin - doc_config.font_size

                canvas.drawString(x, current_y, line)
                current_y -= line_height

    def _render_plain_text(
        self,
        canvas,
        text_lines: List[str],
        x: float,
        y: float,
        line_height: float,
        doc_config: DocumentConfig,
    ):
        """Render plain text without color formatting."""
        current_y = y
        canvas.setFillColor(black)

        for line in text_lines:
            # Handle blank lines (empty text)
            if not line or not line.strip():
                current_y -= line_height
                continue

            bottom_margin = (
                doc_config.margins.get("bottom", 20) * mm
                if isinstance(doc_config.margins.get("bottom", 20), (int, float))
                else doc_config.margins.get("bottom", 20 * mm)
            )
            if current_y < bottom_margin:
                # Start new page if needed
                canvas.showPage()
                canvas.setFont(
                    self.font_manager.load_font(doc_config.font_name) or "Helvetica",
                    doc_config.font_size,
                )
                top_margin = (
                    doc_config.margins.get("top", 20) * mm
                    if isinstance(doc_config.margins.get("top", 20), (int, float))
                    else doc_config.margins.get("top", 20 * mm)
                )
                current_y = canvas._pagesize[1] - top_margin - doc_config.font_size

            # Calculate proper right margin from document config
            right_margin = (
                doc_config.margins.get("right", 20) * mm
                if isinstance(doc_config.margins.get("right", 20), (int, float))
                else doc_config.margins.get("right", 20 * mm)
            )
            max_width = canvas._pagesize[0] - x - right_margin

            # Handle line wrapping
            wrapped_lines = self._wrap_text(canvas, line, max_width)

            for wrapped_line in wrapped_lines:
                canvas.drawString(x, current_y, wrapped_line)
                current_y -= line_height

    def _render_fallback_text(self, canvas, text: str, doc_config: DocumentConfig):
        """Render basic fallback text when other methods fail."""
        try:
            canvas.setFont("Helvetica", 12)
            canvas.setFillColor(black)

            lines = text.split("\n")[:20]  # Limit to 20 lines for safety
            y = canvas._pagesize[1] - 50

            for line in lines:
                if y < 50:
                    break
                canvas.drawString(50, y, line[:80])  # Limit line length
                y -= 15

        except Exception as e:
            logger.error(f"Error in fallback text rendering: {e}")

    def _wrap_text(self, canvas, text: str, max_width: float) -> List[str]:
        """Wrap text to fit within specified width."""
        try:
            words = text.split()
            lines = []
            current_line = []

            for word in words:
                test_line = " ".join(current_line + [word])
                text_width = canvas.stringWidth(test_line)

                if text_width <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(" ".join(current_line))
                        current_line = [word]
                    else:
                        # Word is too long, add it anyway
                        lines.append(word)

            if current_line:
                lines.append(" ".join(current_line))

            return lines if lines else [text]

        except Exception:
            # Fallback: return original text
            return [text]

    def calculate_layout(self, text: str, page_size: tuple, font_size: int) -> dict:
        """
        Calculate layout parameters for the PDF.

        Args:
            text: Text content to layout
            page_size: Tuple of (width, height) in points
            font_size: Font size in points

        Returns:
            Dictionary with layout information
        """
        try:
            width, height = page_size

            # Calculate margins (convert mm to points)
            margins = {
                "top": 20 * mm,
                "bottom": 20 * mm,
                "left": 20 * mm,
                "right": 20 * mm,
            }

            # Calculate content area
            content_width = width - margins["left"] - margins["right"]
            content_height = height - margins["top"] - margins["bottom"]

            # Calculate line height (120% of font size is typical)
            line_height = font_size * 1.2

            # Estimate lines per page
            lines_per_page = int(content_height / line_height)

            # Count text lines
            text_lines = text.split("\n") if text else []
            total_lines = len(text_lines)

            # Estimate pages needed
            pages_needed = max(1, (total_lines + lines_per_page - 1) // lines_per_page)

            return {
                "margins": margins,
                "content_width": content_width,
                "content_height": content_height,
                "line_height": line_height,
                "lines_per_page": lines_per_page,
                "total_lines": total_lines,
                "pages_needed": pages_needed,
                "font_size": font_size,
            }

        except Exception as e:
            logger.error(f"Error calculating layout: {e}")
            # Return default layout
            return {
                "margins": self.default_margins,
                "content_width": 500,
                "content_height": 700,
                "line_height": font_size * 1.2,
                "lines_per_page": 30,
                "total_lines": len(text.split("\n")) if text else 0,
                "pages_needed": 1,
                "font_size": font_size,
            }

    def _create_document_config(self, options: dict) -> DocumentConfig:
        """Create DocumentConfig from options dictionary."""
        # Safely convert font_size to int
        try:
            font_size = int(options.get("font_size", 12))
        except (ValueError, TypeError):
            font_size = 12  # Default fallback

        # Ensure font_size is within reasonable bounds
        font_size = max(6, min(72, font_size))

        # Ensure font_name is not None
        font_name = options.get("font_name") or "Helvetica"

        return DocumentConfig(
            font_name=font_name,
            font_size=font_size,
            document_size=options.get("document_size", "A4"),
            guidelines=bool(options.get("guidelines", False)),
            guideline_type=options.get("guideline_type", "none"),
            black_text=bool(options.get("black_text", True)),
            gray_text=bool(options.get("gray_text", False)),
            blank_lines=bool(options.get("blank_lines", False)),
            margins=options.get(
                "margins", {"top": 20, "bottom": 20, "left": 20, "right": 20}
            ),
        )

    def _process_text_content(self, content: str, options: dict) -> TextContent:
        """Process text content using TextProcessor."""
        # Use TextProcessor to handle text processing
        processed_result = TextProcessor.process_text_with_options(content, options)

        return TextContent(
            raw_text=content,
            processed_lines=processed_result.get("text_lines", []),
            formatting_applied=processed_result.get("formatting_applied", False),
            color_segments=processed_result.get("color_segments", []),
        )
