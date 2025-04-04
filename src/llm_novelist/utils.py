"""
Utility functions for LLM Novelist.

This module provides utility functions for the LLM Novelist package,
including XML parsing, EPUB generation, and file handling utilities.
"""

import os
import re
import uuid
from datetime import datetime
from ebooklib import epub
from loguru import logger

from .chapter import Chapter


def extract_xml(text: str, tag: str) -> str:
    """
    Extracts the content of the specified XML tag from the given text. Used for parsing structured responses.

    Args:
        text (str): The text containing the XML.
        tag (str): The XML tag to extract content from.

    Returns:
        str: The content of the specified XML tag, or an empty string if the tag is not found.
    """
    match = re.search(f'<{tag}>(.*?)</{tag}>', text, re.DOTALL)
    return match.group(1) if match else ""


def clean_xml_response(response):
    """
    Clean the XML response by removing thinking tags and other markup.
    
    Args:
        response (str): Raw response from LLM
        
    Returns:
        str: Cleaned response
    """
    # Remove content inside <think> or <thoughts> tags
    for tag in ["think", "thoughts"]:
        if f"<{tag}>" in response and f"</{tag}>" in response:
            after_tag = response.split(f"</{tag}>", 1)
            if len(after_tag) > 1:
                response = after_tag[1].strip()
    
    # Remove markdown code blocks if present
    if "```" in response:
        lines = response.split("\n")
        clean_lines = []
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if not in_code_block:
                clean_lines.append(line)
                
        response = "\n".join(clean_lines)
    
    return response


def generate_unique_dir(base_dir="output"):
    """
    Generate a unique directory name based on timestamp and UUID.

    Args:
        base_dir (str): Base directory for output

    Returns:
        str: Path to the unique directory
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    dir_name = f"{timestamp}_{unique_id}"
    dir_path = os.path.join(base_dir, dir_name)
    os.makedirs(dir_path, exist_ok=True)
    return dir_path


def ensure_output_dir(output_dir):
    """
    Ensure output directory exists.
    
    Args:
        output_dir (str): Path to the directory
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")


def create_safe_filename(title, max_length=50):
    """
    Create a safe filename from a title.
    
    Args:
        title (str): Original title
        max_length (int): Maximum length for the filename
        
    Returns:
        str: Safe filename
    """
    # Truncate title if too long
    safe_title = title[:max_length] if len(title) > max_length else title
    # Remove invalid filename characters
    safe_title = "".join(c for c in safe_title if c.isalnum() or c in "： -_.,()").strip()
    return safe_title


