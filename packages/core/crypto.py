import base64
import hashlib

from cryptography.fernet import Fernet


def _derive_fernet_key(master_key: str) -> bytes:
    digest = hashlib.sha256(master_key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_secret(master_key: str, value: str) -> str:
    f = Fernet(_derive_fernet_key(master_key))
    return f.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(master_key: str, encrypted: str) -> str:
    f = Fernet(_derive_fernet_key(master_key))
    return f.decrypt(encrypted.encode("utf-8")).decode("utf-8")
