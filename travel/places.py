import math

import requests
from travel.api_trace import exchange

from travel.config import Settings
from travel.errors import TravelError


KAKAO_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"


def _coordinate(value: object, minimum: float, maximum: float) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or not minimum <= number <= maximum:
        return None
    return number


def normalize_place(item: object) -> tuple[dict[str, object] | None, bool]:
    if not isinstance(item, dict):
        return None, True
    name = item.get("place_name")
    address = item.get("road_address_name") or item.get("address_name")
    if not isinstance(name, str) or not name.strip() or not isinstance(address, str) or not address.strip():
        return None, True

    longitude = _coordinate(item.get("x"), -180, 180)
    latitude = _coordinate(item.get("y"), -90, 90)
    warning = longitude is None or latitude is None
    return {
        "id": str(item["id"]) if item.get("id") is not None else None,
        "name": name.strip(),
        "address": address.strip(),
        "category": item.get("category_name", "") if isinstance(item.get("category_name", ""), str) else "",
        "url": item.get("place_url", "") if isinstance(item.get("place_url", ""), str) else "",
        "x": longitude,
        "y": latitude,
    }, warning


def search_restaurants(city: str, settings: Settings) -> tuple[list[dict[str, object]], str, list[dict[str, object]]]:
    try:
        response = exchange(
            requests.get,
            KAKAO_URL,
            provider="kakao", stage="restaurant_search",
            secrets=(settings.gemini_api_key, settings.kakao_rest_api_key),
            headers={"Authorization": f"KakaoAK {settings.kakao_rest_api_key}"},
            params={"query": f"{city} 맛집", "category_group_code": "FD6", "size": 5},
            timeout=(5, 15),
        )
    except requests.Timeout as exc:
        raise TravelError("places", "TIMEOUT", "장소 API 요청 시간이 초과되었습니다.") from exc
    except requests.RequestException as exc:
        raise TravelError("places", "NETWORK_ERROR", "장소 API에 연결할 수 없습니다.") from exc

    if response.status_code in (401, 403):
        raise TravelError("places", f"HTTP_{response.status_code}", "장소 API 인증에 실패했습니다. REST API 키와 이용 설정을 확인하세요.")
    if response.status_code == 429:
        raise TravelError("places", "HTTP_429", "장소 API 사용 한도에 도달했습니다.")
    if response.status_code >= 400:
        raise TravelError("places", f"HTTP_{response.status_code}", "장소 API 요청이 실패했습니다.")

    try:
        payload = response.json()
    except (ValueError, requests.JSONDecodeError) as exc:
        raise TravelError("places", "INVALID_RESPONSE", "장소 API 응답을 해석할 수 없습니다.") from exc
    documents = payload.get("documents") if isinstance(payload, dict) else None
    if not isinstance(documents, list):
        raise TravelError("places", "INVALID_RESPONSE", "장소 API 응답 형식이 올바르지 않습니다.")

    restaurants: list[dict[str, object]] = []
    warnings: list[dict[str, object]] = []
    seen: set[str] = set()
    for item in documents:
        place, had_warning = normalize_place(item)
        if had_warning:
            warnings.append({
                "stage": "places",
                "code": "INVALID_PLACE_DATA",
                "message": "일부 장소 데이터가 누락되거나 좌표를 해석할 수 없어 제외 또는 null 처리했습니다.",
                "attempt": 1,
                "recovered": True,
            })
        if place is None:
            continue
        identity = place["id"] or f"{place['name']}|{place['address']}"
        if identity in seen:
            continue
        seen.add(identity)
        restaurants.append(place)
        if len(restaurants) == 5:
            break

    return restaurants, "success" if restaurants else "empty", warnings
