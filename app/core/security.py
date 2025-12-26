"""
安全驗證模組
"""
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.config import settings
from app.core.exceptions import InvalidAPIKeyException

api_key_header = APIKeyHeader(name=settings.API_KEY_HEADER, auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """驗證 API Key"""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key is required"
        )
    
    if api_key != settings.API_KEY:
        raise InvalidAPIKeyException()
    
    return True

async def optional_api_key(api_key: str = Security(api_key_header)):
    """可選的 API Key 驗證"""
    if api_key and api_key != settings.API_KEY:
        raise InvalidAPIKeyException()
    return api_key is not None
