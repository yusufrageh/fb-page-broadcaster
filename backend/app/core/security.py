from cryptography.fernet import Fernet

from app.core.config import app_settings

_fernet = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        key = app_settings.ENCRYPTION_KEY
        if not key:
            key = Fernet.generate_key().decode()
            print(f"WARNING: No ENCRYPTION_KEY set. Generated temporary key: {key}")
            print("Set this in your .env file to persist encrypted data across restarts.")
        _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet


def encrypt(value: str) -> str:
    if not value:
        return ""
    return _get_fernet().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    if not value:
        return ""
    return _get_fernet().decrypt(value.encode()).decode()
