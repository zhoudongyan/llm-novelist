"""
LLM Novelist - AI-Powered Novel Generation Tool

This module provides functionality to generate complete novels using AI language models.
It supports multiple writing styles, automatic chapter generation, and EPUB formatting.

Features:
- Multiple writing styles support (fantasy, sci-fi, romance, etc.)
- Automatic chapter outline generation
- Dynamic chapter content generation
- Cover image generation using Stability AI
- Multiple output formats (EPUB, Markdown, TXT)
- Configurable chapter count and writing style
- Detailed logging and error handling
"""

import os
import re
import random
import argparse

from dotenv import load_dotenv
from loguru import logger

from .chapter import Chapter
from .writing_styles import WRITING_STYLES
from .llm import llm_completion
from .text2image import generate_image
from .utils import (
    extract_xml,
    generate_unique_dir,
    create_safe_filename,
    create_epub,
)

# Configure loguru
logger.add("novel_generation.log", rotation="500 MB", level="INFO")

load_dotenv()


# ============= XML Parsing Functions =============
def parse_style_and_chapters(response):
    """
    Parse XML response specifically for style and chapter determination.

    Args:
        response (str): XML response from LLM containing style and chapter information

    Returns:
        dict: Dictionary with style, chapters, and explanation, or None if parsing fails
    """
    logger.info("Parsing style and chapters determination")
    try:
        style = extract_xml(response, "style")
        chapters = extract_xml(response, "chapters")
        explanation = extract_xml(response, "explanation")

        if style and chapters:
            try:
                return {
                    "style": style,
                    "chapters": int(chapters),
                    "explanation": explanation or "No explanation provided",
                }
            except ValueError:
                logger.warning(f"Failed to parse chapters as integer: {chapters}")
        return None
    except Exception as e:
        logger.error(f"Error parsing style and chapters: {str(e)}")
        return None


def parse_chapter_outline(response) -> list[Chapter]:
    """
    Parse XML response specifically for chapter outline.

    Args:
        response (str): XML response from LLM containing chapter outline information

    Returns:
        list: List of chapter dictionaries, or None if parsing fails
    """
    logger.info("Parsing chapter outline")
    try:
        chapters_xml = extract_xml(response, "chapters")
        if not chapters_xml:
            logger.warning("No <chapters> tag found in the response")
            return None

        # Parse individual chapter entries
        chapters = []
        chapter_numbers = re.findall(r"<chapter (\d+)>", chapters_xml)

        for num in chapter_numbers:
            # Extract each chapter's content using the chapter number
            chapter_content = re.search(
                f"<chapter {num}>(.*?)</chapter {num}>", chapters_xml, re.DOTALL
            )

            if chapter_content:
                chapter_text = chapter_content.group(1).strip()
                title = extract_xml(chapter_text, "title")
                overview = extract_xml(chapter_text, "overview")

                if title and overview:
                    chapters.append(Chapter(number=num, title=title, overview=overview))

        return chapters if chapters else None
    except Exception as e:
        logger.error(f"Error parsing chapter outline: {str(e)}")
        return None


# ============= Story Outline Generation =============
def generate_story_outlines(prompt, style):
    """
    Generate multiple story outlines based on the prompt and writing style.

    Args:
        prompt (str): The story prompt or concept
        style (str): The writing style to use

    Returns:
        list: A list of generated story outlines
    """
    system_prompt = f"{WRITING_STYLES[style]['system_prompt']}"
    user_prompt = f"""
    Generate 5 {WRITING_STYLES[style]['name']} story outlines based on user prompt.

    User prompt:
    {prompt}

    Requirements:
    1. All outlines should be in the same language as the user prompt

    Output your response concisely in the following format:
    <response>
    <outline 1>outline 1</outline 1>
    <outline 2>outline 2</outline 2>
    <outline 3>outline 3</outline 3>
    <outline 4>outline 4</outline 4>
    <outline 5>outline 5</outline 5>
    </response>
    """
    response = llm_completion(system_prompt, user_prompt)
    return extract_xml(response, "response")


