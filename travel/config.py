import os
from dataclasses import dataclass

from dotenv import load_dotenv


class ConfigError(ValueError):
    """Raised when required API configuration is missing."""


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    gemini_model: str
    kakao_rest_api_key: str


def load_settings() -> Settings:
    load_dotenv()
    names = ("GEMINI_API_KEY", "GEMINI_MODEL", "KAKAO_REST_API_KEY")
    values = {name: os.getenv(name, "").strip() for name in names}
    missing = [name for name, value in values.items() if not value]
    if missing:
        joined = ", ".join(missing)
        raise ConfigError(f"필수 설정이 없습니다: {joined}. .env.example을 참고하세요.")
    return Settings(
        gemini_api_key=values["GEMINI_API_KEY"],
        gemini_model=values["GEMINI_MODEL"],
        kakao_rest_api_key=values["KAKAO_REST_API_KEY"],
    )
