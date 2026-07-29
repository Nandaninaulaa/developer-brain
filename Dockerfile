# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app/backend

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install all Python dependencies (Django, DRF, gunicorn, whitenoise, the
# RAG stack) from the single requirements.txt.
COPY backend/requirements.txt /app/backend/
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy the rest of the project (includes the pre-built frontend/dist, which
# Django's STATICFILES_DIRS points at)
COPY . /app/

RUN chmod +x /app/entrypoint.sh

# NOTE: migrations and collectstatic run at container *start* (see
# entrypoint.sh), not here at build time — that way they run against
# whatever DATABASE_URL / volume is attached at runtime, not a
# build-time-only sqlite file baked into the image.

# Expose port
EXPOSE 8000

# Run the application via gunicorn (a real production WSGI server —
# manage.py runserver is dev-only: single-threaded and not meant to take
# real traffic).
ENTRYPOINT ["/app/entrypoint.sh"]
