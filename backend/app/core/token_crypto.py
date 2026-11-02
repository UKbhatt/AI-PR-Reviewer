from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from app.config import settings
from app.utils.exceptions import ValidationException


def _fernet() -> Optional[Fernet]:
    key = settings.TOKEN_ENCRYPTION_KEY
    return Fernet(key.encode()) if key else None


def encrypt_token(token: Optional[str]) -> Optional[str]:
    """Encrypt a user-supplied secret so it never crosses the broker in plaintext."""
    if not token:
        return None
    fernet = _fernet()
    if fernet is None:
        raise ValidationException(
            "Per-request GitHub tokens are disabled: TOKEN_ENCRYPTION_KEY is not configured on the server"
        )
    return fernet.encrypt(token.encode()).decode()


def decrypt_token(value: Optional[str]) -> Optional[str]:
    """Reverse encrypt_token inside the worker."""
    if not value:
        return None
    fernet = _fernet()
    if fernet is None:
        raise ValidationException("TOKEN_ENCRYPTION_KEY is not configured on the worker")
    try:
        return fernet.decrypt(value.encode()).decode()
    except InvalidToken as e:
        raise ValidationException("GitHub token could not be decrypted; API and worker keys differ") from e
