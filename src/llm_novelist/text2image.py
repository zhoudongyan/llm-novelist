"""
Text2Image Module - Image Generation Integration

This module handles all interactions with the Stability AI API for image generation.
"""

import os
import requests
from dotenv import load_dotenv
from loguru import logger
from .llm_translator import translate_text

load_dotenv()

# Stability AI Configuration
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")

def generate_image(prompt, output_path, max_retries=3):
    """
    Generate an image using Stability AI's API.
    
    Args:
        prompt (str): The prompt to generate image from
        output_path (str): Path where the image should be saved
        max_retries (int): Maximum number of retry attempts
        
    Raises:
        Exception: If the API request fails or API key is missing
    """
    try:
        # Translate the prompt to English if it's not already in English
        translated_prompt = translate_text(prompt, "en")

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        api_key = STABILITY_API_KEY
        if not api_key:
            raise Exception("Missing Stability API key.")

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    "https://api.stability.ai/v2beta/stable-image/generate/sd3",
                    headers={
                        "authorization": f"Bearer {api_key}",
                        "accept": "image/*"
                    },
                    files={"none": ''},
                    data={
                        "prompt": translated_prompt,
                        "output_format": "jpeg",
                    },
                    timeout=30  # Add timeout
                )

                if response.status_code == 200:
                    # Save the image
                    with open(output_path, "wb") as f:
                        f.write(response.content)
                    logger.info(f"Image generated successfully: {output_path}")
                    return
                else:
                    error_msg = f"Stability API error (attempt {attempt + 1}/{max_retries}): {str(response.json())}"
                    logger.warning(error_msg)
                    if attempt == max_retries - 1:
                        raise Exception(error_msg)
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:
                    raise Exception(f"Failed to generate image after {max_retries} attempts: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Error in generate_image: {str(e)}")
        raise 