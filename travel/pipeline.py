from typing import Any

from travel.config import Settings
from travel.errors import TravelError
from travel.llm import generate_text, request_recommendation
from travel.places import search_restaurants
from travel.report import build_fallback_report, finalize_report, make_report_prompt
from travel.storage import current_timestamp, save_results


def run_pipeline(travel_date: str, settings: Settings) -> int:
    errors: list[dict[str, object]] = []
    recommendation: dict[str, Any] | None = None
    restaurants: list[dict[str, object]] = []
    search_status = "empty"
    report_status = "pending"
    timestamp = current_timestamp().isoformat(timespec="seconds")

    print(f"[1/5] 입력 및 설정 확인 완료: 여행 날짜 {travel_date}")
    print("[2/5] 국내 여행 지역 추천 요청 중")
    try:
        recommendation = request_recommendation(settings, travel_date, errors)
    except TravelError as exc:
        errors.append(exc.as_record(attempt=2, recovered=False))
        report_status = "fallback"
        print(f"[ERROR] {exc.message}")

    if recommendation is not None:
        print("[3/5] 추천 지역 음식점 검색 중")
        try:
            restaurants, search_status, place_warnings = search_restaurants(
                recommendation["recommended_city"], settings
            )
            errors.extend(place_warnings)
            if search_status == "empty":
                print("[WARN] 검색된 맛집이 없습니다. 빈 목록으로 계속합니다.")
        except TravelError as exc:
            search_status = "failed"
            errors.append(exc.as_record(recovered=True))
            print(f"[WARN] {exc.message} 맛집 데이터 없이 계속합니다.")

        print("[4/5] 최종 여행 리포트 생성 중")
        try:
            prompt = make_report_prompt(travel_date, recommendation, restaurants)
            raw_report = generate_text(prompt, settings)
            report = finalize_report(raw_report, travel_date, timestamp, recommendation, restaurants, errors)
            report_status = "generated"
        except TravelError as exc:
            errors.append(exc.as_record(recovered=True))
            report_status = "fallback"
            report = build_fallback_report(travel_date, timestamp, recommendation, restaurants, errors)
            print(f"[WARN] 최종 LLM 실패, 대체 리포트를 저장합니다: {exc.message}")
    else:
        report = build_fallback_report(travel_date, timestamp, None, restaurants, errors)

    result = {
        "schema_version": "1.0",
        "travel_date": travel_date,
        "executed_at": timestamp,
        "providers": {"llm": "gemini", "places": "kakao"},
        "recommendation": recommendation,
        "restaurants": restaurants,
        "search_status": search_status,
        "report_status": report_status,
        "errors": errors,
    }
    print("[5/5] 결과 저장 중")
    try:
        json_path, markdown_path = save_results(result, report, travel_date)
    except TravelError as exc:
        print(f"[ERROR] {exc.message}")
        return 1
    print("[5/5] 결과 저장 완료")
    print(f"JSON: {json_path}")
    print(f"REPORT: {markdown_path}")
    return 0 if recommendation is not None and report_status == "generated" else 1
