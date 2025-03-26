"""
LLM Translator - AI-Powered Text Translation Tool

This module provides functionality to translate text between different languages using AI language models.
It supports multiple language pairs and provides accurate translation results.

Features:
- Support for multiple target languages
- High-quality AI-powered translations
- Batch translation capability
- Context-aware translation
- Technical and domain-specific translation support
"""

from loguru import logger
from dotenv import load_dotenv

from .llm import llm_completion
from .utils import extract_xml, clean_xml_response

# Configure loguru
logger.add("translation.log", rotation="100 MB", level="INFO")

load_dotenv()


# ============= Language Detection Functions =============
def detect_language(text):
    """
    Detect the language of a text using LLM.

    Args:
        text (str): The text to detect language for

    Returns:
        str: Detected language code or name
    """
    if not text or not text.strip():
        raise ValueError("Text for language detection cannot be empty")
    
    # For short texts, use only the first 500 characters for detection
    sample_text = text[:500] if len(text) > 500 else text
    
    system_prompt = """
    You are a language detection expert who can accurately identify the language of any text.
    Your response should only contain the language name or ISO code.
    """
    
    user_prompt = f"""
    Please identify the language of the following text. 
    
    Text:
    {sample_text}
    
    Output your response concisely in the following format:
    <response>
    language name or ISO code that you detected (e.g., English, Chinese, French, etc.)
    </response>
    """
    
    try:
        response = llm_completion(system_prompt, user_prompt)
        detected_language = extract_xml(response, "response").strip()
        logger.info(f"Detected language: {detected_language}")
        return detected_language
    
    except Exception as e:
        logger.error(f"Language detection error: {str(e)}")
        raise


def is_same_language(lang1, lang2):
    """
    Check if two language names/codes refer to the same language.
    
    Args:
        lang1 (str): First language name or code
        lang2 (str): Second language name or code
        
    Returns:
        bool: True if languages are the same, False otherwise
    """
    if not lang1 or not lang2:
        return False
    
    # Normalize language names/codes
    lang1 = lang1.lower().strip()
    lang2 = lang2.lower().strip()
    
    # Direct match
    if lang1 == lang2:
        return True
    
    # Common language code/name pairs
    language_map = {
        "zh": ["chinese", "mandarin", "中文", "汉语", "普通话"],
        "en": ["english", "英语", "英文"],
        "fr": ["french", "français", "法语", "法文"],
        "es": ["spanish", "español", "西班牙语"],
        "de": ["german", "deutsch", "德语", "德文"],
        "ja": ["japanese", "日本语", "日语"],
        "ko": ["korean", "한국어", "朝鲜语", "韩语"],
        "ru": ["russian", "русский", "俄语", "俄文"],
        "it": ["italian", "italiano", "意大利语"],
        "pt": ["portuguese", "português", "葡萄牙语"],
        "ar": ["arabic", "العربية", "阿拉伯语"],
        "hi": ["hindi", "हिन्दी", "印地语"],
        "bn": ["bengali", "বাংলা", "孟加拉语"],
        "vi": ["vietnamese", "tiếng việt", "越南语"]
    }
    
    # Check if languages match based on common codes and names
    for code, names in language_map.items():
        if (lang1 == code or lang1 in names) and (lang2 == code or lang2 in names):
            return True
    
    return False


# ============= Translation Functions =============
def translate_text(text, target_language, source_language=None, context=None, preserve_format=True, skip_same_language=True):
    """
    Translate text to the target language using LLM.

    Args:
        text (str): The text to translate
        target_language (str): Target language code or name (e.g., "zh", "fr", "Chinese", "French")
        source_language (str, optional): Source language code or name (auto-detected if not provided)
        context (str, optional): Additional context to improve translation accuracy
        preserve_format (bool): Whether to preserve original formatting (default: True)
        skip_same_language (bool): Skip translation if source is already target language (default: True)

    Returns:
        str: The translated text

    Raises:
        ValueError: If the text is empty or target language is not provided
    """
    if not text or not text.strip():
        raise ValueError("Text to translate cannot be empty")
    
    if not target_language:
        raise ValueError("Target language must be provided")

    # Detect source language if not provided
    if not source_language and skip_same_language:
        try:
            detected_language = detect_language(text)
            source_language = detected_language
            logger.info(f"Auto-detected source language: {source_language}")
        except Exception as e:
            logger.warning(f"Failed to auto-detect language: {str(e)}")
    
    # Check if source and target languages are the same
    if skip_same_language and source_language and is_same_language(source_language, target_language):
        logger.info(f"Source language '{source_language}' is the same as target language '{target_language}'. Skipping translation.")
        return text

    logger.info(f"Translating text from {source_language or 'auto-detected'} to {target_language}")
    
    system_prompt = """
    You are a professional translator with expertise in multiple languages. 
    Your translations are accurate, natural, and maintain the original tone and meaning.
    For technical content, you correctly use domain-specific terminology.
    For creative content, you preserve the style and emotional impact of the original.
    """

    # Build the user prompt with all the details
    user_prompt = f"""
    Please translate the following text to {target_language}.
    
    {f"The source language is: {source_language}" if source_language else ""}
    {f"Context: {context}" if context else ""}
    
    Text to translate:
    {text}
    
    {"Please preserve the original formatting." if preserve_format else ""}

    Output your response concisely in the following XML format:
    <response>
    translated text in {target_language}
    </response>
    """
    
    try:
        # Get translation from LLM
        response = llm_completion(system_prompt, user_prompt)
        
        # Extract and clean the translated text
        translated_text = extract_xml(response, "response")
        logger.info(f"Translation completed successfully")
        return translated_text
    
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        raise


