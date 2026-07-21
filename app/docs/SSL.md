# Scholarius HTTPS

Scholarius runs Uvicorn with a self-signed TLS certificate.

The certificate files are:

```text
app/cert.pem
app/key.pem
```

They are reused when present. If either is absent, `app/cert.py` invokes
OpenSSL to create a new certificate.

Set the IP address included in the certificate with:

```bash
export SCHOLARIUS_SSL_HOST=192.168.150.83
```

or place it in a `.env` file beside `compose.yaml`:

```text
SCHOLARIUS_SSL_HOST=192.168.150.83
```

Access the application with:

```text
https://192.168.150.83:8000
```

Because the certificate is self-signed, browsers will display a trust warning
until the certificate is explicitly trusted.
