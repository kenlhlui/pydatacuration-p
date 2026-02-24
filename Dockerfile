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
# Create a workdir for user files
RUN mkdir -p /app/workdir && chown -R app:app /app/workdir

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
COPY --chown=app:app app.py /app/
COPY --chown=app:app pydatacuration /app/pydatacuration

# Start the app with uv
CMD ["uv", "run", "app.py"]

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget -q -O /dev/null http://localhost:9005/health || exit 1