"""SSL certificate management for Scholarius.

A self-signed certificate is generated on first startup and reused on
subsequent runs. The certificate and private key live in the persistent
``app`` directory.
"""

from pathlib import Path
import subprocess


def ensure_ssl_certs(host: str, days: int = 365) -> tuple[str, str]:
    """Return paths to a reusable certificate and private key."""

    app_dir = Path(__file__).resolve().parent
    cert_path = app_dir / "cert.pem"
    key_path = app_dir / "key.pem"

    if cert_path.exists() and key_path.exists():
        print("Using existing Scholarius SSL certificate", flush=True)
        return str(cert_path), str(key_path)

    print(
        f"Generating a self-signed Scholarius certificate for {host}",
        flush=True,
    )

    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:4096",
            "-sha256",
            "-nodes",
            "-out",
            str(cert_path),
            "-keyout",
            str(key_path),
            "-days",
            str(days),
            "-subj",
            f"/CN={host}",
            "-addext",
            f"subjectAltName=IP:{host}",
        ],
        check=True,
    )

    return str(cert_path), str(key_path)
