import sys

from travel.cli import parse_args
from travel.config import ConfigError, load_settings
from travel.pipeline import run_pipeline


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        settings = load_settings()
    except ConfigError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    return run_pipeline(args.travel_date, settings)


if __name__ == "__main__":
    raise SystemExit(main())
