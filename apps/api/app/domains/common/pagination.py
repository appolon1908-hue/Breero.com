from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PageRequest:
    limit: int = 50
    cursor: str | None = None

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 200:
            raise ValueError("limit must be between 1 and 200")
        if self.cursor is not None and not self.cursor.strip():
            raise ValueError("cursor must be non-empty when supplied")
