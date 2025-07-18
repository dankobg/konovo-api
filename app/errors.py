from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class KonovoError(Exception):
    def __init__(self, code: str, message: str, detail: str):
        super().__init__()
        self.code = code
        self.message = message
        self.detail = detail


class UnavailableError(KonovoError):
    """Result is not available right now"""

    pass


class TimeOutError(KonovoError):
    """Operation was timed out"""

    pass


class NotFoundError(KonovoError):
    """Item not found"""

    pass


class AuthenticationError(KonovoError):
    """Not authenticated"""

    pass


class AuthorizationError(KonovoError):
    """Invalid permissions"""

    pass


async def global_exception_handler(request: Request, exc: Exception):
    # log error here etc...

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": "internal_error",
            "message": "An unexpected error occurred",
            "detail": "Please contact our support at ...",
        },
    )


def create_exception_handler(status_code: int):
    out: dict[str, Any] = {
        "code": "unknown",
        "message": "Unexpected error",
    }

    async def exception_handler(_: Request, exc: Exception) -> JSONResponse:
        if isinstance(exc, KonovoError):
            if exc.code:
                out["code"] = exc.code
            if exc.message:
                out["message"] = exc.message
            if exc.detail:
                out["detail"] = str(exc.detail)

        if isinstance(exc, RequestValidationError):
            out["code"] = "validation_error"
            out["message"] = f"Invalid request, got {len(exc.errors())} error(s)"
            out["detail"] = exc.errors()

        # log error here etc...
        return JSONResponse(status_code=status_code, content={**out})

    return exception_handler


def register_app_exception_handlers(app: FastAPI):
    app.add_exception_handler(
        exc_class_or_status_code=Exception, handler=global_exception_handler
    )

    app.add_exception_handler(
        exc_class_or_status_code=RequestValidationError,
        handler=create_exception_handler(status.HTTP_422_UNPROCESSABLE_ENTITY),
    )

    app.add_exception_handler(
        exc_class_or_status_code=UnavailableError,
        handler=create_exception_handler(status.HTTP_503_SERVICE_UNAVAILABLE),
    )

    app.add_exception_handler(
        exc_class_or_status_code=TimeOutError,
        handler=create_exception_handler(status.HTTP_408_REQUEST_TIMEOUT),
    )

    app.add_exception_handler(
        exc_class_or_status_code=NotFoundError,
        handler=create_exception_handler(status.HTTP_404_NOT_FOUND),
    )

    app.add_exception_handler(
        exc_class_or_status_code=AuthenticationError,
        handler=create_exception_handler(status.HTTP_401_UNAUTHORIZED),
    )

    app.add_exception_handler(
        exc_class_or_status_code=AuthorizationError,
        handler=create_exception_handler(status.HTTP_403_FORBIDDEN),
    )
