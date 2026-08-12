FROM python:3.12-slim

WORKDIR /app

# build-essential + libicu-dev: needed to compile PyICU (Russian/Greek)
# against the system ICU library — PyICU has no prebuilt wheels.
# espeak-ng: runtime binary + voice data for Arabic phonemization; not
# compiled against, so no -dev package needed for it.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libicu-dev espeak-ng \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

# Shell form (not exec/array form) so $PORT actually expands — Render
# assigns a dynamic port via this env var and routes to whatever the
# container listens on. The ${PORT:-8000} default keeps `docker compose
# up` working locally, where PORT isn't set.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
