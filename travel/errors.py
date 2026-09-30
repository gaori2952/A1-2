from dataclasses import asdict, dataclass


@dataclass
class TravelError(Exception):
    stage: str
    code: str
    message: str

    def __str__(self) -> str:
        return self.message

    def as_record(self, attempt: int = 1, recovered: bool = False) -> dict[str, object]:
        return {
            "stage": self.stage,
            "code": self.code,
            "message": self.message,
            "attempt": attempt,
            "recovered": recovered,
        }


def validation_error(message: str, attempt: int, recovered: bool) -> dict[str, object]:
    return {
        "stage": "recommendation",
        "code": "INVALID_OUTPUT",
        "message": message,
        "attempt": attempt,
        "recovered": recovered,
    }
