from typing import Any

from pydantic import BaseModel


class ApiError(BaseModel):
    code: str
    message: str
    correlation_id: str
    fields: dict[str, Any] | None = None
