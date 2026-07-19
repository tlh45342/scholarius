"""SSL Certificate Management for Scholarius.

Generates self-signed certificates on first startup.
Certificates are reused on subsequent runs.
"""

import subprocess
from pathlib import Path


def ensure_ssl_certs(host: str = "192.168.150.83", days: int = 365):
    """
    Generate self-signed SSL certificates if they don't exist.
    
    Args:
        host: The hostname/IP for the certificate (default: local dev IP)
        days: Certificate validity period in days (default: 365)
    
    Returns:
        Tuple[str, str]: (cert_file_path, key_file_path)
    """
    app_dir = Path(__file__).parent
    cert_path = app_dir / "cert.pem"
    key_path = app_dir / "key.pem"
    
    # If certs already exist, use them
    if cert_path.exists() and key_path.exists():
        print(f"✓ Using existing SSL certificates")
        return str(cert_path), str(key_path)
    
    # Generate new certs
    print("🔐 Generating self-signed SSL certificate...")
    print(f"   Host: {host}")
    print(f"   Validity: {days} days")
    
    try:
        subprocess.run(
            [
                "openssl",
                "req",
                "-x509",
                "-newkey", "rsa:4096",
                "-nodes",
                "-out", str(cert_path),
                "-keyout", str(key_path),
                "-days", str(days),
                "-subj", f"/CN={host}"
            ],
            check=True,
            capture_output=True
        )
        
        print(f"✓ SSL certificate created successfully")
        print(f"\n⚠️  On first visit, your browser will show a security warning.")
        print(f"   This is normal for self-signed certificates.")
        print(f"   Click 'Proceed' or 'Advanced' → 'Proceed anyway' to continue.\n")
        
        return str(cert_path), str(key_path)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to generate SSL certificate")
        print(f"   Error: {e.stderr.decode()}")
        raise
    except FileNotFoundError:
        print(f"❌ OpenSSL not found. Install it with:")
        print(f"   macOS: brew install openssl")
        print(f"   Linux: apt-get install openssl")
        raise
