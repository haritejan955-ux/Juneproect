from fastapi import Header, HTTPException, status

from app.core.config import get_settings


async def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    """Fail-closed: an unset API_KEYS config rejects every request, never lets everyone through."""
    settings = get_settings()
    if not settings.api_keys or x_api_key not in settings.api_keys:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")
