from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class DomainError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def install_error_handlers(app: FastAPI) -> None:
    def payload(code: str, message: str, request: Request) -> dict:
        return {
            "data": None,
            "meta": {
                "request_id": getattr(request.state, "request_id", None),
                "correlation_id": getattr(request.state, "correlation_id", None),
            },
            "error": {"code": code, "message": message},
        }

    @app.exception_handler(DomainError)
    async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=payload(exc.code, exc.message, _),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, _: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=payload("VALIDATION_ERROR", "The request contains invalid data.", request),
        )

    @app.exception_handler(HTTPException)
    async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
        code = {
            401: "AUTH_REQUIRED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            409: "CONFLICT",
            429: "RATE_LIMITED",
        }.get(exc.status_code, "VALIDATION_ERROR" if exc.status_code == 400 else "REQUEST_FAILED")
        message = exc.detail if isinstance(exc.detail, str) else "The request could not be completed."
        return JSONResponse(
            status_code=exc.status_code,
            content=payload(code, message, request),
            headers=exc.headers,
        )
