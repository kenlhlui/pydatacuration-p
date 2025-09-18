# Use uv + Debian bookworm (glibc), not Alpine
FROM ghcr.io/astral-sh/uv:python3.12-bookworm

# Install ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
  && rm -rf /var/lib/apt/lists/*

# Create a non-root user and group to run the app
ARG UID=1000
ARG GID=1000
RUN groupadd -g "$GID" app && \
    useradd -m -u "$UID" -g "$GID" -s /bin/bash app

# Create /app directory and set proper ownership
RUN mkdir -p /app && chown -R app:app /app

# Switch to non-root user
USER app

# Set working directory
WORKDIR /app

# Set environment variables
ENV UV_COMPILE_BYTECODE=1 
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_PREFERENCE=only-managed
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy the uv.lock and pyproject.toml first for better caching
COPY --chown=app:app uv.lock uv.lock
COPY --chown=app:app pyproject.toml pyproject.toml

# Create virtual environment and install dependencies as the app user
RUN uv venv --relocatable && \
    uv sync --frozen --no-install-project --no-dev --no-editable

# Copy the rest of your app
COPY --chown=app:app . /app

# Use port 8000 instead of 80 (non-root users can't bind to ports < 1024)
CMD ["uv", "run", "fastapi", "run", "app.py", "--port", "8000", "--host", "0.0.0.0"]

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8000/health || exit 1