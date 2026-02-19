"""
Font management module for handling font operations.
"""

import os
import platform
import logging
import time
import hashlib
from typing import List, Dict, Optional, Tuple
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
import base64
from .models import FontInfo

logger = logging.getLogger(__name__)


class FontManager:
    """Manages available fonts and font rendering."""

    def __init__(self):
        """Initialize the font manager."""
        self._font_cache = {}
        self._system_fonts = {}
        self._font_paths = {}
        self._metrics_cache = {}  # Cache for font metrics calculations
        self._preview_cache = {}  # Cache for font previews
        self._cache_timestamps = {}  # Track cache entry timestamps
        self._cache_ttl = 3600  # Cache TTL in seconds (1 hour)
        self._default_fonts = [
            "Helvetica",
            "Times-Roman",
            "Courier",
            "Symbol",
            "ZapfDingbats",
        ]
        self._initialize_system_fonts()

    def _initialize_system_fonts(self):
        """Initialize system font detection and caching."""
        try:
            # Get system-specific font directories
            font_dirs = self._get_system_font_directories()

            # Scan for available fonts
            for font_dir in font_dirs:
                if os.path.exists(font_dir):
                    self._scan_font_directory(font_dir)

            # Add default ReportLab fonts
            self._add_default_fonts()

        except Exception as e:
            logger.warning(f"Error initializing system fonts: {e}")
            # Fall back to default fonts only
            self._add_default_fonts()

    def _get_system_font_directories(self) -> List[str]:
        """Get system-specific font directories."""
        system = platform.system().lower()

        if system == "windows":
            return [
                os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts"),
                os.path.expanduser("~\\AppData\\Local\\Microsoft\\Windows\\Fonts"),
            ]
        elif system == "darwin":  # macOS
            return [
                "/System/Library/Fonts",
                "/Library/Fonts",
                os.path.expanduser("~/Library/Fonts"),
            ]
        else:  # Linux and other Unix-like systems
            return [
                "/usr/share/fonts",
                "/usr/local/share/fonts",
                os.path.expanduser("~/.fonts"),
                os.path.expanduser("~/.local/share/fonts"),
            ]

    def _scan_font_directory(self, font_dir: str):
        """Scan a directory for font files."""
        try:
            for root, dirs, files in os.walk(font_dir):
                for file in files:
                    # Only process TTF files as ReportLab doesn't support OTF well
                    if file.lower().endswith(".ttf"):
                        font_path = os.path.join(root, file)
                        self._register_font_file(font_path)
        except Exception as e:
            logger.warning(f"Error scanning font directory {font_dir}: {e}")

    def _register_font_file(self, font_path: str):
        """Register a font file and extract metadata."""
        try:
            # Extract font name from filename (basic approach)
            font_name = os.path.splitext(os.path.basename(font_path))[0]

            # Clean up font name
            font_name = font_name.replace("-", " ").replace("_", " ")

            # Store font information
            self._font_paths[font_name] = font_path
            self._system_fonts[font_name] = FontInfo(
                name=font_name,
                file_path=font_path,
                preview_text="The quick brown fox jumps over the lazy dog",
                supported_sizes=list(range(8, 73)),  # Common font sizes
                is_system_font=True,
            )

        except Exception as e:
            logger.warning(f"Error registering font {font_path}: {e}")

    def _add_default_fonts(self):
        """Add default ReportLab fonts."""
        default_font_info = {
            "Helvetica": "Clean, modern sans-serif font",
            "Times-Roman": "Classic serif font for formal documents",
            "Courier": "Monospace font for code and typewriter style",
            "Symbol": "Mathematical and special symbols",
            "ZapfDingbats": "Decorative symbols and dingbats",
        }

        for font_name, description in default_font_info.items():
            self._system_fonts[font_name] = FontInfo(
                name=font_name,
                file_path="",  # Built-in ReportLab font
                preview_text="The quick brown fox jumps over the lazy dog",
                supported_sizes=list(range(6, 73)),
                is_system_font=True,
            )

    def get_available_fonts(self) -> List[Dict[str, str]]:
        """Get list of available fonts with metadata."""
        fonts = []

        # Add system fonts
        for font_name, font_info in self._system_fonts.items():
            fonts.append(
                {
                    "name": font_name,
                    "display_name": font_name,
                    "type": "system" if font_info.is_system_font else "custom",
                    "preview_text": font_info.preview_text,
                    "file_path": font_info.file_path,
                }
            )

        # Sort fonts alphabetically
        fonts.sort(key=lambda x: x["display_name"])

        return fonts

    def load_font(self, font_name: str) -> Optional[str]:
        """Load a specific font and return the ReportLab font name."""
        try:
            # Check if font is already loaded
            if font_name in self._font_cache:
                return self._font_cache[font_name]

            # Check if it's a default ReportLab font
            if font_name in self._default_fonts:
                self._font_cache[font_name] = font_name
                return font_name

            # Check if it's a system font we've registered
            if font_name in self._system_fonts:
                font_info = self._system_fonts[font_name]

                # If it has a file path, register it with ReportLab
                if font_info.file_path and os.path.exists(font_info.file_path):
                    try:
                        # Create a safe ReportLab font name
                        rl_font_name = f"Custom_{font_name.replace(' ', '_')}"

                        # Register the font with ReportLab
                        pdfmetrics.registerFont(
                            TTFont(rl_font_name, font_info.file_path)
                        )

                        # Cache the mapping
                        self._font_cache[font_name] = rl_font_name
                        return rl_font_name

                    except Exception as e:
                        logger.warning(f"Failed to register font {font_name}: {e}")
                        # Fall back to default font
                        return self._get_fallback_font()
                else:
                    # It's a built-in font, use as-is
                    self._font_cache[font_name] = font_name
                    return font_name

            # Font not found, return fallback
            logger.warning(f"Font {font_name} not found, using fallback")
            return self._get_fallback_font()

        except Exception as e:
            logger.error(f"Error loading font {font_name}: {e}")
            return self._get_fallback_font()

    def _get_fallback_font(self) -> str:
        """Get a fallback font when requested font is not available."""
        return "Helvetica"  # Always available in ReportLab

    def validate_font(self, font_name: str) -> bool:
        """Validate if a font is available and can be loaded."""
        try:
            loaded_font = self.load_font(font_name)
            return loaded_font is not None
        except Exception:
            return False

    def calculate_text_dimensions(
        self, text: str, font_name: str, size: int
    ) -> Tuple[float, float]:
        """Calculate text dimensions for layout planning with caching."""
        try:
            # Create cache key
            cache_key = self._create_cache_key(text, font_name, size)

            # Check cache first
            cached_result = self._get_cached_result(self._metrics_cache, cache_key)
            if cached_result is not None:
                return cached_result

            # Load the font
            rl_font_name = self.load_font(font_name)
            if not rl_font_name:
                rl_font_name = self._get_fallback_font()

            # Create a temporary canvas to measure text
            buffer = BytesIO()
            temp_canvas = canvas.Canvas(buffer, pagesize=letter)
            temp_canvas.setFont(rl_font_name, size)

            # Calculate dimensions
            width = temp_canvas.stringWidth(text, rl_font_name, size)

            # Estimate height based on font size (rough approximation)
            height = size * 1.2  # Typical line height is 120% of font size

            result = (width, height)

            # Cache the result
            self._cache_result(self._metrics_cache, cache_key, result)

            return result

        except Exception as e:
            logger.error(f"Error calculating text dimensions: {e}")
            # Return rough estimates
            return (len(text) * size * 0.6, size * 1.2)

    def generate_font_preview(self, font_name: str, preview_text: str = None) -> str:
        """Generate a base64-encoded image preview of the font with caching."""
        try:
            if preview_text is None:
                preview_text = "The quick brown fox jumps over the lazy dog"

            # Create cache key
            cache_key = self._create_cache_key(font_name, preview_text[:40])

            # Check cache first
            cached_result = self._get_cached_result(self._preview_cache, cache_key)
            if cached_result is not None:
                return cached_result

            # Load the font
            rl_font_name = self.load_font(font_name)
            if not rl_font_name:
                rl_font_name = self._get_fallback_font()

            # Create a small PDF with the font preview
            buffer = BytesIO()
            preview_canvas = canvas.Canvas(buffer, pagesize=(300, 60))

            # Set font and draw text
            preview_canvas.setFont(rl_font_name, 14)
            preview_canvas.drawString(10, 30, preview_text[:40])  # Limit text length

            preview_canvas.save()

            # Convert to base64 for web display
            buffer.seek(0)
            pdf_data = buffer.getvalue()
            base64_data = base64.b64encode(pdf_data).decode("utf-8")

            result = f"data:application/pdf;base64,{base64_data}"

            # Cache the result
            self._cache_result(self._preview_cache, cache_key, result)

            return result

        except Exception as e:
            logger.error(f"Error generating font preview for {font_name}: {e}")
            return ""

    def generate_font_preview_image(self, font_name: str, preview_text: str = None, font_size: int = 28) -> str:
        """Generate a base64-encoded PNG image preview of the font.

        Uses Pillow to render text with the actual font file for web display.

        Args:
            font_name: Name of the font to preview
            preview_text: Text to render (default: sample text)
            font_size: Font size for rendering (default: 28)

        Returns:
            Base64-encoded PNG data URI string, or empty string on failure
        """
        try:
            from PIL import Image, ImageDraw, ImageFont

            if preview_text is None:
                preview_text = "The quick brown fox jumps over the lazy dog"

            preview_text = preview_text[:60]  # Limit text length

            # Create cache key including font size
            cache_key = self._create_cache_key(
                f"img_{font_name}_{font_size}", preview_text
            )

            # Check cache first
            cached_result = self._get_cached_result(self._preview_cache, cache_key)
            if cached_result is not None:
                return cached_result

            # Try to load the actual TTF font file for Pillow rendering
            pil_font = None
            font_path = self._font_paths.get(font_name)

            if font_path and os.path.exists(font_path):
                try:
                    pil_font = ImageFont.truetype(font_path, font_size)
                except Exception as e:
                    logger.warning(f"Could not load TTF font {font_name} for preview: {e}")

            # Fallback: try common system font paths
            if pil_font is None:
                fallback_paths = [
                    f"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    f"/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                    f"/usr/share/fonts/TTF/DejaVuSans.ttf",
                ]
                for path in fallback_paths:
                    if os.path.exists(path):
                        try:
                            pil_font = ImageFont.truetype(path, font_size)
                            break
                        except Exception:
                            continue

            # Last resort: use default PIL font
            if pil_font is None:
                pil_font = ImageFont.load_default()

            # Calculate text dimensions
            dummy_img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
            dummy_draw = ImageDraw.Draw(dummy_img)
            bbox = dummy_draw.textbbox((0, 0), preview_text, font=pil_font)
            text_width = bbox[2] - bbox[0] + 20  # Add padding
            text_height = bbox[3] - bbox[1] + 20

            # Create image with transparent background
            img_width = max(text_width, 400)
            img_height = max(text_height, 50)
            img = Image.new("RGBA", (img_width, img_height), (255, 255, 255, 0))
            draw = ImageDraw.Draw(img)

            # Draw text
            y_offset = (img_height - (bbox[3] - bbox[1])) // 2 - bbox[1]
            draw.text((10, y_offset), preview_text, font=pil_font, fill=(51, 51, 51, 255))

            # Convert to base64 PNG
            buffer = BytesIO()
            img.save(buffer, format="PNG", optimize=True)
            buffer.seek(0)
            base64_data = base64.b64encode(buffer.getvalue()).decode("utf-8")

            result = f"data:image/png;base64,{base64_data}"

            # Cache the result
            self._cache_result(self._preview_cache, cache_key, result)

            return result

        except ImportError:
            logger.error("Pillow is not installed. Cannot generate image preview.")
            return ""
        except Exception as e:
            logger.error(f"Error generating font preview image for {font_name}: {e}")
            return ""

    def get_font_info(self, font_name: str) -> Optional[FontInfo]:
        """Get detailed information about a specific font."""
        return self._system_fonts.get(font_name)

    def get_font_metrics(self, font_name: str, size: int) -> Dict[str, float]:
        """Get detailed font metrics for layout calculations with caching."""
        try:
            # Create cache key
            cache_key = self._create_cache_key(font_name, size, "metrics")

            # Check cache first
            cached_result = self._get_cached_result(self._metrics_cache, cache_key)
            if cached_result is not None:
                return cached_result

            rl_font_name = self.load_font(font_name)
            if not rl_font_name:
                rl_font_name = self._get_fallback_font()

            # Basic metrics calculation
            line_height = size * 1.2
            ascent = size * 0.8
            descent = size * 0.2

            result = {
                "line_height": line_height,
                "ascent": ascent,
                "descent": descent,
                "font_size": size,
                "em_width": size,  # Approximate em width
                "space_width": size * 0.25,  # Approximate space width
            }

            # Cache the result
            self._cache_result(self._metrics_cache, cache_key, result)

            return result

        except Exception as e:
            logger.error(f"Error getting font metrics: {e}")
            # Return default metrics
            return {
                "line_height": size * 1.2,
                "ascent": size * 0.8,
                "descent": size * 0.2,
                "font_size": size,
                "em_width": size,
                "space_width": size * 0.25,
            }

    def _create_cache_key(self, *args) -> str:
        """Create a cache key from arguments."""
        key_string = "|".join(str(arg) for arg in args)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_cached_result(self, cache_dict: dict, cache_key: str):
        """Get cached result if valid and not expired."""
        if cache_key in cache_dict:
            timestamp = self._cache_timestamps.get(cache_key, 0)
            if time.time() - timestamp < self._cache_ttl:
                return cache_dict[cache_key]
            else:
                # Remove expired entry
                del cache_dict[cache_key]
                if cache_key in self._cache_timestamps:
                    del self._cache_timestamps[cache_key]
        return None

    def _cache_result(self, cache_dict: dict, cache_key: str, result):
        """Cache a result with timestamp."""
        cache_dict[cache_key] = result
        self._cache_timestamps[cache_key] = time.time()

        # Limit cache size to prevent memory issues
        if len(cache_dict) > 1000:
            self._cleanup_old_cache_entries(cache_dict)

    def _cleanup_old_cache_entries(self, cache_dict: dict):
        """Remove oldest cache entries when cache gets too large."""
        # Sort by timestamp and remove oldest 20%
        sorted_keys = sorted(
            cache_dict.keys(), key=lambda k: self._cache_timestamps.get(k, 0)
        )

        keys_to_remove = sorted_keys[: len(sorted_keys) // 5]  # Remove oldest 20%

        for key in keys_to_remove:
            if key in cache_dict:
                del cache_dict[key]
            if key in self._cache_timestamps:
                del self._cache_timestamps[key]

    def clear_cache(self):
        """Clear all caches."""
        self._font_cache.clear()
        self._metrics_cache.clear()
        self._preview_cache.clear()
        self._cache_timestamps.clear()
        logger.info("Font manager caches cleared")
