# Backend Dockerfile for FastAPI application
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory for resumes
RUN mkdir -p uploads/resumes

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import os, httpx; httpx.get('http://127.0.0.1:{}/health'.format(os.getenv('PORT', '8000')), timeout=5)" || exit 1

# Expose port 8000
EXPOSE 8000

# Run migrations, provision an optional initial admin, and start the application
CMD ["sh", "-c", "python run_migration.py && python provision_admin.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
