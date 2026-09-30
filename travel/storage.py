import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from travel.errors import TravelError


SEOUL = timezone(timedelta(hours=9))
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def current_timestamp() -> datetime:
    return datetime.now(SEOUL)


def make_result_paths(travel_date: str, now: datetime | None = None) -> tuple[Path, Path]:
    timestamp = (now or current_timestamp()).strftime("%Y%m%d_%H%M%S_%f")
    results_dir = PROJECT_ROOT / "results"
    stem = f"{timestamp}_{travel_date}"
    json_path = results_dir / f"{stem}.json"
    markdown_path = results_dir / f"{stem}.md"
    suffix = 1
    while json_path.exists() or markdown_path.exists():
        json_path = results_dir / f"{stem}_{suffix:02d}.json"
        markdown_path = results_dir / f"{stem}_{suffix:02d}.md"
        suffix += 1
    return json_path, markdown_path


def save_results(data: dict[str, Any], report: str, travel_date: str) -> tuple[Path, Path]:
    json_path, markdown_path = make_result_paths(travel_date)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_temp = json_path.with_suffix(json_path.suffix + ".tmp")
    markdown_temp = markdown_path.with_suffix(markdown_path.suffix + ".tmp")
    try:
        json_temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        markdown_temp.write_text(report, encoding="utf-8")
        os.replace(json_temp, json_path)
        os.replace(markdown_temp, markdown_path)
    except OSError as exc:
        for temporary in (json_temp, markdown_temp):
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
        raise TravelError("storage", "SAVE_FAILED", "결과 파일을 저장하지 못했습니다. 경로와 쓰기 권한을 확인하세요.") from exc
    return json_path, markdown_path