def create_epub(title, story_outline, chapters: list[Chapter], author, cover_image_path, output_dir, safe_title):
    """
    Create an EPUB file with the novel content.

    Args:
        title (str): Novel title
        author (str): Author name
        chapters (list[Chapter]): List of chapter objects
        cover_image_path (str): Path to cover image (can be None)
        output_dir (str): Output directory path
        safe_title (str): Safe title for filenames
    Returns:
        str: Path to the created EPUB file
    """
    try:
        book = epub.EpubBook()

        # Set metadata
        book.set_identifier(f"id_{uuid.uuid4()}")
        book.set_title(title)
        book.set_language("en")
        book.add_author(author)
        book.add_metadata(
            "DC", "description", f'Generated by Novelist - {datetime.now().strftime("%Y-%m-%d")}'
        )
        book.add_metadata("DC", "rights", "All rights reserved")
        book.add_metadata("DC", "date", datetime.now().strftime("%Y-%m-%d"))

        # Add cover image if available
        if cover_image_path and os.path.exists(cover_image_path):
            try:
                with open(cover_image_path, "rb") as cover_file:
                    cover_image = cover_file.read()
                book.set_cover("cover.png", cover_image)
                logger.info(f"Added cover image from: {cover_image_path}")
            except Exception as e:
                logger.warning(f"Failed to add cover image: {str(e)}")
        else:
            logger.info("No cover image provided or file not found")

        # Create chapters and add them to the book
        epub_chapters = []
        for i, chapter in enumerate(chapters):
            try:
                chapter_title = chapter.title
                chapter_content = chapter.content or ""
                    
                # Truncate chapter title if too long
                if len(chapter_title) > 100:
                    chapter_title = chapter_title[:97] + "..."
                
                # Create safe file name for the chapter
                chapter_file_name = f"chapter_{i+1}.xhtml"
                epub_chapter = epub.EpubHtml(title=chapter_title, file_name=chapter_file_name, lang="en")

                # Add paragraph breaks with proper spacing
                paragraphs = [p.strip() for p in chapter_content.split("\n") if p.strip()]
                formatted_content = "".join(
                    f'<p class="paragraph">{paragraph}</p>\n' for paragraph in paragraphs
                )

                epub_chapter.content = f"""
                    <div class="chapter">
                        <h1 class="chapter-title">Chapter {chapter.number}</h1>
                        <h2 class="chapter-subtitle">{chapter_title}</h2>
                        <div class="chapter-content">
                            {formatted_content}
                        </div>
                    </div>
                """
                book.add_item(epub_chapter)
                epub_chapters.append(epub_chapter)
            except Exception as e:
                logger.warning(f"Error adding chapter {i+1} to EPUB: {str(e)}")
                # Create a simple fallback chapter if needed
                chapter_file_name = f"chapter_{i+1}.xhtml"
                epub_chapter = epub.EpubHtml(title=f"Chapter {i+1}", file_name=chapter_file_name, lang="en")
                epub_chapter.content = f"""
                    <div class="chapter">
                        <h1 class="chapter-title">Chapter {i+1}</h1>
                        <div class="chapter-content">
                            <p>Chapter content unavailable.</p>
                        </div>
                    </div>
                """
                book.add_item(epub_chapter)
                epub_chapters.append(epub_chapter)

        # Define Table of Contents
        book.toc = epub_chapters

        # Add default NCX and Nav files
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # Define CSS style
        style = """
        @namespace epub "http://www.idpf.org/2007/ops";
        
        /* Base styles */
        body {
            font-family: "Georgia", "Times New Roman", serif;
            font-size: 1.1em;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            background-color: #fff;
        }
        
        /* Chapter styles */
        .chapter {
            margin: 2em auto;
            max-width: 800px;
            padding: 0 1em;
        }
        
        .chapter-title {
            font-size: 2em;
            font-weight: bold;
            text-align: center;
            margin: 1em 0;
            color: #2c3e50;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }
        
        .chapter-subtitle {
            font-size: 1.5em;
            text-align: center;
            margin: 0.5em 0 1.5em;
            color: #34495e;
            font-style: italic;
        }
        
        .chapter-content {
            text-align: justify;
        }
        
        /* Paragraph styles */
        .paragraph {
            margin: 1em 0;
            text-indent: 1.5em;
        }
        
        /* First paragraph of chapter */
        .chapter-content .paragraph:first-of-type {
            text-indent: 0;
            font-size: 1.2em;
            line-height: 1.8;
        }
        
        /* Links */
        a {
            color: #3498db;
            text-decoration: none;
        }
        
        a:hover {
            text-decoration: underline;
        }
        
        /* Navigation */
        nav#toc ol {
            list-style-type: none;
            padding-left: 1em;
        }
        
        nav#toc ol li {
            margin: 0.5em 0;
        }
        
        nav#toc a {
            color: #2c3e50;
            text-decoration: none;
        }
        
        /* Cover page */
        .cover {
            text-align: center;
            padding: 2em;
        }
        
        .cover img {
            max-width: 100%;
            height: auto;
            margin: 1em 0;
        }
        
        .cover h1 {
            font-size: 2.5em;
            margin: 1em 0;
            color: #2c3e50;
        }
        
        .cover h2 {
            font-size: 1.5em;
            color: #7f8c8d;
            margin: 0.5em 0;
        }
        """

        # Add CSS file
        nav_css = epub.EpubItem(
            uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style
        )
        book.add_item(nav_css)

        # Create spine
        book.spine = ["nav"] + epub_chapters

        # Save the EPUB file
        try:
            epub_path = os.path.join(output_dir, f"{safe_title}.epub")
            epub.write_epub(epub_path, book)
            logger.info(f"EPUB file generated: {epub_path}")
            return epub_path
        except Exception as e:
            logger.error(f"Error writing EPUB file: {str(e)}")
            # Try with a simpler filename as fallback
            simple_filename = f"novel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.epub"
            epub_path = os.path.join(output_dir, simple_filename)
            epub.write_epub(epub_path, book)
            logger.info(f"EPUB file generated with fallback name: {epub_path}")
            return epub_path
    except Exception as e:
        logger.error(f"Error creating EPUB: {str(e)}")
        raise 