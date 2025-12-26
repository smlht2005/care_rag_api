"""
自訂例外類別
"""
from fastapi import HTTPException, status

class CareRAGException(Exception):
    """基礎例外類別"""
    pass

class InvalidAPIKeyException(HTTPException):
    """無效的 API Key"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )

class QueryValidationException(HTTPException):
    """查詢驗證失敗"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Query validation failed: {detail}"
        )

class LLMServiceException(HTTPException):
    """LLM 服務錯誤"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM service error: {detail}"
        )

class CacheServiceException(HTTPException):
    """快取服務錯誤"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Cache service error: {detail}"
        )


