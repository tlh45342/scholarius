"""HTTPS launcher for Scholarius."""

import os

import uvicorn

from app.cert import ensure_ssl_certs


def main() -> None:
    host = os.getenv("SCHOLARIUS_BIND_HOST", "0.0.0.0")
    port = int(os.getenv("SCHOLARIUS_PORT", "8000"))
    certificate_host = os.getenv("SCHOLARIUS_SSL_HOST", "192.168.150.83")

    cert_file, key_file = ensure_ssl_certs(certificate_host)

    print(
        f"Scholarius HTTPS server starting on {host}:{port}",
        flush=True,
    )

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        ssl_certfile=cert_file,
        ssl_keyfile=key_file,
        proxy_headers=True,
    )


if __name__ == "__main__":
    main()
