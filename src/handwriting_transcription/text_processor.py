"""
Text processing module for handling text manipulation operations.
"""

import re
from typing import List, Dict
from html import escape


class TextProcessor:
    """Handles text manipulation and formatting operations."""

    @staticmethod
    def remove_spaces(text: str) -> str:
        """
        Remove all spaces from the input text.

        Args:
            text: Input text string

        Returns:
            Text with all spaces removed
        """
        if not text:
            return ""
        return text.replace(" ", "")

    @staticmethod
    def remove_line_breaks(text: str) -> str:
        """
        Remove line breaks and normalize text.
        Converts line breaks to spaces and normalizes whitespace.

        Args:
            text: Input text string

        Returns:
            Text with line breaks converted to spaces and normalized
        """
        if not text:
            return ""

        # Replace various line break types with spaces
        text = re.sub(r"\r\n|\r|\n", " ", text)

        # Normalize multiple spaces to single spaces
        text = re.sub(r"\s+", " ", text)

        # Strip leading and trailing whitespace
        return text.strip()

    @staticmethod
    def apply_color_formatting(
        text: str, black: bool, gray: bool
    ) -> List[Dict[str, str]]:
        """
        Apply text color formatting to create color segments.

        Args:
            text: Input text string
            black: Whether to include black text segments
            gray: Whether to include gray text segments

        Returns:
            List of color segments with text and color information
        """
        if not text:
            return []

        # If no colors are selected, default to black
        if not black and not gray:
            black = True

        segments = []
        lines = text.split("\n")

        for line in lines:
            # Handle blank lines (preserve them)
            if not line or not line.strip():
                # Add blank line segment if either color is requested
                if black or gray:
                    segments.append({"text": "", "color": "black" if black else "gray"})
                continue

            # Add black text segment if requested
            if black:
                segments.append({"text": line, "color": "black"})

            # Add gray text segment if requested
            if gray:
                segments.append({"text": line, "color": "gray"})

        return segments

    @staticmethod
    def add_blank_lines(text_lines: List[str]) -> List[str]:
        """
        Insert blank lines between content lines.

        Args:
            text_lines: List of text lines

        Returns:
            List with blank lines inserted between original lines
        """
        if not text_lines:
            return []

        result = []
        for i, line in enumerate(text_lines):
            result.append(line)
            # Add blank line after each line except the last one
            if i < len(text_lines) - 1:
                result.append("")

        return result

    @staticmethod
    def process_text_with_options(
        text: str, options: Dict[str, bool]
    ) -> Dict[str, any]:
        """
        Process text with multiple formatting options applied.

        Args:
            text: Input text string
            options: Dictionary of processing options
                - remove_spaces: bool
                - remove_line_breaks: bool
                - black_text: bool
                - gray_text: bool
                - blank_lines: bool

        Returns:
            Dictionary containing processed text and formatting information
        """
        # First sanitize the input
        processed_text = TextProcessor.sanitize_input(text)

        # Apply text processing options
        if options.get("remove_spaces", False):
            processed_text = TextProcessor.remove_spaces(processed_text)

        if options.get("remove_line_breaks", False):
            processed_text = TextProcessor.remove_line_breaks(processed_text)

        # Split into lines for further processing
        text_lines = processed_text.split("\n") if processed_text else []

        # Filter out empty lines first, then add blank lines if requested
        non_empty_lines = [line for line in text_lines if line.strip()]

        # Add blank lines if requested
        if options.get("blank_lines", False):
            text_lines = TextProcessor.add_blank_lines(non_empty_lines)
        else:
            text_lines = non_empty_lines

        # Apply color formatting
        color_segments = TextProcessor.apply_color_formatting(
            "\n".join(text_lines),
            options.get("black_text", False),
            options.get("gray_text", False),
        )

        return {
            "processed_text": "\n".join(text_lines),
            "text_lines": text_lines,
            "color_segments": color_segments,
            "formatting_applied": any(options.values()),
        }

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize text by removing extra whitespace and standardizing format.

        Args:
            text: Input text string

        Returns:
            Normalized text
        """
        if not text:
            return ""

        # Replace multiple spaces with single spaces
        text = re.sub(r" +", " ", text)

        # Replace multiple line breaks with single line breaks
        text = re.sub(r"\n+", "\n", text)

        # Strip leading and trailing whitespace
        return text.strip()

    @staticmethod
    def split_into_lines(text: str) -> List[str]:
        """
        Split text into lines, handling various line ending formats.

        Args:
            text: Input text string

        Returns:
            List of text lines
        """
        if not text:
            return []

        # Handle different line ending formats
        text = re.sub(r"\r\n", "\n", text)  # Windows
        text = re.sub(r"\r", "\n", text)  # Old Mac

        return text.split("\n")

    @staticmethod
    def validate_text_length(text: str, max_length: int) -> bool:
        """
        Validate that text length is within acceptable limits.

        Args:
            text: Input text string
            max_length: Maximum allowed length

        Returns:
            True if text is within limits, False otherwise
        """
        if not text:
            return True

        return len(text) <= max_length

    @staticmethod
    def count_characters(text: str) -> Dict[str, int]:
        """
        Count different types of characters in text.

        Args:
            text: Input text string

        Returns:
            Dictionary with character counts
        """
        if not text:
            return {
                "total": 0,
                "letters": 0,
                "digits": 0,
                "spaces": 0,
                "punctuation": 0,
                "other": 0,
            }

        counts = {
            "total": len(text),
            "letters": 0,
            "digits": 0,
            "spaces": 0,
            "punctuation": 0,
            "other": 0,
        }

        for char in text:
            if char.isalpha():
                counts["letters"] += 1
            elif char.isdigit():
                counts["digits"] += 1
            elif char.isspace():
                counts["spaces"] += 1
            elif char in ".,!?;:()-[]{}\"'/\\@#$%^&*+=|`~":
                counts["punctuation"] += 1
            else:
                counts["other"] += 1

        return counts

    @staticmethod
    def estimate_processing_time(text: str) -> float:
        """
        Estimate processing time for text based on length and complexity.

        Args:
            text: Input text string

        Returns:
            Estimated processing time in seconds
        """
        if not text:
            return 0.0

        # Base time per character (very rough estimate)
        base_time_per_char = 0.0001  # 0.1ms per character

        # Additional time for line breaks (more processing needed)
        line_breaks = text.count("\n")
        line_break_time = line_breaks * 0.001  # 1ms per line break

        # Additional time for special characters
        special_chars = len(re.findall(r"[^\w\s]", text))
        special_char_time = special_chars * 0.0002  # 0.2ms per special char

        total_time = (
            len(text) * base_time_per_char + line_break_time + special_char_time
        )

        # Minimum time of 0.001 seconds
        return max(0.001, total_time)

    @staticmethod
    def sanitize_input(text: str, max_length: int = 10000) -> str:
        """
        Validate and sanitize user input with configurable max length.

        Args:
            text: Raw input text
            max_length: Maximum allowed text length

        Returns:
            Sanitized and validated text
        """
        if not text:
            return ""

        # Limit text length to prevent abuse
        if len(text) > max_length:
            text = text[:max_length]

        # Escape HTML entities to prevent XSS
        text = escape(text)

        # Remove or replace potentially problematic characters
        # Keep only printable ASCII characters, common Unicode characters, and basic punctuation
        text = re.sub(
            r"[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\"\'\/\\@#\$%\^&\*\+\=\|`~\n\r\t]",
            "",
            text,
        )

        # Normalize line endings to \n
        text = re.sub(r"\r\n|\r", "\n", text)

        # Remove excessive consecutive line breaks (more than 3)
        text = re.sub(r"\n{4,}", "\n\n\n", text)

        # Strip leading and trailing whitespace
        text = text.strip()

        return text
