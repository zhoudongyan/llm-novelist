"""
Tests for the LLM Novelist package
"""

import pytest
from llm_novelist import generate_novel

def test_generate_novel():
    """Test basic novel generation"""
    result = generate_novel(
        prompt="A story about a robot learning to paint",
        num_chapters=2,  # Use small number for testing
        style="science_fiction"
    )
    
    assert result["status"] == "success"
    assert result["title"]
    assert result["files"]
    assert result["novel"]

def test_generate_novel_without_style():
    """Test novel generation with automatic style determination"""
    result = generate_novel(
        prompt="A story about a robot learning to paint"
    )
    
    assert result["status"] == "success"
    assert result["title"]
    assert result["files"]
    assert result["novel"]

def test_generate_novel_without_chapters():
    """Test novel generation with automatic chapter determination"""
    result = generate_novel(
        prompt="A story about a robot learning to paint",
        style="science_fiction"
    )
    
    assert result["status"] == "success"
    assert result["title"]
    assert result["files"]
    assert result["novel"] 