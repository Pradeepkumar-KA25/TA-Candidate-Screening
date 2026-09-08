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
