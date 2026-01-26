
FROM python:3.13-slim AS builder

WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libxml2-dev \
    libxslt-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (ultra-fast Python package installer)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first (for caching)
COPY pyproject.toml uv.lock* ./

# Create virtual environment and install dependencies
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv pip install -e .

FROM python:3.13-slim

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy only runtime dependencies from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY config/ ./config/
COPY data/company_profiles/ ./data/company_profiles/

# Create necessary directories with proper permissions
RUN mkdir -p data logs data/documents \
    && chown -R appuser:appuser /app

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Switch to non-root user
USER appuser

# Expose port (if needed for API later)
EXPOSE 8000

# Run application
CMD ["python", "-m", "src.main", "--run-once"]
