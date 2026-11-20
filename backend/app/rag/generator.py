"""
RAG Pipeline — LLM Service (Google Gemini)
"""
from typing import Optional
from app.config import settings
from app.core.exceptions import AINotConfiguredError


def _get_gemini_client():
    if not settings.GEMINI_API_KEY:
        raise AINotConfiguredError()
    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel(settings.GEMINI_MODEL)


def generate_response(
    prompt: str,
    temperature: float = 0.1,
    max_tokens: int = 4096,
) -> str:
    """Call the configured LLM and return the generated text."""
    if settings.LLM_PROVIDER == "gemini":
        return _gemini_generate(prompt, temperature, max_tokens)
    else:
        raise AINotConfiguredError()


def _gemini_generate(prompt: str, temperature: float, max_tokens: int) -> str:
    model = _get_gemini_client()
    import google.generativeai as genai
    config = genai.GenerationConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
    )
    response = model.generate_content(prompt, generation_config=config)
    return response.text
