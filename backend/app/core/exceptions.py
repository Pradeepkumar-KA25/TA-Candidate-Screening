from __future__ import annotations

from datetime import UTC, datetime
import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas.errors import ErrorResponse
from app.services.auth_service import AuthError
from app.services.candidate_service import CandidateError
from app.services.integration_service import IntegrationError
from app.services.job_description_service import JobDescriptionError
from app.services.ranking_criteria_service import RankingCriteriaError
from app.services.ranking_service import RankingError
from app.services.duplicate_service import DuplicateError
from app.services.saved_filter_service import SavedFilterError
from app.services.sync_service import SyncError


logger = logging.getLogger(__name__)


def _build_error_response(
    *,
    code: str,
    message: str,
    path: str,
    details: list[dict[str, str]] | None = None,
) -> ErrorResponse:
    return ErrorResponse(
        code=code,
        message=message,
        path=path,
        timestamp=datetime.now(UTC),
        details=details,
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AuthError)
    async def auth_error_handler(request: Request, exc: AuthError) -> JSONResponse:
        payload = _build_error_response(
            code="AUTH_ERROR",
            message=exc.detail,
            path=str(request.url.path),
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))

    @app.exception_handler(SyncError)
    async def sync_error_handler(request: Request, exc: SyncError) -> JSONResponse:
        payload = _build_error_response(
            code=exc.code,
            message=exc.detail,
            path=str(request.url.path),
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))

    @app.exception_handler(CandidateError)
    async def candidate_error_handler(request: Request, exc: CandidateError) -> JSONResponse:
        payload = _build_error_response(
            code=exc.code,
            message=exc.detail,
            path=str(request.url.path),
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))

    @app.exception_handler(IntegrationError)
    async def integration_error_handler(request: Request, exc: IntegrationError) -> JSONResponse:
        payload = _build_error_response(
            code=exc.code,
            message=exc.detail,
            path=str(request.url.path),
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))

    @app.exception_handler(SavedFilterError)
    async def saved_filter_error_handler(request: Request, exc: SavedFilterError) -> JSONResponse:
        payload = _build_error_response(
            code=exc.code,
            message=exc.detail,
            path=str(request.url.path),
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))

    @app.exception_handler(JobDescriptionError)
    async def job_description_error_handler(request: Request, exc: JobDescriptionError) -> JSONResponse:
        payload = _build_error_response(
            code=exc.code,
            message=exc.detail,
            path=str(request.url.path),
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))

    @app.exception_handler(RankingCriteriaError)
    async def ranking_criteria_error_handler(request: Request, exc: RankingCriteriaError) -> JSONResponse:
        payload = _build_error_response(
            code=exc.code,
            message=exc.detail,
            path=str(request.url.path),
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))

    @app.exception_handler(RankingError)
    async def ranking_error_handler(request: Request, exc: RankingError) -> JSONResponse:
        payload = _build_error_response(
            code=exc.code,
            message=exc.detail,
            path=str(request.url.path),
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))

    @app.exception_handler(DuplicateError)
    async def duplicate_error_handler(request: Request, exc: DuplicateError) -> JSONResponse:
        payload = _build_error_response(
            code=exc.code,
            message=exc.detail,
            path=str(request.url.path),
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {
                "field": ".".join(str(item) for item in error.get("loc", [])),
                "message": error.get("msg", "Invalid value"),
            }
            for error in exc.errors()
        ]
        payload = _build_error_response(
            code="VALIDATION_ERROR",
            message="Malformed request payload",
            path=str(request.url.path),
            details=details,
        )
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=payload.model_dump(mode="json"))

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled server error", exc_info=exc)
        payload = _build_error_response(
            code="INTERNAL_SERVER_ERROR",
            message="Internal server error",
            path=str(request.url.path),
        )
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload.model_dump(mode="json"))
