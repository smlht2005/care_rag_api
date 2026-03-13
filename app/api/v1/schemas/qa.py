"""
QA 查詢 API 結構定義

更新時間：2026-03-06
作者：AI Assistant
修改摘要：QASearchResponse 增加 answer 欄位（QUERY_TYPE=rag 時由 LLM 產出）
更新時間：2026-01-13 15:20
作者：AI Assistant
修改摘要：更新標頭註解日期
更新時間：2025-12-30 11:30
作者：AI Assistant
修改摘要：建立 QA 查詢相關的 Schema 定義
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class QASearchRequest(BaseModel):
    """QA 搜尋請求"""
    query: str = Field(..., description="搜尋關鍵詞", min_length=1, max_length=200)
    limit: Optional[int] = Field(10, description="返回結果數量", ge=1, le=50)
    doc_id: Optional[str] = Field(None, description="限制搜尋特定文件 ID")


class QAResult(BaseModel):
    """QA 結果"""
    id: str
    qa_number: Optional[int] = None
    question: str
    answer: str
    scenario: Optional[str] = None
    keywords: Optional[List[str]] = []
    steps: Optional[List[str]] = []
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}


class QASearchResponse(BaseModel):
    """QA 搜尋回應（QUERY_TYPE=rag 時含 answer；sql 時 answer 為 None）"""
    query: str
    total: int
    results: List[QAResult]
    answer: Optional[str] = None  # rag 時為 LLM 產出之單一回答；sql 時為 None


class QADocumentInfo(BaseModel):
    """QA 文件資訊"""
    id: str
    name: str
    type: str
    qa_count: int
    source: Optional[str] = None


class QADocumentsResponse(BaseModel):
    """QA 文件列表回應"""
    total: int
    documents: List[QADocumentInfo]


class QAByDocumentRequest(BaseModel):
    """根據文件 ID 查詢 QA"""
    doc_id: str = Field(..., description="文件 ID")
    limit: Optional[int] = Field(100, description="返回結果數量", ge=1, le=200)
