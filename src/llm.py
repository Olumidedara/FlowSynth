import httpx
from groq import Groq
from groq import RateLimitError

from src.config import settings

_groq_client: Groq | None = None


def _get_groq() -> Groq:
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=settings.groq_api_key, timeout=30.0)
    return _groq_client


def _call_groq(
    system_prompt: str,
    user_message: str,
    model: str | None = None,
    temperature: float = 0.7,
) -> str:
    client = _get_groq()
    response = client.chat.completions.create(
        model=model or settings.groq_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content or ""


def _call_gemini(
    system_prompt: str,
    user_message: str,
    model: str | None = None,
    temperature: float = 0.7,
) -> str:
    model_name = model or settings.gemini_model
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"

    resp = httpx.post(
        url,
        params={"key": settings.gemini_api_key},
        json={
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": user_message}]}],
            "generationConfig": {"temperature": temperature},
        },
        timeout=30.0,
    )
    resp.raise_for_status()
    data = resp.json()

    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError("Gemini returned no candidates")

    parts = candidates[0].get("content", {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts)


def call_llm(
    system_prompt: str,
    user_message: str,
    model: str | None = None,
    temperature: float = 0.7,
) -> str:
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is not set")

    try:
        return _call_groq(system_prompt, user_message, model, temperature)
    except (RateLimitError, httpx.HTTPStatusError) as exc:
        if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code not in (429, 502, 503):
            raise
    except Exception:
        pass

    if not settings.gemini_api_key:
        raise RuntimeError(
            "Groq rate limited and GEMINI_API_KEY is not set. "
            "Set GEMINI_API_KEY in .env for automatic fallback."
        )

    return _call_gemini(system_prompt, user_message, model, temperature)
