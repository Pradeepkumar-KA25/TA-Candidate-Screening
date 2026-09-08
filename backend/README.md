# Backend (FastAPI)

This folder contains the backend service for the Talent Acquisition platform.

## Suggested stack
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL

## Authentication slice
- `POST /api/v1/auth/login` authenticates recruiters and returns a JWT access token plus profile data.
- `POST /api/v1/auth/logout` is a protected endpoint for Recruiter/Admin roles and acknowledges stateless JWT logout.
- Protected routes use a shared bearer-token dependency that validates JWTs and resolves the current recruiter context.
- Alembic migrations live under `alembic/` and are configured through `alembic.ini`.

## Zoho integration status slice
- `GET /api/v1/integrations/zoho/status` returns Zoho Recruit connection state, access level, sync type, and timestamps.
- Integration token metadata is stored in `integration_settings` and encrypted at rest using `integration_encryption_key`.

## Quick start
1. Create and activate a virtual environment.
2. Install dependencies:
   pip install -r requirements.txt
3. Run the app:
   uvicorn app.main:app --reload

To apply the database migration locally:

1. Set `DATABASE_URL` if you want to target a database other than the default.
2. Run `alembic -c alembic.ini upgrade head` from the `backend/` folder.

## Project layout
- `app/api` - API routers
- `app/core` - settings and shared core utilities
- `app/services` - domain/business logic
- `app/repositories` - data access layer
- `app/integrations` - Zoho and other external adapters
- `app/background` - background task handlers
- `app/schemas` - Pydantic request/response models
- `tests` - backend tests
