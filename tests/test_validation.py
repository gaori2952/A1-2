import unittest

from travel.validation import ValidationError, validate_date, validate_recommendation


class DateValidationTests(unittest.TestCase):
    def test_accepts_valid_leap_day(self):
        self.assertEqual(validate_date("2028-02-29"), "2028-02-29")

    def test_rejects_wrong_format_and_impossible_date(self):
        for value in ("2026-9-1", "2026/09/01", "2026-02-30"):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                validate_date(value)


class RecommendationValidationTests(unittest.TestCase):
    def test_trims_valid_values(self):
        actual = validate_recommendation({
            "recommended_city": " 강릉 ",
            "weather": " 선선한 편입니다. ",
            "events": [" 일정 확인이 필요한 행사 후보 "],
            "reason": " 바다와 도심을 함께 둘러보기 좋습니다. ",
        })
        self.assertEqual(actual["recommended_city"], "강릉")
        self.assertEqual(actual["events"], ["일정 확인이 필요한 행사 후보"])

    def test_rejects_valid_json_with_wrong_events_type(self):
        with self.assertRaises(ValidationError):
            validate_recommendation(
                '{"recommended_city":"강릉","weather":"선선함",'
                '"events":"행사 후보","reason":"추천 이유"}'
            )

    def test_rejects_missing_or_extra_keys(self):
        payload = {
            "recommended_city": "강릉",
            "weather": "선선함",
            "events": ["행사 후보"],
            "reason": "추천 이유",
            "extra": "not allowed",
        }
        with self.assertRaises(ValidationError):
            validate_recommendation(payload)


if __name__ == "__main__":
    unittest.main()