def select_best_outline(outlines, style):
    """
    Select or combine the best story outline from multiple options.

    Args:
        outlines (list): List of story outlines to choose from
        style (str): The writing style to use

    Returns:
        str: The selected or combined best outline
    """
    system_prompt = f"{WRITING_STYLES[style]['system_prompt']}"
    user_prompt = f"""
    Please select the most engaging outline, or combine the best elements from multiple candidate outlines into a new one.
    The most important thing is that the story should be engaging, unique, and creative.

    Candidate outlines:
    {outlines}

    Output your response concisely in the following format:
    <response>
    content of the best outline, in the same language as candidate outlines
    </response>
    """
    response = llm_completion(system_prompt, user_prompt)
    return extract_xml(response, "response")


def refine_story_outline(outline, style):
    """
    Refine and improve a story outline to make it more engaging.

    Args:
        outline (str): The story outline to improve
        style (str): The writing style to use

    Returns:
        str: The improved story outline
    """
    system_prompt = f"{WRITING_STYLES[style]['system_prompt']}"
    user_prompt = f"""
    Please improve and refine this story outline to make it more engaging.

    Story outline to refine:
    {outline}

    Output your response concisely in the following format:
    <response>
    content of the refined outline, in the same language as the story outline
    </response>
    """
    response = llm_completion(system_prompt, user_prompt)
    return extract_xml(response, "response")


def generate_story_title(outline, style):
    """
    Generate a title for the story based on the outline.

    Args:
        outline (str): The story outline
        style (str): The writing style to use

    Returns:
        str: The generated story title
    """
    system_prompt = f"{WRITING_STYLES[style]['system_prompt']}"
    user_prompt = f"""
    Please create a beautiful title based on the story outline.

    Story outline to create title for:
    {outline}

    Requirements:
    1. The title should be in the same language as the story outline

    Output your response concisely in the following format:
    <response>
    beautiful story title without any tags or extra texts, e.g. not "The Great Gatsby" but The Great Gatsby
    </response>
    """
    response = llm_completion(system_prompt, user_prompt)
    return extract_xml(response, "response").strip()


def generate_chapter_outline(story_outline, num_chapters, style) -> list[Chapter]:
    """
    Generate a detailed chapter-by-chapter outline for the story.

    Args:
        story_outline (str): The story outline
        num_chapters (int): Number of chapters to generate
        style (str): The writing style to use

    Returns:
        list[Chapter]: A list of Chapter objects
    """
    logger.info("Generating story outline and chapter summaries...")

    system_prompt = f"{WRITING_STYLES[style]['system_prompt']}"
    user_prompt = f"""
    Please create a {WRITING_STYLES[style]['name']} story outline with {num_chapters} chapters based on story outline.

    Story outline:
    {story_outline}

    Requirements:
    1. Each chapter must have a unique title
    2. Chapter titles should be descriptive and engaging
    3. Chapter overviews should be 2-3 sentences
    4. Do not include any special characters in titles
    5. Generate exactly {num_chapters} chapters numbered from 1 to {num_chapters}
    6. All titles and overviews should be in the same language as the story outline
    
    Output your response concisely in the following format:
    <response>
    <chapters>
    <chapter 1>
      <title>First Chapter Title</title>
      <overview>Brief overview of chapter one content.</overview>
    </chapter 1>
    ...
    <chapter N>
      <title>Chapter N Title</title>
      <overview>Brief overview of chapter N content.</overview>
    </chapter N>
    </chapters>
    </response>
    """

    try:
        # Generate initial outline
        response = llm_completion(system_prompt, user_prompt)
        response = extract_xml(response, "response")

        # Parse XML using specific chapter outline parser
        result = parse_chapter_outline(response)
        return result

    except Exception as e:
        logger.error(f"Error in generate_chapter_outline: {str(e)}")
        return None


# ============= Chapter Content Generation =============
def _generate_chapter_with_retry(generate_func, chapter_num, *args, **kwargs):
    """
    Generic retry function for chapter generation.

    Args:
        generate_func: Function that actually generates chapter content
        chapter_num: Chapter number for logging purposes
        *args: Positional arguments to pass to the generation function
        **kwargs: Keyword arguments to pass to the generation function

    Returns:
        str: Generated chapter content
    """
    max_retries = 3  # Maximum number of retries
    min_length = 1000  # Minimum chapter length
    retry_count = 0
    chapter_content = None

    while retry_count < max_retries:
        try:
            chapter_content = generate_func(*args, **kwargs)

            content_length = len(str(chapter_content)) if chapter_content else 0
            if content_length >= min_length:
                break

            retry_count += 1
            if retry_count < max_retries:
                logger.warning(
                    f"Chapter {chapter_num} length insufficient ({content_length} < {min_length}), retry {retry_count}/{max_retries}..."
                )
            else:
                logger.warning(
                    f"Chapter {chapter_num} length still insufficient after {max_retries} attempts, using last generated content"
                )

        except Exception as e:
            logger.error(
                f"Error writing chapter {chapter_num} (attempt {retry_count + 1}/{max_retries}): {str(e)}"
            )
            retry_count += 1
            if retry_count >= max_retries:
                logger.error(
                    f"Max retries reached with errors for chapter {chapter_num}, using last successful content or None"
                )
                break

    if chapter_content is None:
        logger.error(
            f"Failed to generate content for chapter {chapter_num} after {max_retries} attempts"
        )
        chapter_content = f"[Error: Content generation failed for Chapter {chapter_num}]"

    return chapter_content


