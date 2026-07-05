from groq import Groq, RateLimitError

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
    model: str,
    temperature: float = 0.7,
) -> str:
    client = _get_groq()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content or ""


def _get_groq_models() -> list[str]:
    models = [settings.groq_model]
    if settings.groq_fallback_model:
        models.append(settings.groq_fallback_model)
    if settings.groq_fallback_model_2:
        models.append(settings.groq_fallback_model_2)
    return models


def call_llm(
    system_prompt: str,
    user_message: str,
    model: str | None = None,
    temperature: float = 0.7,
) -> str:
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is not set")

    models_to_try = [model] if model else _get_groq_models()
    last_error: Exception | None = None

    for groq_model in models_to_try:
        try:
            return _call_groq(system_prompt, user_message, groq_model, temperature)
        except (RateLimitError, Exception) as exc:
            status = None
            if hasattr(exc, "status_code"):
                status = exc.status_code
            elif hasattr(exc, "response") and hasattr(exc.response, "status_code"):
                status = exc.response.status_code

            if status and status not in (429, 502, 503):
                raise

            last_error = RuntimeError(
                f"Groq model '{groq_model}' unavailable (HTTP {status})"
                if status
                else f"Groq model '{groq_model}' failed: {exc}"
            )

    raise RuntimeError(
        "All Groq models exhausted. "
        "Set GROQ_FALLBACK_MODEL and/or GROQ_FALLBACK_MODEL_2 in .env "
        "with different model names to add fallback capacity."
    ) from last_error
