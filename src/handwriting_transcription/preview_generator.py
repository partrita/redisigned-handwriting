"""
Preview generation module for real-time HTML/CSS previews.
"""

import html
from .text_processor import TextProcessor


class PreviewGenerator:
    """Creates real-time HTML/CSS previews of the final output."""

    def __init__(self):
        """Initialize the preview generator."""
        self.document_sizes = {
            "A4": {"width": 210, "height": 297, "unit": "mm"},
            "Letter": {"width": 8.5, "height": 11, "unit": "in"},
            "Legal": {"width": 8.5, "height": 14, "unit": "in"},
            "A3": {"width": 297, "height": 420, "unit": "mm"},
            "A5": {"width": 148, "height": 210, "unit": "mm"},
        }

        # Standard margins in mm
        self.margins = {"top": 20, "bottom": 20, "left": 20, "right": 20}

    def generate_html_preview(self, content: str, options: dict) -> str:
        """Generate HTML representation of PDF layout."""
        if not content or not content.strip():
            return self._generate_empty_preview()

        # Process text content
        processed_content = self._process_content_for_preview(content, options)

        # Calculate dimensions
        dimensions = self.calculate_preview_dimensions(options)

        # Generate CSS styles
        css_styles = self.apply_css_styling(options, dimensions)

        # Create HTML structure
        html_content = self._create_preview_html(processed_content, options, dimensions)

        return f"""
        <div class="preview-document" style="{css_styles["document"]}">
            <div class="preview-content" style="{css_styles["content"]}">
                {html_content}
            </div>
        </div>
        """

    def apply_css_styling(self, options: dict, dimensions: dict = None) -> dict:
        """Apply CSS styling to match PDF appearance."""
        if dimensions is None:
            dimensions = self.calculate_preview_dimensions(options)

        font_name = options.get("font_name", "Helvetica")
        font_size = options.get("font_size", 16)

        # Map PDF fonts to web-safe fonts
        web_font = self._map_font_to_web_safe(font_name)

        # Document container styles
        document_styles = {
            "width": f"{dimensions['width']}px",
            "height": f"{dimensions['height']}px",
            "background-color": "white",
            "border": "1px solid #ddd",
            "box-shadow": "0 4px 8px rgba(0,0,0,0.1)",
            "margin": "0 auto",
            "position": "relative",
            "overflow": "hidden",
        }
        document_style = "; ".join(
            [f"{key}: {value}" for key, value in document_styles.items()]
        )

        # Content area styles - build as dictionary first
        content_styles = {
            "padding": f"{dimensions['margins']['top']}px {dimensions['margins']['right']}px {dimensions['margins']['bottom']}px {dimensions['margins']['left']}px",
            "font-family": web_font,
            "font-size": f"{font_size}px",
            "line-height": f"{self._calculate_line_height(font_size)}px",
            "height": "100%",
            "overflow": "hidden",
        }

        # Add guidelines if enabled
        if options.get("guidelines") and options.get("guideline_type") != "none":
            guideline_styles = self._generate_guideline_css(options, dimensions)
            content_styles.update(guideline_styles)

        # Convert to CSS string
        content_style = "; ".join(
            [f"{key}: {value}" for key, value in content_styles.items()]
        )

        return {"document": document_style, "content": content_style}

    def calculate_preview_dimensions(self, options: dict) -> dict:
        """Calculate preview dimensions."""
        document_size = options.get("document_size", "A4")
        size_info = self.document_sizes.get(document_size, self.document_sizes["A4"])

        # Convert to pixels for preview (assuming 96 DPI)
        if size_info["unit"] == "mm":
            # 1 mm = 3.78 pixels at 96 DPI
            width_px = int(size_info["width"] * 3.78)
            height_px = int(size_info["height"] * 3.78)
        else:  # inches
            # 1 inch = 96 pixels at 96 DPI
            width_px = int(size_info["width"] * 96)
            height_px = int(size_info["height"] * 96)

        # Scale down for preview (50% of actual size)
        preview_scale = 0.5
        width_px = int(width_px * preview_scale)
        height_px = int(height_px * preview_scale)

        # Calculate margin pixels
        margin_scale = 3.78 * preview_scale  # mm to pixels with preview scale
        margins_px = {
            "top": int(self.margins["top"] * margin_scale),
            "bottom": int(self.margins["bottom"] * margin_scale),
            "left": int(self.margins["left"] * margin_scale),
            "right": int(self.margins["right"] * margin_scale),
        }

        return {
            "width": width_px,
            "height": height_px,
            "margins": margins_px,
            "scale": preview_scale,
        }

    def _process_content_for_preview(self, content: str, options: dict) -> list:
        """Process content for preview display."""
        # Use TextProcessor to handle text processing consistently
        processed_result = TextProcessor.process_text_with_options(content, options)

        # Return the processed lines
        return processed_result.get("text_lines", [])

    def _create_preview_html(
        self, processed_content: list, options: dict, dimensions: dict
    ) -> str:
        """Create HTML structure for preview."""
        html_lines = []

        black_text = options.get("black_text", True)
        gray_text = options.get("gray_text", False)

        for line in processed_content:
            if not line:  # Empty line
                html_lines.append(
                    '<div class="preview-line preview-blank-line">&nbsp;</div>'
                )
                continue

            # Escape HTML characters
            escaped_line = html.escape(line)

            # Apply color styling
            line_classes = ["preview-line"]
            line_styles = []

            if black_text and gray_text:
                # Both colors - alternate or show both
                line_classes.append("preview-dual-color")
                line_styles.append("color: #333")
            elif black_text:
                line_classes.append("preview-black-text")
                line_styles.append("color: #000")
            elif gray_text:
                line_classes.append("preview-gray-text")
                line_styles.append("color: #666")
            else:
                # Default to black if no color is selected
                line_classes.append("preview-black-text")
                line_styles.append("color: #000")

            style_attr = f'style="{"; ".join(line_styles)}"' if line_styles else ""
            class_attr = f'class="{" ".join(line_classes)}"'

            html_lines.append(f"<div {class_attr} {style_attr}>{escaped_line}</div>")

        return "\n".join(html_lines)

    def _generate_empty_preview(self) -> str:
        """Generate preview for empty content."""
        return """
        <div class="preview-document" style="width: 400px; height: 566px; background-color: white; border: 1px solid #ddd; box-shadow: 0 4px 8px rgba(0,0,0,0.1); margin: 0 auto; display: flex; align-items: center; justify-content: center;">
            <div class="preview-placeholder" style="color: #999; font-style: italic; text-align: center;">
                Enter text above to see preview
            </div>
        </div>
        """

    def _map_font_to_web_safe(self, font_name: str) -> str:
        """Map PDF font names to web-safe font families."""
        font_mapping = {
            "Helvetica": '"Helvetica Neue", Helvetica, Arial, sans-serif',
            "Arial": 'Arial, "Helvetica Neue", Helvetica, sans-serif',
            "Times-Roman": '"Times New Roman", Times, serif',
            "Times New Roman": '"Times New Roman", Times, serif',
            "Courier": '"Courier New", Courier, monospace',
            "Courier New": '"Courier New", Courier, monospace',
            "Georgia": 'Georgia, "Times New Roman", Times, serif',
            "Verdana": "Verdana, Arial, sans-serif",
            "Comic Sans MS": '"Comic Sans MS", cursive',
            "Impact": 'Impact, "Arial Black", sans-serif',
            "Trebuchet MS": '"Trebuchet MS", Arial, sans-serif',
            "Palatino": 'Palatino, "Palatino Linotype", "Times New Roman", serif',
        }

        return font_mapping.get(
            font_name, '"Helvetica Neue", Helvetica, Arial, sans-serif'
        )

    def _calculate_line_height(self, font_size: int) -> int:
        """Calculate appropriate line height for font size."""
        # Standard line height is typically 1.2-1.5 times font size
        return int(font_size * 1.4)

    def _generate_guideline_css(self, options: dict, dimensions: dict) -> dict:
        """Generate CSS properties for guidelines (ruled or dotted lines)."""
        guideline_type = options.get("guideline_type", "none")

        if not options.get("guidelines") or guideline_type == "none":
            return {}

        line_height = self._calculate_line_height(options.get("font_size", 16))

        if guideline_type == "ruled":
            # Solid horizontal lines
            bg_image = f"repeating-linear-gradient(0deg, transparent 0px, transparent {line_height - 1}px, #bbb {line_height - 1}px, #bbb {line_height}px)"
            return {
                "background-image": bg_image,
                "background-size": f"100% {line_height}px",
            }
        elif guideline_type == "dotted":
            # Dotted horizontal lines - create actual dots
            dot_pattern = "repeating-linear-gradient(90deg, #aaa 0px, #aaa 2px, transparent 2px, transparent 8px)"
            line_pattern = f"repeating-linear-gradient(0deg, transparent 0px, transparent {line_height - 1}px, transparent {line_height - 1}px, transparent {line_height}px)"
            return {
                "background-image": f"{line_pattern}, {dot_pattern}",
                "background-size": f"100% {line_height}px, 8px 1px",
                "background-position": f"0 0, 0 {line_height - 1}px",
            }

        return {}
