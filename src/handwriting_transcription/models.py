"""
Data models for the transcription game application.
"""

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class DocumentConfig:
    """Configuration for document generation."""

    font_name: str
    font_size: int
    document_size: str  # 'A4', 'Letter', etc.
    guidelines: bool
    guideline_type: str  # 'ruled', 'dotted', 'none'
    black_text: bool
    gray_text: bool
    blank_lines: bool
    margins: Dict[str, int]  # {'top': 20, 'bottom': 20, 'left': 20, 'right': 20}


@dataclass
class TextContent:
    """Text content and processing information."""

    raw_text: str
    processed_lines: List[str]
    formatting_applied: bool
    color_segments: List[Dict[str, str]]  # [{'text': str, 'color': str}]


@dataclass
class FontInfo:
    """Font information and metadata."""

    name: str
    file_path: str
    preview_text: str
    supported_sizes: List[int]
    is_system_font: bool
