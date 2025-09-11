"""
Unit tests for TextProcessor module.
"""

from handwriting_transcription.text_processor import TextProcessor


class TestTextProcessor:
    """Test cases for TextProcessor class."""

    def test_remove_spaces_basic(self):
        """Test basic space removal functionality."""
        text = "Hello world test"
        result = TextProcessor.remove_spaces(text)
        assert result == "Helloworldtest"

    def test_remove_spaces_multiple_spaces(self):
        """Test removal of multiple consecutive spaces."""
        text = "Hello    world   test"
        result = TextProcessor.remove_spaces(text)
        assert result == "Helloworldtest"

    def test_remove_spaces_with_newlines(self):
        """Test space removal preserves newlines."""
        text = "Hello world\nSecond line test"
        result = TextProcessor.remove_spaces(text)
        assert result == "Helloworld\nSecondlinetest"

    def test_remove_spaces_empty_string(self):
        """Test space removal with empty string."""
        result = TextProcessor.remove_spaces("")
        assert result == ""

    def test_remove_spaces_only_spaces(self):
        """Test space removal with string containing only spaces."""
        result = TextProcessor.remove_spaces("   ")
        assert result == ""

    def test_remove_line_breaks_basic(self):
        """Test basic line break removal."""
        text = "Line 1\nLine 2\nLine 3"
        result = TextProcessor.remove_line_breaks(text)
        assert result == "Line 1 Line 2 Line 3"

    def test_remove_line_breaks_multiple_breaks(self):
        """Test removal of multiple consecutive line breaks."""
        text = "Line 1\n\n\nLine 2"
        result = TextProcessor.remove_line_breaks(text)
        assert result == "Line 1 Line 2"

    def test_remove_line_breaks_carriage_returns(self):
        """Test removal of carriage returns."""
        text = "Line 1\r\nLine 2\rLine 3"
        result = TextProcessor.remove_line_breaks(text)
        assert result == "Line 1 Line 2 Line 3"

    def test_remove_line_breaks_empty_string(self):
        """Test line break removal with empty string."""
        result = TextProcessor.remove_line_breaks("")
        assert result == ""

    def test_sanitize_input_basic(self):
        """Test basic input sanitization."""
        text = "Normal text with some content"
        result = TextProcessor.sanitize_input(text)
        assert result == text

    def test_sanitize_input_html_tags(self):
        """Test sanitization removes HTML tags."""
        text = "<script>alert('test')</script>Hello world"
        result = TextProcessor.sanitize_input(text)
        assert "<script>" not in result
        assert "Hello world" in result

    def test_sanitize_input_special_characters(self):
        """Test sanitization handles special characters."""
        text = "Text with émojis 🎉 and àccénts"
        result = TextProcessor.sanitize_input(text)
        # Should preserve valid Unicode characters
        assert "émojis" in result or "emojis" in result  # May be normalized
        assert "àccénts" in result or "accents" in result

    def test_sanitize_input_length_limit(self):
        """Test sanitization respects length limits."""
        long_text = "a" * 20000  # Very long text
        result = TextProcessor.sanitize_input(long_text, max_length=1000)
        assert len(result) <= 1000

    def test_apply_color_formatting_black_only(self):
        """Test color formatting with black text only."""
        text = "Test text"
        result = TextProcessor.apply_color_formatting(text, black=True, gray=False)

        assert len(result) == 1
        assert result[0]["text"] == text
        assert result[0]["color"] == "black"

    def test_apply_color_formatting_gray_only(self):
        """Test color formatting with gray text only."""
        text = "Test text"
        result = TextProcessor.apply_color_formatting(text, black=False, gray=True)

        assert len(result) == 1
        assert result[0]["text"] == text
        assert result[0]["color"] == "gray"

    def test_apply_color_formatting_both_colors(self):
        """Test color formatting with both black and gray text."""
        text = "Test text"
        result = TextProcessor.apply_color_formatting(text, black=True, gray=True)

        assert len(result) == 2
        colors = [segment["color"] for segment in result]
        assert "black" in colors
        assert "gray" in colors

    def test_apply_color_formatting_no_colors(self):
        """Test color formatting with no colors selected."""
        text = "Test text"
        result = TextProcessor.apply_color_formatting(text, black=False, gray=False)

        # Should default to black
        assert len(result) == 1
        assert result[0]["color"] == "black"

    def test_add_blank_lines_basic(self):
        """Test adding blank lines between text lines."""
        lines = ["Line 1", "Line 2", "Line 3"]
        result = TextProcessor.add_blank_lines(lines)

        expected = ["Line 1", "", "Line 2", "", "Line 3"]
        assert result == expected

    def test_add_blank_lines_empty_list(self):
        """Test adding blank lines to empty list."""
        result = TextProcessor.add_blank_lines([])
        assert result == []

    def test_add_blank_lines_single_line(self):
        """Test adding blank lines to single line."""
        result = TextProcessor.add_blank_lines(["Single line"])
        assert result == ["Single line"]

    def test_process_text_with_options_comprehensive(self, sample_text):
        """Test comprehensive text processing with all options."""
        options = {
            "remove_spaces": True,
            "remove_line_breaks": True,
            "black_text": True,
            "gray_text": False,
            "blank_lines": True,
        }

        result = TextProcessor.process_text_with_options(sample_text, options)

        assert "text_lines" in result
        assert "color_segments" in result
        assert "formatting_applied" in result
        assert result["formatting_applied"] is True

    def test_process_text_with_options_no_processing(self, sample_text):
        """Test text processing with no options enabled."""
        options = {
            "remove_spaces": False,
            "remove_line_breaks": False,
            "black_text": True,
            "gray_text": False,
            "blank_lines": False,
        }

        result = TextProcessor.process_text_with_options(sample_text, options)

        assert "text_lines" in result
        assert len(result["text_lines"]) == 3  # Original line count

    def test_process_text_with_options_invalid_input(self):
        """Test text processing with invalid input."""
        result = TextProcessor.process_text_with_options(None, {})

        assert result["text_lines"] == []
        assert result["formatting_applied"] is False

    def test_normalize_text_basic(self):
        """Test text normalization."""
        text = "  Text with   extra   spaces  \n\n"
        result = TextProcessor.normalize_text(text)

        assert result.strip() == "Text with extra spaces"
        assert "   " not in result  # No multiple spaces

    def test_normalize_text_unicode(self):
        """Test text normalization with Unicode characters."""
        text = "Café naïve résumé"
        result = TextProcessor.normalize_text(text)

        # Should preserve Unicode characters
        assert "Café" in result or "Cafe" in result
        assert len(result) > 0

    def test_split_into_lines_basic(self):
        """Test splitting text into lines."""
        text = "Line 1\nLine 2\nLine 3"
        result = TextProcessor.split_into_lines(text)

        assert len(result) == 3
        assert result == ["Line 1", "Line 2", "Line 3"]

    def test_split_into_lines_mixed_separators(self):
        """Test splitting with mixed line separators."""
        text = "Line 1\nLine 2\r\nLine 3\rLine 4"
        result = TextProcessor.split_into_lines(text)

        assert len(result) == 4
        assert "Line 1" in result
        assert "Line 4" in result

    def test_split_into_lines_empty_lines(self):
        """Test splitting text with empty lines."""
        text = "Line 1\n\nLine 3"
        result = TextProcessor.split_into_lines(text)

        assert len(result) == 3
        assert result[1] == ""  # Empty line preserved

    def test_validate_text_length(self):
        """Test text length validation."""
        short_text = "Short text"
        long_text = "a" * 2000

        assert TextProcessor.validate_text_length(short_text, 1000) is True
        assert TextProcessor.validate_text_length(long_text, 1000) is False

    def test_count_characters(self):
        """Test character counting."""
        text = "Hello world! 123"
        result = TextProcessor.count_characters(text)

        assert result["total"] == len(text)
        assert result["letters"] > 0
        assert result["digits"] > 0
        assert result["spaces"] > 0
        assert result["punctuation"] > 0

    def test_estimate_processing_time(self):
        """Test processing time estimation."""
        short_text = "Short"
        long_text = "a" * 1000

        short_time = TextProcessor.estimate_processing_time(short_text)
        long_time = TextProcessor.estimate_processing_time(long_text)

        assert isinstance(short_time, float)
        assert isinstance(long_time, float)
        assert long_time > short_time
