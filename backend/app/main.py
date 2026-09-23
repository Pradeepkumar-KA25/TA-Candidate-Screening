import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.api.router import api_router
from app.core.config import settings
from app.core.database import get_db_session
from app.core.dependencies import get_sync_service
from app.core.exceptions import register_exception_handlers

logger = logging.getLogger(__name__)


# Background task for auto-sync
_auto_sync_task = None


async def auto_sync_background_worker():
    """Periodically check and run auto-sync if enabled."""
    from app.core.database import get_session_factory
    from app.repositories.sync_log_repository import SyncLogRepository
    from app.repositories.candidate_repository import CandidateRepository
    from app.repositories.integration_settings_repository import IntegrationSettingsRepository
    from app.repositories.activity_log_repository import ActivityLogRepository
    from app.repositories.duplicate_review_repository import DuplicateReviewRepository
    from app.repositories.normalization_rule_repository import NormalizationRuleRepository
    from app.services.sync_service import SyncService
    from app.services.duplicate_detection_service import DuplicateDetectionService
    from app.services.normalization_service import NormalizationService
    from app.services.resume_fetch_service import ResumeFetchService
    from app.integrations.zoho_oauth import ZohoOAuthClient
    from app.integrations.zoho_recruit import ZohoRecruitClient
    
    logger.info("Auto-sync background worker started")
    
    while True:
        try:
            # Check every minute if auto-sync should run
            await asyncio.sleep(60)
            
            # Get a fresh database session for this check
            session_factory = get_session_factory()
            session = session_factory()
            try:
                # Initialize repositories
                sync_log_repo = SyncLogRepository(session)
                candidate_repo = CandidateRepository(session)
                integration_repo = IntegrationSettingsRepository(session)
                activity_log_repo = ActivityLogRepository(session)
                duplicate_review_repo = DuplicateReviewRepository(session)
                normalization_rule_repo = NormalizationRuleRepository(session)
                
                # Initialize services
                zoho_oauth_client = ZohoOAuthClient()
                zoho_recruit_client = ZohoRecruitClient()
                
                duplicate_detection_service = DuplicateDetectionService(
                    candidate_repo, duplicate_review_repo
                )
                normalization_service = NormalizationService(normalization_rule_repo)
                resume_fetch_service = ResumeFetchService(
                    candidate_repository=candidate_repo,
                    zoho_recruit_client=zoho_recruit_client,
                )
                
                sync_service = SyncService(
                    sync_log_repository=sync_log_repo,
                    candidate_repository=candidate_repo,
                    integration_repository=integration_repo,
                    activity_log_repository=activity_log_repo,
                    duplicate_detection_service=duplicate_detection_service,
                    normalization_service=normalization_service,
                    zoho_oauth_client=zoho_oauth_client,
                    zoho_recruit_client=zoho_recruit_client,
                    resume_fetch_service=resume_fetch_service,
                )
                
                # Try to run auto-sync
                sync_id = sync_service.run_auto_sync()
                if sync_id:
                    logger.info(f"Auto-sync triggered (sync_id={sync_id})")
                    try:
                        # Run the sync synchronously
                        sync_service.run_sync(sync_id)
                        logger.info(f"Auto-sync completed successfully (sync_id={sync_id})")
                    except Exception as sync_error:
                        logger.error(f"Error during sync execution (sync_id={sync_id}): {str(sync_error)}", exc_info=True)
                else:
                    logger.debug("Auto-sync not triggered (interval not met or disabled)")
            except Exception as e:
                logger.error(f"Error in auto-sync check: {str(e)}", exc_info=True)
            finally:
                session.close()
                    
        except asyncio.CancelledError:
            logger.info("Auto-sync background worker cancelled")
            break
        except Exception as e:
            logger.error(f"Unexpected error in auto-sync worker: {str(e)}", exc_info=True)
            # Wait a bit before retrying on unexpected errors
            try:
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                logger.info("Auto-sync background worker cancelled during error recovery")
                break


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup and shutdown."""
    global _auto_sync_task
    
    # Startup
    logger.info("Application startup")
    _auto_sync_task = asyncio.create_task(auto_sync_background_worker())
    
    yield
    
    # Shutdown
    logger.info("Application shutdown")
    if _auto_sync_task:
        _auto_sync_task.cancel()
        try:
            await _auto_sync_task
        except asyncio.CancelledError:
            pass


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        redirect_slashes=False,  # Disable automatic trailing slash redirects (307 errors)
        lifespan=lifespan,  # Add lifespan context manager
    )

    # Custom middleware to ensure CORS headers are ALWAYS applied
    @app.middleware("http")
    async def add_cors_headers(request: Request, call_next):
        cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
            if request.headers.get("origin") in cors_origins:
                response.headers["Access-Control-Allow-Origin"] = request.headers.get("origin")
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
                response.headers["Access-Control-Allow-Headers"] = request.headers.get("access-control-request-headers", "*")
                response.headers["Access-Control-Allow-Credentials"] = "true"
            return response
        
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"Exception in route handler: {str(e)}", exc_info=True)
            response = Response(content='{"detail": "Internal Server Error"}', status_code=500, media_type="application/json")
        
        # Add CORS headers to response
        if request.headers.get("origin") in cors_origins:
            response.headers["Access-Control-Allow-Origin"] = request.headers.get("origin")
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Expose-Headers"] = "Content-Disposition"
        
        return response

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    # Register exception handlers
    register_exception_handlers(app)
    
    # Include API router
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    # Add CORS middleware LAST (it will execute FIRST due to middleware stack)
    cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["Content-Disposition"],
        )

    return app


app = create_app()
