import unittest
from unittest.mock import Mock, patch

from travel.config import Settings
from travel.places import search_restaurants


class PlaceSearchTests(unittest.TestCase):
    @patch("travel.places.requests.get")
    def test_uses_recommended_city_and_normalizes_coordinates(self, get):
        response = Mock(status_code=200)
        response.json.return_value = {"documents": [{
            "id": "42",
            "place_name": "식당",
            "road_address_name": "강원 강릉시",
            "category_name": "음식점 > 한식",
            "place_url": "https://place.map.kakao.com/42",
            "x": "128.90",
            "y": "37.75",
        }]}
        get.return_value = response
        places, status, errors = search_restaurants("강릉", Settings("g", "m", "k"))
        self.assertEqual(status, "success")
        self.assertEqual(places[0]["x"], 128.9)
        self.assertEqual(places[0]["y"], 37.75)
        self.assertEqual(errors, [])
        self.assertEqual(get.call_args.kwargs["params"]["query"], "강릉 맛집")
        self.assertEqual(get.call_args.kwargs["params"]["size"], 5)

    @patch("travel.places.requests.get")
    def test_zero_results_are_empty_not_failed(self, get):
        response = Mock(status_code=200)
        response.json.return_value = {"documents": []}
        get.return_value = response
        self.assertEqual(search_restaurants("강릉", Settings("g", "m", "k")), ([], "empty", []))

    @patch("travel.places.requests.get")
    def test_missing_coordinates_are_null_and_recorded_as_warning(self, get):
        response = Mock(status_code=200)
        response.json.return_value = {"documents": [{
            "id": "42",
            "place_name": "식당",
            "address_name": "강원 강릉시",
        }]}
        get.return_value = response
        places, status, warnings = search_restaurants("강릉", Settings("g", "m", "k"))
        self.assertEqual(status, "success")
        self.assertIsNone(places[0]["x"])
        self.assertIsNone(places[0]["y"])
        self.assertEqual(warnings[0]["code"], "INVALID_PLACE_DATA")


if __name__ == "__main__":
    unittest.main()
