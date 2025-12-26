"""
文件 API 結構定義
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class DocumentRequest(BaseModel):
    """文件新增請求"""
    content: str = Field(..., description="文件內容", min_length=1)
    metadata: Optional[Dict[str, Any]] = Field(None, description="文件元資料")
    source: Optional[str] = Field(None, description="文件來源")

class DocumentResponse(BaseModel):
    """文件回應"""
    id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    source: Optional[str] = None
    created_at: Optional[str] = None

class DocumentListRequest(BaseModel):
    """批量文件新增請求"""
    documents: List[DocumentRequest] = Field(..., description="文件列表", min_items=1)

class DocumentListResponse(BaseModel):
    """批量文件回應"""
    status: str
    count: int
    document_ids: List[str] = []


