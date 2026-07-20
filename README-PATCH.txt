Scholarius 0.0.9 Docker startup fix

Replace:
  Dockerfile
  changelog.md

Then run:
  docker compose down
  docker compose build --no-cache
  docker compose up -d
  docker compose logs -f scholarius

Expected startup output includes:
  Uvicorn running on http://0.0.0.0:8000

The version remains 0.0.9.