def _generate_chapter_content(system_prompt, user_prompt):
    """
    Generic function for generating chapter content.

    Args:
        system_prompt (str): System prompt for the LLM
        user_prompt (str): User prompt for the LLM

    Returns:
        str: Generated chapter content
    """
    response = llm_completion(system_prompt, user_prompt)
    return extract_xml(response, "response")


def write_first_chapter(story_outline, chapter_title, chapter_overview, style, chapter_num=1):
    """
    Write the first chapter of the story, setting up the world and characters.

    Args:
        story_outline (str): The overall story outline
        chapter_title (str): The title of the first chapter
        chapter_overview (str): The overview of the first chapter
        style (str): The writing style to use
        chapter_num (int): The chapter number, defaults to 1

    Returns:
        str: The generated first chapter content
    """
    system_prompt = f"{WRITING_STYLES[style]['system_prompt']}"
    user_prompt = f"""Please write the first chapter of the story based on the story outline, chapter title and overview.

    Story outline:
    {story_outline}

    Chapter title (the title of the first chapter):
    {chapter_title}

    Chapter overview (the overview of the first chapter):
    {chapter_overview}
    
    This first chapter should:
    1. Set up the story world and introduce key characters
    2. Establish the tone and atmosphere
    3. Hook the reader's interest
    4. Begin building the main conflict or tension

    Output your response concisely in the following format:
    <response>
    ONLY content(not including chapter title and overview) of the first chapter, in the same language as the story outline
    </response>
    """
    return _generate_chapter_with_retry(
        lambda: _generate_chapter_content(system_prompt, user_prompt), chapter_num
    )


def write_middle_chapter(
    story_outline, previous_chapter, chapter_title, chapter_overview, style, chapter_num
):
    """
    Write a middle chapter of the story, maintaining consistency and advancing the plot.

    Args:
        story_outline (str): The overall story outline
        previous_chapter (str): The content of previous chapter
        chapter_title (str): The title of the current chapter
        chapter_overview (str): The overview of the current chapter
        style (str): The writing style to use
        chapter_num (int): The chapter number

    Returns:
        str: The generated chapter content
    """
    system_prompt = f"{WRITING_STYLES[style]['system_prompt']}"
    user_prompt = f"""
    Please continue writing the next chapter based on the story outline, previous chapters, chapter title and overview.

    Story outline:
    {story_outline}

    Content of the previous chapter:
    {previous_chapter}

    Chapter title (the title of the next chapter):
    {chapter_title}

    Chapter overview (the overview of the next chapter):
    {chapter_overview}
    
    This next chapter should:
    1. Maintain consistency with previous events and character development
    2. Advance the plot naturally
    3. Keep the established tone and style
    4. Build upon the story's momentum 

    Output your response concisely in the following format:
    <response>
    ONLY content(not including chapter title and overview) of the next chapter, in the same language as the story outline
    </response>
    """
    return _generate_chapter_with_retry(
        lambda: _generate_chapter_content(system_prompt, user_prompt), chapter_num
    )


