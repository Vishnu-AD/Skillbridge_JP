import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet

def hash_password(pw: str) -> str:
    return generate_password_hash(pw)

def verify_password(pw: str, pw_hash: str) -> bool:
    return check_password_hash(pw_hash, pw)

def get_fernet(key: str) -> Fernet:
    # key must be urlsafe base64-encoded 32-byte
    return Fernet(key.encode() if isinstance(key, str) else key)

def encrypt_text(fernet: Fernet, txt: str | None) -> str | None:
    if not txt:
        return None
    return fernet.encrypt(txt.encode()).decode()

def decrypt_text(fernet: Fernet, token: str | None) -> str | None:
    if not token:
        return None
    return fernet.decrypt(token.encode()).decode()

def new_csrf_token() -> str:
    return secrets.token_urlsafe(24)

def csrf_protect(session, form_token: str | None) -> bool:
    return bool(form_token) and session.get("csrf_token") == form_token