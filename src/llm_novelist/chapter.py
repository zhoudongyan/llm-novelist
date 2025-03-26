"""
Chapter class definition for LLM Novelist.

This module provides the Chapter class used to represent novel chapters
throughout the LLM Novelist package.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class Chapter:
    """
    Represents a chapter in a novel.
    
    Attributes:
        number (int): Chapter number
        title (str): Chapter title
        overview (str): Chapter overview/summary
        content (Optional[str]): Chapter content text, may be empty
    """
    number: int
    title: str
    overview: str
    content: Optional[str] = None
    
    def __str__(self) -> str:
        """Returns string representation of the chapter, including number and title"""
        return f"Chapter {self.number}: {self.title}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converts the chapter to dictionary format"""
        return {
            "number": self.number,
            "title": self.title,
            "overview": self.overview,
            "content": self.content
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Chapter':
        """Creates a chapter object from a dictionary"""
        return cls(
            number=data.get("number", 0),
            title=data.get("title", ""),
            overview=data.get("overview", ""),
            content=data.get("content")
        )
        
    def is_empty(self) -> bool:
        """Checks if the chapter content is empty"""
        return self.content is None or self.content.strip() == ""
    
    def word_count(self) -> int:
        """Calculates the word count of the chapter content"""
        if self.is_empty():
            return 0
        return len(self.content.split())
    
    def summary(self, max_length: int = 100) -> str:
        """
        Gets a summary of the chapter content
        
        Args:
            max_length (int): Maximum length of the summary
            
        Returns:
            str: Content summary
        """
        if self.is_empty():
            return "Empty chapter"
            
        if len(self.content) <= max_length:
            return self.content
            
        return self.content[:max_length].rsplit(' ', 1)[0] + "..." 