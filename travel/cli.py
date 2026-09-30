import argparse

from travel.validation import ValidationError, validate_date


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="국내 여행 지역과 맛집을 추천합니다.")
    parser.add_argument("-date", "--date", required=True, dest="travel_date", help="여행 날짜 (YYYY-MM-DD)")
    args = parser.parse_args(argv)
    try:
        args.travel_date = validate_date(args.travel_date)
    except ValidationError as exc:
        parser.error(str(exc))
    return args
