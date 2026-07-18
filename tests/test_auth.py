from app.auth import hash_password, verify_password


def test_password_round_trip():
    encoded = hash_password("Scholarius-Test-472")
    assert encoded.startswith("pbkdf2_sha256$")
    assert verify_password("Scholarius-Test-472", encoded)
    assert not verify_password("wrong-password", encoded)
