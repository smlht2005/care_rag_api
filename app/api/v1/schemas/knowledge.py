"""
知識庫 API 結構定義
更新時間：2025-12-26 12:15
作者：AI Assistant
修改摘要：創建知識庫相關的 Schema 定義，添加輸入驗證
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

# 允許的實體類型列表
ALLOWED_ENTITY_TYPES = [
    "Person", "Organization", "Location", "Document", 
    "Concept", "Event", "Product", "Service", "Other"
]

class KnowledgeQueryRequest(BaseModel):
    """知識庫查詢請求"""
    query: str = Field(..., description="查詢問題", min_length=1, max_length=1000)
    top_k: Optional[int] = Field(3, description="返回結果數量", ge=1, le=10)
    include_graph: Optional[bool] = Field(True, description="是否包含圖結構資訊")
    
    @validator('query')
    def validate_query(cls, v):
        """驗證查詢字串"""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()

class KnowledgeQueryResponse(BaseModel):
    """知識庫查詢回應"""
    answer: str
    sources: List[Dict[str, Any]] = []
    graph_entities: List[Dict[str, Any]] = []
    graph_relations: List[Dict[str, Any]] = []
    query: str

class KnowledgeSourceResponse(BaseModel):
    """知識來源回應"""
    sources: List[Dict[str, Any]] = []
    total: int = 0

class KnowledgeIngestRequest(BaseModel):
    """知識攝取請求"""
    content: str = Field(..., description="知識內容", min_length=1, max_length=1000000)
    source: Optional[str] = Field(None, description="來源標識", max_length=255)
    metadata: Optional[Dict[str, Any]] = Field(None, description="元數據")
    entity_types: Optional[List[str]] = Field(None, description="實體類型列表", max_items=50)
    
    @validator('content')
    def validate_content(cls, v):
        """驗證內容長度"""
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        if len(v) > 1000000:
            raise ValueError("Content too long, maximum 1,000,000 characters")
        return v.strip()
    
    @validator('entity_types')
    def validate_entity_types(cls, v):
        """驗證實體類型"""
        if v:
            invalid_types = [t for t in v if t not in ALLOWED_ENTITY_TYPES]
            if invalid_types:
                raise ValueError(f"Invalid entity types: {invalid_types}. Allowed types: {ALLOWED_ENTITY_TYPES}")
        return v
    
    @validator('source')
    def validate_source(cls, v):
        """驗證來源標識"""
        if v and len(v) > 255:
            raise ValueError("Source identifier too long, maximum 255 characters")
        return v

class KnowledgeIngestResponse(BaseModel):
    """知識攝取回應"""
    document_id: str
    entities_count: int = 0
    relations_count: int = 0
    status: str = "success"
    created_at: datetime

