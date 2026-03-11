import asyncio

from google import genai

from app.core.security import decrypt
from app.core.database import async_session
from app.models.settings import Settings
from sqlalchemy import select


async def _get_api_key() -> str:
    async with async_session() as session:
        result = await session.execute(select(Settings).where(Settings.id == 1))
        settings = result.scalar_one_or_none()
        if settings and settings.gemini_api_key:
            return decrypt(settings.gemini_api_key)
    return ""


async def _generate_with_retry(client, contents, max_retries: int = 5):
    """Call Gemini with exponential backoff on 429 rate limit errors."""
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=contents,
            )
            return response
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait = 2 ** attempt  # 1, 2, 4, 8, 16 seconds
                print(f"[Gemini] Rate limited, retrying in {wait}s (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(wait)
            else:
                raise
    raise ValueError("Gemini API rate limit exceeded after retries. Try again later.")


async def rephrase_message(base_message: str, variant_count: int = 1) -> list[str]:
    api_key = await _get_api_key()
    if not api_key:
        raise ValueError("Gemini API key not configured")

    client = genai.Client(api_key=api_key)
    variants = []

    for i in range(variant_count):
        response = await _generate_with_retry(
            client,
            contents=(
                f"Rephrase the following message with MINIMAL changes — just enough to avoid "
                f"pattern detection (swap a word or two, change punctuation, reorder a phrase). "
                f"Keep it as close to the original as possible. Same meaning, same tone, same structure. "
                f"IMPORTANT: Reply in the SAME language as the original message. "
                f"If the message is in Arabic, reply in Egyptian Arabic dialect (عامية مصرية), not formal Arabic. "
                f"If in English, reply in English. "
                f"Only return the rephrased message, nothing else.\n\n"
                f"Message: {base_message}"
            ),
        )
        variants.append(response.text.strip())

    return variants
