from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 2880
    database_url: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()

if not settings.jwt_secret:
    secret_file = Path(__file__).resolve().parent.parent / "data" / "jwt_secret.txt"
    secret_file.parent.mkdir(parents=True, exist_ok=True)
    if secret_file.exists():
        settings.jwt_secret = secret_file.read_text().strip()
    else:
        import secrets
        settings.jwt_secret = secrets.token_hex(32)
        secret_file.write_text(settings.jwt_secret)
