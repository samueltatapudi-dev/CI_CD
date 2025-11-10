# syntax=docker/dockerfile:1

ARG PYTHON_IMAGE=python:3.12-slim
FROM ${PYTHON_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    # Select which app under flask_apps to run
    APP_VERSION=ACEest_Fitness \
    # HTTP port in the container
    PORT=8000 \
    # Process manager: gunicorn (default) or flask
    RUNNER=gunicorn \
    # Number of gunicorn workers
    WORKERS=2

WORKDIR /app

# System deps (optional, for matplotlib build if needed)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN python -m pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install gunicorn

# Copy source
COPY . .

# Entrypoint script to route to selected app
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE ${PORT}

ENTRYPOINT ["/entrypoint.sh"]
CMD []

