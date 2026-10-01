import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from travel.config import Settings
from travel.errors import TravelError
from travel.llm import request_recommendation
from travel.pipeline import run_pipeline
from travel.report import finalize_report


SETTINGS = Settings("test-gemini-key", "test-model", "test-kakao-key")
RECOMMENDATION = {
    "recommended_city": "강릉",
    "weather": "가을에는 선선할 수 있습니다.",
    "events": ["일정 확인이 필요한 지역 행사 후보"],
    "reason": "바다와 도심을 함께 즐기기 좋습니다. 하루 일정으로 구성하기 편합니다.",
}


class RecommendationRetryTests(unittest.TestCase):
    @patch("travel.llm.generate_text", side_effect=["not json", RECOMMENDATION])
    def test_invalid_json_retries_once_then_returns_valid_data(self, generate):
        errors = []
        result = request_recommendation(SETTINGS, "2026-10-15", errors)
        self.assertEqual(result["recommended_city"], "강릉")
        self.assertEqual(generate.call_count, 2)
        self.assertEqual(errors[0]["attempt"], 1)
        self.assertTrue(errors[0]["recovered"])
        self.assertIn("검증에 실패", generate.call_args_list[1].args[0])


class PipelineTests(unittest.TestCase):
    @patch("travel.pipeline.save_results", return_value=(Path("result.json"), Path("result.md")))
    @patch("travel.pipeline.generate_text", return_value="## 1일 일정 제안\n- 오전: 해변 산책")
    @patch("travel.pipeline.search_restaurants", side_effect=TravelError("places", "HTTP_401", "장소 API 인증에 실패했습니다."))
    @patch("travel.pipeline.request_recommendation", return_value=RECOMMENDATION)
    def test_place_failure_continues_to_final_llm_and_saves_error(
        self, request_recommendation_mock, search_mock, generate_mock, save_mock
    ):
        code = run_pipeline("2026-10-15", SETTINGS)
        self.assertEqual(code, 0)
        search_mock.assert_called_once_with("강릉", SETTINGS)
        final_prompt = generate_mock.call_args.args[0]
        self.assertIn("맛집 목록: []", final_prompt)
        saved = save_mock.call_args.args[0]
        report = save_mock.call_args.args[1]
        self.assertEqual(saved["search_status"], "failed")
        self.assertEqual(saved["errors"][0]["code"], "HTTP_401")
        self.assertIn("데이터 없음", report)
        self.assertIn("## errors", report)

    def test_finalizer_replaces_unverified_restaurant_and_fills_schedule(self):
        report = finalize_report(
            "## 맛집 리스트\n- 존재하지 않는 식당\n## 1일 일정 제안\n- 오전: 산책",
            "2026-10-15",
            "2026-09-30T12:00:00+09:00",
            RECOMMENDATION,
            [],
            [],
        )
        self.assertNotIn("존재하지 않는 식당", report)
        self.assertIn("데이터 없음", report)
        self.assertRegex(report, r"(?m)^- 오전:")
        self.assertRegex(report, r"(?m)^- 오후:")
        self.assertRegex(report, r"(?m)^- 저녁:")
        self.assertEqual(report.count("- 오전:"), 1)
        self.assertEqual(report.count("- 오후:"), 1)
        self.assertEqual(report.count("- 저녁:"), 1)

    def test_finalizer_fills_empty_required_section(self):
        report = finalize_report(
            "## 날씨 요약\n\n## 1일 일정 제안\n- 오전: 산책\n- 오후: 관람\n- 저녁: 식사",
            "2026-10-15",
            "2026-09-30T12:00:00+09:00",
            RECOMMENDATION,
            [],
            [],
        )
        weather = report.split("## 날씨 요약\n", 1)[1].split("\n## ", 1)[0]
        self.assertIn("선선", weather)

    def test_finalizer_preserves_bold_schedule_without_duplicates_and_renders_kakao_link(self):
        restaurants = [{
            "name": "식당",
            "address": "경주 주소",
            "category": "음식점",
            "url": "http://place.map.kakao.com/123",
        }]
        report = finalize_report(
            "## 1일 일정 제안\n## 1일 일정 제안\n"
            "*   **오전:** 산책\n*   **오후:** 관람\n*   **저녁:** 식사",
            "2026-10-15",
            "2026-10-01T12:00:00+09:00",
            RECOMMENDATION,
            restaurants,
            [],
        )
        self.assertEqual(report.count("## 1일 일정 제안"), 1)
        self.assertEqual(report.count("**오전:**"), 1)
        self.assertEqual(report.count("**오후:**"), 1)
        self.assertEqual(report.count("**저녁:**"), 1)
        self.assertIn("http://place.map.kakao.com/123", report)


if __name__ == "__main__":
    unittest.main()
