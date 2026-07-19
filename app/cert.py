"""SSL certificate management."""
import subprocess
from pathlib import Path

def ensure_ssl_certs():
    """Generate self-signed certs if they don't exist."""
    cert_path = Path(__file__).parent / "cert.pem"
    key_path = Path(__file__).parent / "key.pem"
    
    if cert_path.exists() and key_path.exists():
        print("✓ Using existing SSL certificates")
        return str(cert_path), str(key_path)
    
    print("🔐 Generating self-signed SSL certificate...")
    subprocess.run([
        "openssl", "req", "-x509", "-newkey", "rsa:4096",
        "-nodes", "-out", str(cert_path), "-keyout", str(key_path),
        "-days", "365", "-subj", "/CN=192.168.150.83"
    ], check=True)
    print("✓ SSL certificate created (valid 365 days)")
    return str(cert_path), str(key_path)
