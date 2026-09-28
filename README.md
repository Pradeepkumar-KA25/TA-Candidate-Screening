# Talent Acquisition Candidate Screening

Talent Acquisition Candidate Screening is a full-stack recruiter workflow application. It supports login, Zoho Recruit synchronization, candidate search and filtering, duplicate review, ranking, shortlists, Excel export, and AI-assisted resume generation.

## Technology

- Frontend: Angular and TypeScript
- Backend: FastAPI, SQLAlchemy, and Alembic
- Database: PostgreSQL

## Requirements

- Python 3.11 or later
- Node.js 20 or later
- PostgreSQL running locally

## First-Time Setup

1. Create a PostgreSQL database named `talent_acquisition`, or update `DATABASE_URL` in `backend/.env`.
2. Run `setup.bat` from the project root.
3. Review `backend/.env` and configure database, JWT, Zoho, and optional AI provider values as needed.

`setup.bat` creates the Python virtual environment, installs backend and frontend dependencies, and applies database migrations.

## Run the Application

1. Ensure PostgreSQL is running.
2. Run `run.bat` from the project root.
3. Open `http://localhost:4200` in your browser.

The backend runs at `http://127.0.0.1:8000`. API documentation is available at `http://127.0.0.1:8000/docs`.

## How to Use

1. Sign in with a recruiter account.
2. Use the dashboard to review recruitment activity.
3. Sync candidates from Zoho Recruit when integration credentials are configured.
4. Search, filter, rank, review duplicates, and create shortlists.
5. Open Resume Generator to upload a resume, review the extracted information, select a template, preview it, and download the result.

## Project Structure

- `backend/`: FastAPI application, database migrations, environment settings, and runtime upload storage.
- `frontend/`: Angular web application.
- `setup.bat`: Installs dependencies and applies migrations.
- `run.bat`: Starts the backend and frontend development servers.

## Important Notes

- Keep `backend/.env` private. It contains local configuration and credentials.
- Back up PostgreSQL regularly. It stores recruiters, candidates, resume records, templates, and other application data.
- `backend/uploads/` and `backend/temp/` contain generated runtime files and are excluded from Git.

## Configuration

Local backend runs read `backend/.env`. Docker Compose reads the root `.env`; use `.env.example` as the variable list. Environment-specific values and secrets are not stored in application source.

Required backend settings are `DATABASE_URL`, `FRONTEND_CORS_ORIGIN`, `JWT_SECRET_KEY`, and `INTEGRATION_ENCRYPTION_KEY`. Generate the encryption key with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.

The frontend always calls `/api/v1`. Angular's development proxy forwards that path locally, while the frontend Nginx container uses `BACKEND_URL` at runtime.

## Azure Deployment

- Store secrets in Azure Key Vault and expose them through Azure App Settings or Container Apps secrets.
- Set `APP_ENV=production`, `DEBUG=false`, `DATABASE_URL`, `FRONTEND_CORS_ORIGIN`, and the required secrets.
- Set `STORAGE_BACKEND=azure_blob`, `AZURE_STORAGE_ACCOUNT_URL`, and `AZURE_STORAGE_CONTAINER`.
- Enable a managed identity and grant it `Storage Blob Data Contributor` on the storage account or container. Create the blob container before starting the app.
- Set frontend `BACKEND_URL` to the private or public backend origin and `PORT` to the frontend container target port.
- `INITIAL_ADMIN_EMAIL` and `INITIAL_ADMIN_PASSWORD` are optional one-time bootstrap settings. Remove them after the account is created.
- Ollama is optional at runtime because resume extraction falls back to the deterministic parser, but it is required for AI extraction, sector classification, and AI template-spec generation.

## Ollama

Ollama runs as a separate service. Configure `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_SECTOR_MODEL`, and the comma-separated `OLLAMA_MODELS` list in the backend environment. Resume upload uses Ollama for structured extraction and falls back to the deterministic parser if Ollama is unavailable. Company-sector enrichment uses PostgreSQL caching. AI-generated template specifications are validated before previewing or rendering.

For Azure, keep Ollama private and set `OLLAMA_BASE_URL` to its internal service URL. Persist the Ollama model directory in the Ollama deployment; do not package models into the frontend or backend images.

Resume upload saves an immediate deterministic baseline, persists the source file, and starts complete Ollama extraction in the background. The review page polls PostgreSQL-backed status and displays progress until extraction completes. Long experience sections use overlapping chunks, tolerate individual chunk failures, and merge/deduplicate jobs and projects. Pending jobs resume after backend restart. Source files are removed after successful completion.