def write_final_chapter(
    story_outline, previous_chapter, chapter_title, chapter_overview, style, chapter_num
):
    """
    Write the final chapter of the story, focusing on resolution and closure.

    Args:
        story_outline (str): The overall story outline
        previous_chapter (str): The content of previous chapter
        chapter_title (str): The title of the final chapter
        chapter_overview (str): The overview of the final chapter
        style (str): The writing style to use
        chapter_num (int): The chapter number

    Returns:
        str: The generated final chapter content
    """
    system_prompt = f"{WRITING_STYLES[style]['system_prompt']}"
    user_prompt = f"""Please write the final chapter of the story based on the story outline, previous chapters, chapter title and overview.

    Story outline:
    {story_outline}

    Content of the previous chapter:
    {previous_chapter}

    Chapter title (the title of the final chapter):
    {chapter_title}

    Chapter overview (the overview of the final chapter):
    {chapter_overview}
    
    This final chapter should:
    1. Resolve the main conflicts and storylines
    2. Provide satisfying closure for character arcs
    3. Maintain consistency with previous events
    4. Leave a lasting impression on the reader
    5. Create a memorable ending that fits the story's tone

    Output your response concisely in the following format:
    <response>
    ONLY content(not including chapter title and overview) of the final chapter, in the same language as the story outline
    </response>
    """
    return _generate_chapter_with_retry(
        lambda: _generate_chapter_content(system_prompt, user_prompt), chapter_num
    )


# ============= Cover Generation Functions =============
def generate_cover_prompt(story_outline):
    """
    Generate a detailed prompt for the cover image using LLM.

    Args:
        story_outline (str): The story outline to generate cover for

    Returns:
        str: The generated cover image prompt
    """
    system_prompt = """
    You are a world-class book cover designer with exceptional artistic vision and commercial instinct. Your covers consistently win industry awards and drive book sales through their visual impact and storytelling.

    When designing covers, you focus on:
    - Creating a single powerful, iconic visual that captures the story's essence
    - Using color psychology to evoke the right emotional response
    - Balancing artistic expression with market appeal
    - Creating depth through thoughtful composition, lighting, and perspective
    - Ensuring the design works at all scales (thumbnail to full size)
    - Selecting appropriate typography that complements the visual elements
    - Avoiding clichés while respecting genre conventions

    You excel at translating complex narratives into simple, striking visuals that instantly communicate the story's genre, tone, and core themes."""

    user_prompt = f"""
    Based on story outline, create a detailed description for a striking book cover design.

    Story outline:
    {story_outline}
     
    Your description should:
    1. Describe a SINGLE powerful focal image or scene (not multiple disconnected elements)
    2. Specify a cohesive color palette (3-4 colors maximum)
    3. Define the lighting mood and atmosphere
    4. Suggest composition and visual hierarchy
    5. Express the emotional tone the cover should evoke
    6. Focus on visual elements only. Do not include text placement or typography suggestions.
    7. Make the design distinctive and memorable while aligning with the story's genre.

    Output your response concisely in the following format:
    <response>
    book cover description in English, without any tags or extra texts
    </response>
    """

    response = llm_completion(system_prompt, user_prompt)
    return extract_xml(response, "response")


def create_cover_image(story_outline, output_path):
    """
    Generate a book cover image using Stability AI's API.

    Args:
        story_outline (str): The story outline to generate cover for
        output_path (str): Path where the cover image should be saved
    """
    try:
        # Generate the cover prompt using LLM
        cover_prompt = generate_cover_prompt(story_outline)

        # Generate the image using the text2image module
        generate_image(cover_prompt, output_path)

    except Exception as e:
        logger.error(f"Failed to generate cover: {str(e)}")
        raise


