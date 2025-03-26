"""
LLM Novelist - AI-Powered Novel Generation and Translation Tools

This package provides functionality to generate complete novels and translate text
using AI language models.
"""

from .llm_novelist import (
    generate_novel,
    generate_novel_content,
    create_cover_image,
    determine_style_and_chapters,
)
from .llm_translator import translate_text, batch_translate, translate_with_glossary

__version__ = "0.1.0"
__all__ = [
    "generate_novel",
    "generate_novel_content",
    "create_cover_image",
    "determine_style_and_chapters",
    "translate_text",
    "batch_translate",
    "translate_with_glossary"
] 