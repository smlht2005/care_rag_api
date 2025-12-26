"""
通用 API 結構定義
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any

class ErrorResponse(BaseModel):
    """錯誤回應結構"""
    error: str
    detail: Optional[str] = None
    code: Optional[int] = None

class SuccessResponse(BaseModel):
    """成功回應結構"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class PaginationParams(BaseModel):
    """分頁參數"""
    page: int = 1
    page_size: int = 10

class PaginatedResponse(BaseModel):
    """分頁回應"""
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int


