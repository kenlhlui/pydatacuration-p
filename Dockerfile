FROM python:3.12-slim

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app
COPY . /app

# Install any needed using uv sync
RUN uv sync --locked --no-cache

CMD ["uv", "run", "fastapi", "run", "app.py", "--port", "80", "--host", "0.0.0.0"]
