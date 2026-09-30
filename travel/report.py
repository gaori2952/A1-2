import re
from typing import Any
from urllib.parse import urlparse

from travel.prompts import build_report_prompt


REQUIRED_SECTIONS = (
    "추천 지역과 이유",
    "날씨 요약",
    "행사·축제 후보",
    "맛집 리스트",
    "1일 일정 제안",
)


def _escape_markdown(value: object) -> str:
    text = str(value)
    return re.sub(r"([\\`*_{}\[\]()#+.!|>])", r"\\\1", text)


def render_restaurants(restaurants: list[dict[str, Any]]) -> str:
    if not restaurants:
        return "데이터 없음"
    lines: list[str] = []
    for place in restaurants:
        name = _escape_markdown(place.get("name", ""))
        address = _escape_markdown(place.get("address", ""))
        category = _escape_markdown(place.get("category", ""))
        line = f"- **{name}**"
        if address:
            line += f"  \n  주소: {address}"
        if category:
            line += f"  \n  분류: {category}"
        url = place.get("url", "")
        parsed = urlparse(url) if isinstance(url, str) else None
        if parsed and parsed.scheme == "https" and parsed.hostname == "place.map.kakao.com":
            line += f"  \n  링크: [지도에서 보기]({url})"
        lines.append(line)
    return "\n".join(lines)


def _fallback_section(title: str, recommendation: dict[str, Any] | None, restaurants: list[dict[str, Any]]) -> str:
    if title == "추천 지역과 이유":
        if recommendation:
            return f"{recommendation['recommended_city']}를 추천합니다. {recommendation['reason']}"
        return "추천 정보를 확보하지 못했습니다."
    if title == "날씨 요약":
        return recommendation["weather"] + " 실제 예보를 별도로 확인하세요." if recommendation else "계절 날씨 정보를 확보하지 못했습니다."
    if title == "행사·축제 후보":
        if recommendation:
            candidates = "\n".join(f"- {_escape_markdown(item)}" for item in recommendation["events"])
            return candidates + "\n- 방문 전 해당 연도 일정을 확인하세요."
        return "행사 후보를 확보하지 못했습니다."
    if title == "맛집 리스트":
        return render_restaurants(restaurants)
    return "- 오전: 지역의 대표적인 산책로나 문화 공간을 둘러봅니다.\n- 오후: 실내 명소와 주변 거리를 여유롭게 방문합니다.\n- 저녁: 지역 식사 장소를 찾아 하루를 마무리합니다."


def _replace_section(text: str, title: str, content: str) -> str:
    pattern = re.compile(rf"(?ms)^## {re.escape(title)}\s*$.*?(?=^## |\Z)")
    replacement = f"## {title}\n{content.strip()}\n\n"
    if pattern.search(text):
        return pattern.sub(replacement, text, count=1).rstrip()
    return text.rstrip() + f"\n\n{replacement.rstrip()}"


def finalize_report(
    raw: str,
    travel_date: str,
    generated_at: str,
    recommendation: dict[str, Any] | None,
    restaurants: list[dict[str, Any]],
    errors: list[dict[str, object]],
) -> str:
    text = raw.strip()
    if not text.startswith("# 국내 여행 추천 리포트"):
        text = f"# 국내 여행 추천 리포트\n- 여행 날짜: {travel_date}\n- 생성 시각: {generated_at}\n\n{text}"

    for title in REQUIRED_SECTIONS:
        section = re.search(rf"(?ms)^## {re.escape(title)}\s*$.*?(?=^## |\Z)", text)
        if section is None:
            text = _replace_section(text, title, _fallback_section(title, recommendation, restaurants))
        elif not section.group(0).split("\n", 1)[1].strip():
            text = _replace_section(text, title, _fallback_section(title, recommendation, restaurants))

    text = _replace_section(text, "맛집 리스트", render_restaurants(restaurants))
    schedule_pattern = re.compile(r"(?ms)^## 1일 일정 제안\s*$.*?(?=^## |\Z)")
    schedule_match = schedule_pattern.search(text)
    if schedule_match:
        schedule = schedule_match.group(0)
        additions = [
            line for label, line in (
                ("오전", "- 오전: 지역의 산책로 또는 대표 명소를 둘러봅니다."),
                ("오후", "- 오후: 실내 명소와 주변 거리를 여유롭게 방문합니다."),
                ("저녁", "- 저녁: 지역 식사 장소를 찾아 하루를 마무리합니다."),
            )
            if not re.search(rf"(?m)^[-*]?\s*{label}\s*[:：]", schedule)
        ]
        if additions:
            text = _replace_section(text, "1일 일정 제안", schedule.rstrip() + "\n" + "\n".join(additions))

    text = re.sub(r"(?ms)^## errors\s*$.*?(?=^## |\Z)", "", text).rstrip()
    error_lines = [
        f"- {item.get('stage', 'unknown')} / {item.get('code', 'ERROR')}: {item.get('message', '')}"
        for item in errors
    ]
    error_content = "\n".join(error_lines) if error_lines else "없음"
    return text + f"\n\n## errors\n{error_content}\n"


def build_fallback_report(
    travel_date: str,
    generated_at: str,
    recommendation: dict[str, Any] | None,
    restaurants: list[dict[str, Any]],
    errors: list[dict[str, object]],
) -> str:
    return finalize_report("", travel_date, generated_at, recommendation, restaurants, errors)


def make_report_prompt(travel_date: str, recommendation: dict[str, Any], restaurants: list[dict[str, Any]]) -> str:
    return build_report_prompt(travel_date, recommendation, restaurants)
