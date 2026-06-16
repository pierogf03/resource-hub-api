from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, errors: list | None = None):
        self.message = message
        self.status_code = status_code
        self.errors = errors or []


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "message": exc.message, "errors": exc.errors},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = []
        for error in exc.errors():
            field = ".".join(str(part) for part in error.get("loc", []) if part != "body")
            errors.append({"field": field or "body", "message": error.get("msg", "Validation error")})
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"success": False, "message": "Validation error", "errors": errors},
        )
