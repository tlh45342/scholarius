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

# Run app directly with Python (enables if __name__ == "__main__" block)
# This generates SSL certs and runs uvicorn with HTTPS
CMD ["python", "app/main.py"]