def batch_translate(texts, target_language, source_language=None, context=None, skip_same_language=True):
    """
    Translate a batch of texts to the target language.

    Args:
        texts (list): List of texts to translate
        target_language (str): Target language code or name
        source_language (str, optional): Source language code or name
        context (str, optional): Additional context for all texts
        skip_same_language (bool): Skip translation if source is already target language

    Returns:
        list: List of translated texts
    """
    if not texts:
        return []
    
    logger.info(f"Batch translating {len(texts)} texts to {target_language}")
    
    results = []
    for i, text in enumerate(texts):
        try:
            translated = translate_text(
                text, 
                target_language, 
                source_language, 
                context,
                skip_same_language=skip_same_language
            )
            results.append(translated)
            logger.info(f"Translated text {i+1}/{len(texts)}")
        except Exception as e:
            logger.error(f"Error translating text {i+1}: {str(e)}")
            results.append(None)  # Add None for failed translations
    
    return results


def translate_with_glossary(text, target_language, glossary, source_language=None, skip_same_language=True):
    """
    Translate text using a custom glossary for specialized terminology.

    Args:
        text (str): Text to translate
        target_language (str): Target language code or name
        glossary (dict): Dictionary of terms and their translations
        source_language (str, optional): Source language code or name
        skip_same_language (bool): Skip translation if source is already target language

    Returns:
        str: Translated text with specialized terminology
    """
    if not text or not target_language or not glossary:
        raise ValueError("Text, target language, and glossary must be provided")
    
    # Detect source language if not provided
    if not source_language and skip_same_language:
        try:
            detected_language = detect_language(text)
            source_language = detected_language
            logger.info(f"Auto-detected source language: {source_language}")
        except Exception as e:
            logger.warning(f"Failed to auto-detect language: {str(e)}")
    
    # Check if source and target languages are the same
    if skip_same_language and source_language and is_same_language(source_language, target_language):
        logger.info(f"Source language '{source_language}' is the same as target language '{target_language}'. Skipping translation.")
        return text
    
    # Format glossary for prompt
    glossary_text = "\n".join([f"{term}: {translation}" for term, translation in glossary.items()])
    
    system_prompt = """
    You are a professional translator specializing in technical and domain-specific content.
    Your translations maintain accurate terminology according to the provided glossary.
    """
    
    user_prompt = f"""
    Please translate the following text to {target_language}, using the provided glossary for specialized terms.
    
    {f"The source language is: {source_language}" if source_language else ""}
    
    Glossary:
    {glossary_text}
    
    Text to translate:
    {text}

    Output your response concisely in the following XML format:
    <response>
    translated text in {target_language}
    </response>
    """
    
    try:
        response = llm_completion(system_prompt, user_prompt)
        translated_text = extract_xml(response, "response")
        return translated_text
    
    except Exception as e:
        logger.error(f"Translation with glossary error: {str(e)}")
        raise


# ============= CLI Functions =============
def main():
    """
    Command line interface for the translator.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="LLM Translator - AI-powered text translation")
    parser.add_argument("--text", type=str, help="Text to translate")
    parser.add_argument("--file", type=str, help="File containing text to translate")
    parser.add_argument("--target", type=str, required=True, help="Target language (e.g., en, fr, zh)")
    parser.add_argument("--source", type=str, help="Source language (auto-detect if not specified)")
    parser.add_argument("--context", type=str, help="Additional context to improve translation")
    parser.add_argument("--output", type=str, help="Output file for the translation")
    parser.add_argument("--force", action="store_true", help="Force translation even if source and target languages are the same")
    
    args = parser.parse_args()
    
    if not args.text and not args.file:
        parser.error("Either --text or --file must be provided")
    
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            logger.error(f"Error reading file: {str(e)}")
            return
    else:
        text = args.text
    
    try:
        translated = translate_text(
            text,
            args.target,
            args.source,
            args.context,
            skip_same_language=not args.force
        )
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(translated)
            print(f"Translation saved to {args.output}")
        else:
            print(translated)
            
    except Exception as e:
        logger.error(f"Translation failed: {str(e)}")


if __name__ == "__main__":
    main() 