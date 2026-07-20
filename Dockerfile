FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install Python dependencies before copying the application so Docker can
# reuse this layer when only application files change.
COPY requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY app ./app

EXPOSE 8000

# Verify that the FastAPI service is responding inside the container.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/version', timeout=3)" || exit 1

# app.main defines the FastAPI application object; Uvicorn must remain as
# Docker's foreground process. Running `python -m app.main` only imports the
# module and then exits, which causes a restart loop under restart policies.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
