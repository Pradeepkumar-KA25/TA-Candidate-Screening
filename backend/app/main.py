import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        redirect_slashes=False,  # Disable automatic trailing slash redirects (307 errors)
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
