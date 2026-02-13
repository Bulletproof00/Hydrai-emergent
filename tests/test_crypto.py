from packages.core.crypto import decrypt_secret, encrypt_secret


def test_encrypt_decrypt_roundtrip() -> None:
    master = "test-master-key"
    secret = "super-secret"
    encrypted = encrypt_secret(master, secret)
    assert encrypted != secret
    assert decrypt_secret(master, encrypted) == secret