# ============= File Output Functions =============
def save_novel_content(
    title, story_outline, chapters, author, cover_image_path, output_dir, safe_title
):
    """
    Save novel content in multiple formats (EPUB, Markdown, and text).

    Args:
        title (str): Novel title
        story_outline (str): Story outline
        chapters (list): List of chapter objects
        author (str): Author name
        cover_image_path (str): Path to cover image
        output_dir (str): Output directory path
        safe_title (str): Safe title for filenames
    """

    try:
        # Save markdown format
        md_content = f"# {title}\n\n"
        for i, chapter in enumerate(chapters):
            try:
                md_content += f"## Chapter {i+1}: {chapter.title}\n\n"
                md_content += f"{chapter.content}\n\n"
            except Exception as e:
                logger.warning(f"Error formatting chapter {i+1} for markdown: {str(e)}")
                md_content += f"## Chapter {i+1}\n\n{chapter.content}\n\n"

        md_path = os.path.join(output_dir, f"{safe_title}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        logger.info(f"Markdown file saved: {md_path}")
    except Exception as e:
        logger.error(f"Failed to save markdown file: {str(e)}")

    try:
        # Create EPUB format using the create_epub function
        create_epub(
            title, story_outline, chapters, author, cover_image_path, output_dir, safe_title
        )
    except Exception as e:
        logger.error(f"Failed to create EPUB file: {str(e)}")
        raise


# ============= Core Generation Flow =============
def determine_style_and_chapters(prompt, style=None, num_chapters=None):
    """
    Determine the appropriate writing style and number of chapters based on the prompt.

    Args:
        prompt (str): Story prompt
        style (str, optional): User-specified style
        num_chapters (int, optional): User-specified number of chapters

    Returns:
        tuple: (style, num_chapters)
    """
    if style and num_chapters:
        return style, num_chapters

    system_prompt = """
    You are an expert literary analyst who can determine the most appropriate writing style and chapter count for a story based on user prompt.
    """

    user_prompt = f"""
    Analyze the story prompt and return an style from the list of available styles and chapters count.

    Story prompt:
    {prompt}

    Available styles:
    {', '.join(WRITING_STYLES.keys())}

    Important rules:
    1. Choose a style only from the available options
    2. Chapters should be a number between 5 and 15

    Output your response concisely in the following format:
    <response>
    <style>your selected style</style>
    <chapters>your selected chapters count, a number, not a range</chapters>
    <explanation>your explanation</explanation>
    </response>
    """

    # Set default values
    fallback_style = style if style else random.choice(list(WRITING_STYLES.keys()))
    fallback_chapters = num_chapters if num_chapters else 10

    try:
        response = llm_completion(system_prompt, user_prompt)
        response = extract_xml(response, "response")

        # Parse XML response using specific style and chapters parser
        result = parse_style_and_chapters(response)
        if result is None:
            # Use fallback values if parsing fails
            logger.warning("Failed to parse style determination response")
            return fallback_style, fallback_chapters

        # Validate the returned values
        determined_style = result.get("style")
        determined_chapters = result.get("chapters")

        if not determined_style or determined_style not in WRITING_STYLES:
            logger.warning(f"Invalid style returned: {determined_style}")
            determined_style = fallback_style

        if (
            not isinstance(determined_chapters, int)
            or determined_chapters < 5
            or determined_chapters > 15
        ):
            logger.warning(f"Invalid chapter count returned: {determined_chapters}")
            determined_chapters = fallback_chapters

        # Use user-specified values if provided
        final_style = style if style else determined_style
        final_chapters = num_chapters if num_chapters else determined_chapters

        logger.info(f"Determined style: {final_style}, chapters: {final_chapters}")
        logger.info(f"AI explanation: {result.get('explanation', 'No explanation provided')}")

        return final_style, final_chapters

    except Exception as e:
        logger.warning(f"Error in style determination: {str(e)}")
        logger.info(
            f"Using fallback values - style: {fallback_style}, chapters: {fallback_chapters}"
        )
        return fallback_style, fallback_chapters


def generate_novel_content(prompt, num_chapters, style):
    """
    Generate the complete novel content including outline, title, and all chapters.

    Args:
        prompt (str): The story prompt
        num_chapters (int): Number of chapters to generate
        style (str): The writing style to use

    Returns:
        tuple: (title, story_outline, chapters)

    Raises:
        ValueError: If the style is not supported
    """
    if style not in WRITING_STYLES:
        raise ValueError(
            f"Unsupported writing style: {style}. Supported styles: {', '.join(WRITING_STYLES.keys())}"
        )

    outlines = generate_story_outlines(prompt, style)
    logger.info("Generated story outlines")

    best_outline = select_best_outline(outlines, style)
    logger.info("Selected best outline")

    refined_outline = refine_story_outline(best_outline, style)
    logger.info("Refined outline")

    title = generate_story_title(refined_outline, style)
    logger.info("Generated title")

    chapters = generate_chapter_outline(refined_outline, num_chapters, style)
    logger.info("Generated detailed outline")

    # Write first chapter
    logger.info("Writing first chapter...")
    chapters[0].content = write_first_chapter(
        refined_outline, chapters[0].title, chapters[0].overview, style, 1
    )
    logger.info("Written first chapter")

    # Write middle chapters
    for i in range(num_chapters - 2):
        logger.info(f"Writing chapter {i+2}...")
        chapters[i + 1].content = write_middle_chapter(
            refined_outline,
            chapters[i].content,
            chapters[i + 1].title,
            chapters[i + 1].overview,
            style,
            i + 2,
        )

    # Write final chapter
    logger.info(f"Writing final chapter {num_chapters}...")
    chapters[-1].content = write_final_chapter(
        refined_outline,
        chapters[-2].content,
        chapters[-1].title,
        chapters[-1].overview,
        style,
        num_chapters,
    )

    return title, refined_outline, chapters


# ============= API Functions =============
def generate_novel(prompt, num_chapters=None, style=None, output_dir="output", author="AI"):
    """
    Generate a novel programmatically.

    Args:
        prompt (str): Story prompt
        num_chapters (int, optional): Number of chapters (default: determined by AI)
        style (str, optional): Writing style (default: determined by AI)
        output_dir (str): Base output directory (default: 'output')
        author (str): Author name (default: 'AI')

    Returns:
        dict: A dictionary containing the generated novel information
    """
    try:
        # Determine style and chapters if not provided
        style, num_chapters = determine_style_and_chapters(prompt, style, num_chapters)

        # Generate unique output directory
        unique_dir = generate_unique_dir(output_dir)
        logger.info(f"Using output directory: {unique_dir}")

        logger.info(f"Starting novel generation")
        logger.info(f"Style: {WRITING_STYLES[style]['name']}, Number of chapters: {num_chapters}")
        logger.info(f"Prompt: {prompt}")

        # Generate novel
        title, story_outline, chapters = generate_novel_content(prompt, num_chapters, style)

        # Create a safe title for filenames
        safe_title = create_safe_filename(title)
        logger.info(f"Original title: '{title}', Safe title for files: '{safe_title}'")

        # Create cover
        cover_path = None
        try:
            cover_path = os.path.join(unique_dir, "cover.png")
            create_cover_image(story_outline, cover_path)
            logger.info(f"Cover generated: {cover_path}")
        except Exception as e:
            logger.error(f"Failed to generate cover: {str(e)}")
            logger.info("Continuing without cover image")

        # Save novel content in different formats
        try:
            save_novel_content(
                title, story_outline, chapters, author, cover_path, unique_dir, safe_title
            )
        except Exception as e:
            logger.error(f"Failed to save novel content: {str(e)}")
            raise

        logger.success("Novel generation completed!")

        # The actual files saved might use the safe_title, not the original title
        epub_path = os.path.join(unique_dir, f"{safe_title}.epub")
        md_path = os.path.join(unique_dir, f"{safe_title}.md")

        # Check if files exist, otherwise look for fallback names
        if not os.path.exists(epub_path):
            # Look for fallback epub
            fallback_files = [f for f in os.listdir(unique_dir) if f.endswith(".epub")]
            epub_path = os.path.join(unique_dir, fallback_files[0]) if fallback_files else None

        return {
            "status": "success",
            "title": title,
            "output_dir": unique_dir,
            "files": {
                "epub": epub_path if os.path.exists(epub_path) else None,
                "markdown": md_path if os.path.exists(md_path) else None,
                "cover": cover_path if cover_path and os.path.exists(cover_path) else None,
            },
        }

    except Exception as e:
        logger.error(f"Error during generation: {str(e)}")
        return {"status": "error", "message": str(e)}


# ============= CLI Functions =============
def parse_args():
    """Parse command line arguments for novel generation."""
    parser = argparse.ArgumentParser(description="AI Novel Generator")
    parser.add_argument("--prompt", type=str, required=True, help="Story prompt")
    parser.add_argument(
        "--chapters",
        type=int,
        help="Number of chapters (optional, will be determined by AI if not specified)",
    )
    parser.add_argument(
        "--style",
        type=str,
        choices=list(WRITING_STYLES.keys()),
        help=f'Writing style (optional, will be determined by AI if not specified. Options: {", ".join(WRITING_STYLES.keys())})',
    )
    parser.add_argument(
        "--output-dir", type=str, default="output", help="Output directory (default: output)"
    )
    parser.add_argument("--author", type=str, default="AI", help="Author name (default: AI)")
    return parser.parse_args()


def main():
    """Entry point for the command-line interface."""
    # Parse command line arguments
    args = parse_args()

    # Call generate_novel with command line arguments
    result = generate_novel(
        prompt=args.prompt,
        num_chapters=args.chapters,
        style=args.style,
        output_dir=args.output_dir,
        author=args.author,
    )

    if result["status"] == "error":
        raise Exception(result["message"])


if __name__ == "__main__":
    main()
