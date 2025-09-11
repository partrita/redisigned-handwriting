"""
Unit tests for PDFGenerator module.
"""

import pytest
from unittest.mock import Mock, patch
from io import BytesIO
from handwriting_transcription.pdf_generator import PDFGenerator
from handwriting_transcription.models import DocumentConfig, TextContent


class TestPDFGenerator:
    """Test cases for PDFGenerator class."""

    def test_init(self):
        """Test PDFGenerator initialization."""
        generator = PDFGenerator()
        assert generator is not None
        assert hasattr(generator, "font_manager")
        assert hasattr(generator, "default_margins")

    @patch("handwriting_transcription.pdf_generator.canvas.Canvas")
    def test_create_pdf_basic(self, mock_canvas_class, sample_text, sample_options):
        """Test basic PDF creation."""
        # Setup mock canvas
        mock_canvas = Mock()
        mock_canvas._pagesize = (595.276, 841.89)  # A4 size
        mock_canvas.stringWidth.return_value = 100.0
        mock_canvas_class.return_value = mock_canvas

        # Mock the save method to return bytes
        buffer = BytesIO()
        buffer.write(b"%PDF-1.4 fake pdf content")
        buffer.seek(0)
        mock_canvas.save.side_effect = lambda: buffer.seek(0)

        generator = PDFGenerator()

        with patch.object(generator, "font_manager") as mock_font_manager:
            mock_font_manager.load_font.return_value = "Helvetica"

            # Mock the buffer to return PDF content
            with patch(
                "handwriting_transcription.pdf_generator.BytesIO"
            ) as mock_bytesio:
                mock_buffer = Mock()
                mock_buffer.getvalue.return_value = b"%PDF-1.4 fake pdf content"
                mock_bytesio.return_value = mock_buffer

                result = generator.create_pdf(sample_text, sample_options)

                assert isinstance(result, bytes)
                assert len(result) > 0
                assert result.startswith(b"%PDF")

    def test_create_document_config(self, sample_options):
        """Test document configuration creation."""
        generator = PDFGenerator()
        config = generator._create_document_config(sample_options)

        assert isinstance(config, DocumentConfig)
        assert config.font_name == sample_options["font_name"]
        assert config.font_size == sample_options["font_size"]
        assert config.document_size == sample_options["document_size"]
        assert config.guidelines == sample_options["guidelines"]

    def test_create_document_config_defaults(self):
        """Test document configuration with default values."""
        generator = PDFGenerator()
        config = generator._create_document_config({})

        assert config.font_name == "Helvetica"
        assert config.font_size == 12
        assert config.document_size == "A4"
        assert config.guidelines is False

    def test_process_text_content(self, sample_text, sample_options):
        """Test text content processing."""
        generator = PDFGenerator()

        with patch(
            "handwriting_transcription.pdf_generator.TextProcessor"
        ) as mock_processor:
            mock_processor.process_text_with_options.return_value = {
                "text_lines": ["Line 1", "Line 2"],
                "formatting_applied": True,
                "color_segments": [{"text": "Line 1", "color": "black"}],
            }

            content = generator._process_text_content(sample_text, sample_options)

            assert isinstance(content, TextContent)
            assert content.raw_text == sample_text
            assert len(content.processed_lines) == 2

    def test_calculate_layout_a4(self, sample_text):
        """Test layout calculation for A4 page size."""
        generator = PDFGenerator()
        page_size = (595.276, 841.89)  # A4 in points
        font_size = 12

        layout = generator.calculate_layout(sample_text, page_size, font_size)

        assert "margins" in layout
        assert "content_width" in layout
        assert "content_height" in layout
        assert "line_height" in layout
        assert "lines_per_page" in layout
        assert "total_lines" in layout
        assert "pages_needed" in layout

        assert layout["line_height"] == font_size * 1.2
        assert layout["total_lines"] == len(sample_text.split("\n"))

    def test_calculate_layout_letter(self, sample_text):
        """Test layout calculation for Letter page size."""
        generator = PDFGenerator()
        page_size = (612, 792)  # Letter in points
        font_size = 14

        layout = generator.calculate_layout(sample_text, page_size, font_size)

        assert layout["font_size"] == font_size
        assert layout["line_height"] == font_size * 1.2

    def test_calculate_layout_empty_text(self):
        """Test layout calculation with empty text."""
        generator = PDFGenerator()
        page_size = (595.276, 841.89)
        font_size = 12

        layout = generator.calculate_layout("", page_size, font_size)

        assert layout["total_lines"] == 0
        assert layout["pages_needed"] == 1  # At least one page

    def test_calculate_layout_error_handling(self):
        """Test layout calculation error handling."""
        generator = PDFGenerator()

        # Test with invalid inputs
        layout = generator.calculate_layout(None, (0, 0), 0)

        # Should return default layout
        assert "margins" in layout
        assert layout["pages_needed"] == 1

    @patch("handwriting_transcription.pdf_generator.canvas.Canvas")
    def test_add_guidelines_ruled(self, mock_canvas_class):
        """Test adding ruled guidelines."""
        mock_canvas = Mock()
        mock_canvas_class.return_value = mock_canvas

        generator = PDFGenerator()
        page_size = (595.276, 841.89)
        layout = {"margins": generator.default_margins, "line_height": 20}

        generator.add_guidelines(mock_canvas, page_size, "ruled", layout)

        # Verify canvas methods were called
        mock_canvas.setStrokeColor.assert_called()
        mock_canvas.setLineWidth.assert_called()
        mock_canvas.line.assert_called()

    @patch("handwriting_transcription.pdf_generator.canvas.Canvas")
    def test_add_guidelines_dotted(self, mock_canvas_class):
        """Test adding dotted guidelines."""
        mock_canvas = Mock()
        mock_canvas_class.return_value = mock_canvas

        generator = PDFGenerator()
        page_size = (595.276, 841.89)
        layout = {"margins": generator.default_margins, "line_height": 20}

        generator.add_guidelines(mock_canvas, page_size, "dotted", layout)

        # Verify canvas methods were called
        mock_canvas.setStrokeColor.assert_called()
        mock_canvas.setLineWidth.assert_called()
        mock_canvas.setDash.assert_called()
        mock_canvas.line.assert_called()

    def test_add_guidelines_none(self):
        """Test that no guidelines are added when type is 'none'."""
        generator = PDFGenerator()
        mock_canvas = Mock()
        page_size = (595.276, 841.89)

        # Should not raise an error
        generator.add_guidelines(mock_canvas, page_size, "none")

    def test_add_guidelines_error_handling(self):
        """Test guidelines error handling."""
        generator = PDFGenerator()
        mock_canvas = Mock()
        mock_canvas.setStrokeColor.side_effect = Exception("Canvas error")

        # Should not raise an error, just log and continue
        generator.add_guidelines(mock_canvas, (100, 100), "ruled")

    def test_wrap_text_basic(self, mock_canvas):
        """Test basic text wrapping."""
        generator = PDFGenerator()
        text = "This is a long line that should be wrapped"
        max_width = 200

        # Mock stringWidth to simulate text measurement
        mock_canvas.stringWidth.side_effect = lambda t, *args: len(t) * 10

        result = generator._wrap_text(mock_canvas, text, max_width)

        assert isinstance(result, list)
        assert len(result) >= 1
        assert all(isinstance(line, str) for line in result)

    def test_wrap_text_short_text(self, mock_canvas):
        """Test wrapping short text that fits on one line."""
        generator = PDFGenerator()
        text = "Short text"
        max_width = 1000

        mock_canvas.stringWidth.return_value = 50

        result = generator._wrap_text(mock_canvas, text, max_width)

        assert len(result) == 1
        assert result[0] == text

    def test_wrap_text_single_long_word(self, mock_canvas):
        """Test wrapping single word that's too long."""
        generator = PDFGenerator()
        text = "Supercalifragilisticexpialidocious"
        max_width = 50

        mock_canvas.stringWidth.return_value = 300

        result = generator._wrap_text(mock_canvas, text, max_width)

        # Should include the word even if it's too long
        assert len(result) >= 1
        assert text in result

    def test_wrap_text_error_handling(self, mock_canvas):
        """Test text wrapping error handling."""
        generator = PDFGenerator()
        mock_canvas.stringWidth.side_effect = Exception("Canvas error")

        text = "Test text"
        result = generator._wrap_text(mock_canvas, text, 100)

        # Should return original text as fallback
        assert result == [text]

    def test_render_fallback_text(self, mock_canvas):
        """Test fallback text rendering."""
        generator = PDFGenerator()
        mock_canvas._pagesize = (595.276, 841.89)

        config = DocumentConfig(
            font_name="Helvetica",
            font_size=12,
            document_size="A4",
            guidelines=False,
            guideline_type="none",
            black_text=True,
            gray_text=False,
            blank_lines=False,
            margins={"top": 20, "bottom": 20, "left": 20, "right": 20},
        )

        text = "Test fallback text"

        # Should not raise an error
        generator._render_fallback_text(mock_canvas, text, config)

        # Verify basic canvas operations were called
        mock_canvas.setFont.assert_called()
        mock_canvas.setFillColor.assert_called()
        mock_canvas.drawString.assert_called()

    def test_render_fallback_text_error_handling(self, mock_canvas):
        """Test fallback text rendering with errors."""
        generator = PDFGenerator()
        mock_canvas.setFont.side_effect = Exception("Font error")

        config = DocumentConfig(
            font_name="Helvetica",
            font_size=12,
            document_size="A4",
            guidelines=False,
            guideline_type="none",
            black_text=True,
            gray_text=False,
            blank_lines=False,
            margins={"top": 20, "bottom": 20, "left": 20, "right": 20},
        )

        # Should not raise an error
        generator._render_fallback_text(mock_canvas, "Test", config)

    def test_page_sizes_mapping(self):
        """Test that page size mappings are correct."""
        generator = PDFGenerator()

        assert "A4" in generator.PAGE_SIZES
        assert "Letter" in generator.PAGE_SIZES
        assert "Legal" in generator.PAGE_SIZES

        # Verify sizes are tuples
        for size in generator.PAGE_SIZES.values():
            assert isinstance(size, tuple)
            assert len(size) == 2
            assert all(isinstance(dim, (int, float)) for dim in size)

    def test_colors_mapping(self):
        """Test that color mappings are correct."""
        generator = PDFGenerator()

        assert "black" in generator.COLORS
        assert "gray" in generator.COLORS
        assert "light_gray" in generator.COLORS

        # Verify colors are color objects
        for color in generator.COLORS.values():
            assert hasattr(color, "red") or hasattr(color, "rgb")

    @patch("handwriting_transcription.pdf_generator.canvas.Canvas")
    def test_create_pdf_error_handling(
        self, mock_canvas_class, sample_text, sample_options
    ):
        """Test PDF creation error handling."""
        mock_canvas_class.side_effect = Exception("Canvas creation failed")

        generator = PDFGenerator()

        with pytest.raises(Exception) as exc_info:
            generator.create_pdf(sample_text, sample_options)

        assert "PDF generation failed" in str(exc_info.value)

    def test_create_pdf_with_invalid_options(self, sample_text):
        """Test PDF creation with invalid options."""
        generator = PDFGenerator()

        invalid_options = {
            "font_name": None,
            "font_size": "invalid",
            "document_size": "InvalidSize",
        }

        # Should handle invalid options gracefully
        with patch(
            "handwriting_transcription.pdf_generator.canvas.Canvas"
        ) as mock_canvas_class:
            mock_canvas = Mock()
            mock_canvas._pagesize = (595.276, 841.89)
            mock_canvas_class.return_value = mock_canvas

            with patch(
                "handwriting_transcription.pdf_generator.BytesIO"
            ) as mock_bytesio:
                mock_buffer = Mock()
                mock_buffer.getvalue.return_value = b"%PDF-1.4 fake pdf"
                mock_bytesio.return_value = mock_buffer

                result = generator.create_pdf(sample_text, invalid_options)
                assert isinstance(result, bytes)

    def test_margins_handling(self):
        """Test proper handling of margins in different units."""
        generator = PDFGenerator()

        # Test with default margins
        layout = generator.calculate_layout("test", (595, 842), 12)
        margins = layout["margins"]

        assert "top" in margins
        assert "bottom" in margins
        assert "left" in margins
        assert "right" in margins

        # All margins should be positive numbers
        for margin in margins.values():
            assert isinstance(margin, (int, float))
            assert margin > 0
