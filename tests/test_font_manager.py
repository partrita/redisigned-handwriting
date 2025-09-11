"""
Unit tests for FontManager module.
"""

from unittest.mock import Mock, patch
import tempfile
import os
from handwriting_transcription.font_manager import FontManager
from handwriting_transcription.models import FontInfo


class TestFontManager:
    """Test cases for FontManager class."""

    def test_init(self):
        """Test FontManager initialization."""
        with patch.object(FontManager, "_initialize_system_fonts"):
            manager = FontManager()
            assert manager is not None
            assert hasattr(manager, "_font_cache")
            assert hasattr(manager, "_system_fonts")
            assert hasattr(manager, "_metrics_cache")
            assert hasattr(manager, "_preview_cache")

    def test_get_available_fonts_basic(self):
        """Test getting available fonts."""
        manager = FontManager()
        fonts = manager.get_available_fonts()

        assert isinstance(fonts, list)
        assert len(fonts) > 0

        # Check font structure
        for font in fonts:
            assert "name" in font
            assert "display_name" in font
            assert "type" in font
            assert font["type"] in ["system", "custom"]

    def test_get_available_fonts_empty(self):
        """Test getting fonts when none are available."""
        with patch.object(FontManager, "_initialize_system_fonts"):
            manager = FontManager()
            manager._system_fonts = {}

            fonts = manager.get_available_fonts()
            assert isinstance(fonts, list)
            assert len(fonts) == 0

    def test_load_font_default(self):
        """Test loading default ReportLab fonts."""
        manager = FontManager()

        # Test loading Helvetica (should always be available)
        result = manager.load_font("Helvetica")
        assert result == "Helvetica"

    def test_load_font_cached(self):
        """Test loading font from cache."""
        manager = FontManager()

        # Load font first time
        result1 = manager.load_font("Helvetica")

        # Load same font again (should use cache)
        result2 = manager.load_font("Helvetica")

        assert result1 == result2
        assert "Helvetica" in manager._font_cache

    def test_load_font_fallback(self):
        """Test font loading fallback mechanism."""
        manager = FontManager()

        # Try to load non-existent font
        result = manager.load_font("NonExistentFont")

        # Should return fallback font
        assert result == "Helvetica"

    def test_validate_font_valid(self):
        """Test font validation with valid font."""
        manager = FontManager()

        result = manager.validate_font("Helvetica")
        assert result is True

    def test_validate_font_invalid(self):
        """Test font validation with invalid font."""
        manager = FontManager()

        with patch.object(manager, "load_font", return_value=None):
            result = manager.validate_font("InvalidFont")
            assert result is False

    def test_calculate_text_dimensions_basic(self):
        """Test basic text dimension calculation."""
        manager = FontManager()

        with patch(
            "handwriting_transcription.font_manager.canvas.Canvas"
        ) as mock_canvas_class:
            mock_canvas = Mock()
            mock_canvas.stringWidth.return_value = 100.0
            mock_canvas_class.return_value = mock_canvas

            width, height = manager.calculate_text_dimensions(
                "Test text", "Helvetica", 12
            )

            assert isinstance(width, float)
            assert isinstance(height, float)
            assert width > 0
            assert height > 0

    def test_calculate_text_dimensions_cached(self):
        """Test text dimension calculation with caching."""
        manager = FontManager()

        with patch(
            "handwriting_transcription.font_manager.canvas.Canvas"
        ) as mock_canvas_class:
            mock_canvas = Mock()
            mock_canvas.stringWidth.return_value = 100.0
            mock_canvas_class.return_value = mock_canvas

            # First call
            result1 = manager.calculate_text_dimensions("Test", "Helvetica", 12)

            # Second call (should use cache)
            result2 = manager.calculate_text_dimensions("Test", "Helvetica", 12)

            assert result1 == result2
            # Canvas should only be created once
            assert mock_canvas_class.call_count == 1

    def test_calculate_text_dimensions_error_handling(self):
        """Test text dimension calculation error handling."""
        manager = FontManager()

        with patch(
            "handwriting_transcription.font_manager.canvas.Canvas",
            side_effect=Exception("Canvas error"),
        ):
            width, height = manager.calculate_text_dimensions("Test", "Helvetica", 12)

            # Should return rough estimates
            assert isinstance(width, float)
            assert isinstance(height, float)
            assert width > 0
            assert height > 0

    def test_generate_font_preview_basic(self):
        """Test basic font preview generation."""
        manager = FontManager()

        with patch(
            "handwriting_transcription.font_manager.canvas.Canvas"
        ) as mock_canvas_class:
            mock_canvas = Mock()
            mock_canvas_class.return_value = mock_canvas

            with patch(
                "handwriting_transcription.font_manager.base64.b64encode"
            ) as mock_b64:
                mock_b64.return_value = b"fake_base64_data"

                result = manager.generate_font_preview("Helvetica")

                assert isinstance(result, str)
                assert result.startswith("data:application/pdf;base64,")

    def test_generate_font_preview_cached(self):
        """Test font preview generation with caching."""
        manager = FontManager()

        with patch(
            "handwriting_transcription.font_manager.canvas.Canvas"
        ) as mock_canvas_class:
            mock_canvas = Mock()
            mock_canvas_class.return_value = mock_canvas

            with patch(
                "handwriting_transcription.font_manager.base64.b64encode"
            ) as mock_b64:
                mock_b64.return_value = b"fake_base64_data"

                # First call
                result1 = manager.generate_font_preview("Helvetica", "Test text")

                # Second call (should use cache)
                result2 = manager.generate_font_preview("Helvetica", "Test text")

                assert result1 == result2
                # Canvas should only be created once
                assert mock_canvas_class.call_count == 1

    def test_generate_font_preview_custom_text(self):
        """Test font preview with custom text."""
        manager = FontManager()

        with patch(
            "handwriting_transcription.font_manager.canvas.Canvas"
        ) as mock_canvas_class:
            mock_canvas = Mock()
            mock_canvas_class.return_value = mock_canvas

            with patch(
                "handwriting_transcription.font_manager.base64.b64encode"
            ) as mock_b64:
                mock_b64.return_value = b"fake_base64_data"

                result = manager.generate_font_preview(
                    "Helvetica", "Custom preview text"
                )

                assert isinstance(result, str)
                mock_canvas.drawString.assert_called()

    def test_generate_font_preview_error_handling(self):
        """Test font preview generation error handling."""
        manager = FontManager()

        with patch(
            "handwriting_transcription.font_manager.canvas.Canvas",
            side_effect=Exception("Canvas error"),
        ):
            result = manager.generate_font_preview("Helvetica")

            # Should return empty string on error
            assert result == ""

    def test_get_font_metrics_basic(self):
        """Test basic font metrics calculation."""
        manager = FontManager()

        metrics = manager.get_font_metrics("Helvetica", 12)

        assert isinstance(metrics, dict)
        assert "line_height" in metrics
        assert "ascent" in metrics
        assert "descent" in metrics
        assert "font_size" in metrics
        assert "em_width" in metrics
        assert "space_width" in metrics

        assert metrics["font_size"] == 12
        assert metrics["line_height"] == 12 * 1.2

    def test_get_font_metrics_cached(self):
        """Test font metrics calculation with caching."""
        manager = FontManager()

        # First call
        metrics1 = manager.get_font_metrics("Helvetica", 12)

        # Second call (should use cache)
        metrics2 = manager.get_font_metrics("Helvetica", 12)

        assert metrics1 == metrics2

    def test_get_font_metrics_different_sizes(self):
        """Test font metrics for different font sizes."""
        manager = FontManager()

        metrics_12 = manager.get_font_metrics("Helvetica", 12)
        metrics_24 = manager.get_font_metrics("Helvetica", 24)

        assert metrics_12["font_size"] == 12
        assert metrics_24["font_size"] == 24
        assert metrics_24["line_height"] > metrics_12["line_height"]

    def test_get_font_info_existing(self):
        """Test getting font info for existing font."""
        manager = FontManager()

        # Add a test font
        test_font = FontInfo(
            name="TestFont",
            file_path="/path/to/font.ttf",
            preview_text="Test preview",
            supported_sizes=[8, 10, 12, 14, 16],
            is_system_font=True,
        )
        manager._system_fonts["TestFont"] = test_font

        result = manager.get_font_info("TestFont")

        assert result == test_font
        assert result.name == "TestFont"

    def test_get_font_info_nonexistent(self):
        """Test getting font info for non-existent font."""
        manager = FontManager()

        result = manager.get_font_info("NonExistentFont")
        assert result is None

    def test_cache_key_creation(self):
        """Test cache key creation."""
        manager = FontManager()

        key1 = manager._create_cache_key("text", "font", 12)
        key2 = manager._create_cache_key("text", "font", 12)
        key3 = manager._create_cache_key("different", "font", 12)

        assert key1 == key2  # Same inputs should produce same key
        assert key1 != key3  # Different inputs should produce different keys
        assert isinstance(key1, str)
        assert len(key1) == 32  # MD5 hash length

    def test_cache_expiration(self):
        """Test cache expiration mechanism."""
        manager = FontManager()
        manager._cache_ttl = 0.1  # Very short TTL for testing

        # Add item to cache
        cache_key = "test_key"
        manager._cache_result(manager._metrics_cache, cache_key, {"test": "data"})

        # Should be in cache immediately
        result = manager._get_cached_result(manager._metrics_cache, cache_key)
        assert result is not None

        # Wait for expiration
        import time

        time.sleep(0.2)

        # Should be expired now
        result = manager._get_cached_result(manager._metrics_cache, cache_key)
        assert result is None

    def test_cache_size_limit(self):
        """Test cache size limiting."""
        manager = FontManager()

        # Fill cache beyond limit
        for i in range(1100):  # More than the 1000 limit
            cache_key = f"key_{i}"
            manager._cache_result(manager._metrics_cache, cache_key, f"data_{i}")

        # Cache should be cleaned up
        assert len(manager._metrics_cache) <= 1000

    def test_clear_cache(self):
        """Test cache clearing."""
        manager = FontManager()

        # Add items to caches
        manager._font_cache["test"] = "font"
        manager._metrics_cache["test"] = {"metrics": "data"}
        manager._preview_cache["test"] = "preview_data"
        manager._cache_timestamps["test"] = 12345

        # Clear caches
        manager.clear_cache()

        # All caches should be empty
        assert len(manager._font_cache) == 0
        assert len(manager._metrics_cache) == 0
        assert len(manager._preview_cache) == 0
        assert len(manager._cache_timestamps) == 0

    @patch("handwriting_transcription.font_manager.platform.system")
    def test_get_system_font_directories_windows(self, mock_system):
        """Test system font directory detection on Windows."""
        mock_system.return_value = "Windows"

        with patch.dict(os.environ, {"WINDIR": "C:\\Windows"}):
            manager = FontManager()
            dirs = manager._get_system_font_directories()

            assert any("Windows\\Fonts" in d for d in dirs)
            assert any("AppData" in d for d in dirs)

    @patch("handwriting_transcription.font_manager.platform.system")
    def test_get_system_font_directories_macos(self, mock_system):
        """Test system font directory detection on macOS."""
        mock_system.return_value = "Darwin"

        manager = FontManager()
        dirs = manager._get_system_font_directories()

        assert "/System/Library/Fonts" in dirs
        assert "/Library/Fonts" in dirs

    @patch("handwriting_transcription.font_manager.platform.system")
    def test_get_system_font_directories_linux(self, mock_system):
        """Test system font directory detection on Linux."""
        mock_system.return_value = "Linux"

        manager = FontManager()
        dirs = manager._get_system_font_directories()

        assert "/usr/share/fonts" in dirs
        assert "/usr/local/share/fonts" in dirs

    def test_register_font_file_valid(self):
        """Test registering a valid font file."""
        manager = FontManager()

        # Create a temporary file to simulate a font file
        with tempfile.NamedTemporaryFile(suffix=".ttf", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            initial_count = len(manager._font_paths)
            manager._register_font_file(temp_path)

            # Should have registered a new font (count increased)
            assert len(manager._font_paths) > initial_count

            # Check that the font was added to system fonts as well
            assert len(manager._system_fonts) > initial_count

        finally:
            # Cleanup
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

    def test_register_font_file_invalid(self):
        """Test registering an invalid font file."""
        manager = FontManager()

        # Should not raise an error
        manager._register_font_file("/nonexistent/path/font.ttf")

    def test_scan_font_directory_valid(self):
        """Test scanning a valid font directory."""
        manager = FontManager()

        # Create temporary directory with font file
        with tempfile.TemporaryDirectory() as temp_dir:
            font_file = os.path.join(temp_dir, "test_font.ttf")
            with open(font_file, "w") as f:
                f.write("fake font content")

            initial_count = len(manager._font_paths)
            manager._scan_font_directory(temp_dir)

            # Should have found the font file
            assert len(manager._font_paths) > initial_count

    def test_scan_font_directory_invalid(self):
        """Test scanning an invalid font directory."""
        manager = FontManager()

        # Should not raise an error
        manager._scan_font_directory("/nonexistent/directory")

    def test_fallback_font(self):
        """Test fallback font mechanism."""
        manager = FontManager()

        fallback = manager._get_fallback_font()
        assert fallback == "Helvetica"

        # Fallback should always be loadable
        result = manager.load_font(fallback)
        assert result is not None
