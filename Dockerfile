FROM python:3.11-slim

WORKDIR /app

# Install openssl (required for SSL certificate generation)
RUN apt-get update && \
    apt-get install -y openssl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Use -m flag to run as module (fixes import paths)
CMD ["python", "-m", "app.main"]
