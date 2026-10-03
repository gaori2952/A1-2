import requests
from travel.api_trace import exchange

from travel.config import Settings
from travel.errors import TravelError, validation_error
from travel.prompts import RECOMMENDATION_SCHEMA, build_recommendation_prompt
from travel.validation import ValidationError, validate_recommendation


GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def generate_text(prompt: str, settings: Settings, *, json_schema: dict[str, object] | None = None) -> str:
    url = f"{GEMINI_BASE_URL}/{settings.gemini_model}:generateContent"
    body: dict[str, object] = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7},
    }
    if json_schema:
        body["generationConfig"] = {
            "temperature": 0.3,
            "responseMimeType": "application/json",
            "responseSchema": json_schema,
        }
    try:
        response = exchange(
            requests.post,
            url,
            provider="gemini", stage=("recommendation" if json_schema else "report"),
            secrets=(settings.gemini_api_key, settings.kakao_rest_api_key),
            headers={"x-goog-api-key": settings.gemini_api_key},
            json=body,
            timeout=(5, 60),
        )
    except requests.Timeout as exc:
        raise TravelError("llm", "TIMEOUT", "Gemini 요청 시간이 초과되었습니다.") from exc
    except requests.RequestException as exc:
        raise TravelError("llm", "NETWORK_ERROR", "Gemini API에 연결할 수 없습니다.") from exc

    if response.status_code in (401, 403):
        raise TravelError("llm", f"HTTP_{response.status_code}", "Gemini API 인증에 실패했습니다. 키와 이용 권한을 확인하세요.")
    if response.status_code == 429:
        raise TravelError("llm", "HTTP_429", "Gemini API 사용 한도에 도달했습니다.")
    if response.status_code >= 400:
        raise TravelError("llm", f"HTTP_{response.status_code}", "Gemini API 요청이 실패했습니다.")

    try:
        payload = response.json()
        candidates = payload.get("candidates", [])
        text = "".join(
            part.get("text", "")
            for part in candidates[0]["content"]["parts"]
            if isinstance(part, dict) and isinstance(part.get("text", ""), str)
        )
    except (ValueError, KeyError, IndexError, TypeError, AttributeError) as exc:
        raise TravelError("llm", "INVALID_RESPONSE", "Gemini 응답 형식이 올바르지 않습니다.") from exc
    if not text.strip():
        raise TravelError("llm", "EMPTY_RESPONSE", "Gemini가 사용할 수 있는 텍스트를 반환하지 않았습니다.")
    return text.strip()


def request_recommendation(settings: Settings, travel_date: str, errors: list[dict[str, object]]) -> dict[str, object]:
    previous_problem: str | None = None
    for attempt in (1, 2):
        prompt = build_recommendation_prompt(travel_date, previous_problem)
        try:
            raw = generate_text(prompt, settings, json_schema=RECOMMENDATION_SCHEMA)
            recommendation = validate_recommendation(raw)
        except ValidationError as exc:
            problem = str(exc)
            if attempt == 1:
                previous_problem = problem
                continue
            errors.append(validation_error(problem, attempt=2, recovered=False))
            if previous_problem:
                errors.append(validation_error(previous_problem, attempt=1, recovered=False))
            raise TravelError("recommendation", "INVALID_RECOMMENDATION", "추천 응답 검증에 두 번 실패했습니다.") from exc
        except TravelError:
            if previous_problem:
                errors.append(validation_error(previous_problem, attempt=1, recovered=False))
            raise
        if previous_problem:
            errors.append(validation_error(previous_problem, attempt=1, recovered=True))
        return recommendation
    raise TravelError("recommendation", "INVALID_RECOMMENDATION", "추천 응답 검증에 실패했습니다.")
