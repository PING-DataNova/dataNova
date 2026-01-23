FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libxml2-dev \
    libxslt-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (ultra-fast Python package installer)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies with uv (10-100x faster than pip/poetry)
RUN uv pip install --system -r pyproject.toml

# Copy application
COPY . .

# Create necessary directories
RUN mkdir -p data logs

CMD ["python", "-m", "src.main"]
