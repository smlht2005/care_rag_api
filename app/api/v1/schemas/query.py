"""
查詢 API 結構定義
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class QueryRequest(BaseModel):
    """查詢請求"""
    query: str = Field(..., description="查詢問題", min_length=1)
    top_k: Optional[int] = Field(3, description="返回結果數量", ge=1, le=10)
    provider: Optional[str] = Field(None, description="LLM provider (gemini/openai/deepseek)")
    max_tokens: Optional[int] = Field(None, description="最大 token 數", ge=1, le=4000)
    temperature: Optional[float] = Field(None, description="溫度參數", ge=0.0, le=2.0)

class QueryResponse(BaseModel):
    """查詢回應"""
    answer: str
    sources: List[Dict[str, Any]] = []
    query: str
    provider: Optional[str] = None

class StreamChunk(BaseModel):
    """串流回應片段"""
    chunk: str
    index: int
    done: bool = False
