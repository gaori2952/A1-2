import json
import re
from datetime import date
from typing import Any


class ValidationError(ValueError):
    """Raised when user input or model output violates the data contract."""


def validate_date(value: str) -> str:
    if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value) is None:
        raise ValidationError("날짜는 YYYY-MM-DD 형식이어야 합니다.")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError("실제로 존재하는 날짜를 입력하세요.") from exc
    return value


def validate_recommendation(raw: str | dict[str, Any]) -> dict[str, Any]:
    try:
        payload = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValidationError("추천 응답이 올바른 JSON이 아닙니다.") from exc

    if not isinstance(payload, dict):
        raise ValidationError("추천 응답은 JSON 객체여야 합니다.")
    required = {"recommended_city", "weather", "events", "reason"}
    if set(payload) != required:
        raise ValidationError("추천 응답의 필수 키 구성이 올바르지 않습니다.")

    normalized: dict[str, Any] = {}
    for field in ("recommended_city", "weather", "reason"):
        value = payload[field]
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"추천 응답의 {field} 값이 비어 있거나 문자열이 아닙니다.")
        normalized[field] = value.strip()

    events = payload["events"]
    if not isinstance(events, list) or not 1 <= len(events) <= 3:
        raise ValidationError("events는 1~3개의 문자열을 담은 배열이어야 합니다.")
    if any(not isinstance(event, str) or not event.strip() for event in events):
        raise ValidationError("events의 각 항목은 비어 있지 않은 문자열이어야 합니다.")
    normalized["events"] = [event.strip() for event in events]
    return normalized
