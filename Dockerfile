FROM python:3.12-slim

# Install system dependencies including ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy the current directory contents into the container at /app
WORKDIR /app
COPY . /app

# Install any needed using uv sync
RUN uv sync --locked --no-cache

ENV VIRTUAL_ENV="/app/.venv"
ENV PATH="/app/.venv/bin:$PATH"

# Run the application
CMD ["fastapi", "run", "app.py", "--port", "80", "--host", "0.0.0.0"]