FROM python:3.13-slim

WORKDIR /app

# Install system dependencies (git for GitHub packages, build tools for compiling)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first (for better caching)
# Build context is backend/ directory, so files are directly here
COPY pyproject.toml uv.lock* ./

# Install dependencies using uv
RUN uv sync --frozen --no-dev

# Copy backend code (includes agents/ subdirectory)
COPY . .

# Note: agents/ is already included in backend/ copy above
# No need to copy separately - it would overwrite with wrong directory

# Expose port 8000
EXPOSE 8000

# Health check using uv run
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD uv run python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application using uv (runs in virtual environment)
# Use PORT environment variable if set (for Railway/cloud platforms), otherwise default to 8000
CMD ["sh", "-c", "uv run uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]

