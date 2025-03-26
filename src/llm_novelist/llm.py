"""
LLM Module - Language Model Integration

This module handles all interactions with the OpenAI API for text generation.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

# OpenAI Configuration
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")  # Default to GPT-3.5 if not specified
MAX_TOKENS = os.getenv("MAX_TOKENS", 8192)


def llm_completion(system_prompt, user_prompt, max_retries=3):
    """
    Send a request to the LLM API and get the completion response.

    Args:
        system_prompt (str): The system prompt that sets the context and behavior
        user_prompt (str): The user's input prompt or question
        max_retries (int): Maximum number of retry attempts

    Returns:
        str: The LLM's response text

    Raises:
        Exception: If the API request fails after all retries
    """
    if not OPENAI_API_KEY:
        raise Exception("OpenAI API key is not set")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=MAX_TOKENS,
            )
            content = response.choices[0].message.content
            logger.info(f"========== LLM RESPONSE START ==========\n{content}")
            logger.info(f"========== LLM RESPONSE END ==========")
            return content
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
            if attempt == max_retries - 1:
                raise Exception(f"Failed to get LLM response after {max_retries} attempts: {str(e)}")
            continue 