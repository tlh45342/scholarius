Scholarius 0.0.9 SSL restoration patch

Replace/add the included files, then set SCHOLARIUS_SSL_HOST to the server IP.

Rebuild:
    docker compose down
    docker compose build --no-cache
    docker compose up -d
    docker compose logs -f scholarius

Open:
    https://<server-ip>:8000
