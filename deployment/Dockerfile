FROM python:3.11-slim

LABEL maintainer="Corpus Forge Team"
LABEL description="Corpus Forge - Document Processing and Retrieval System"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copy application code
COPY app/ ./app/
COPY templates/ ./templates/
COPY static/ ./static/

# Create data directory for uploads
RUN mkdir -p /app/data/uploads

# Create non-root user
RUN useradd -m -u 1000 corpus-forge && \
    chown -R corpus-forge:corpus-forge /app

USER corpus-forge

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/').read()" || exit 1

# Run application with gunicorn
CMD ["gunicorn", \
     "--workers=4", \
     "--worker-class=sync", \
     "--bind=0.0.0.0:5000", \
     "--timeout=60", \
     "--access-logfile=-", \
     "--error-logfile=-", \
     "app:create_app()"]
