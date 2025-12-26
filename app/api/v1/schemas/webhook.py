"""
Webhook API 結構定義
更新時間：2025-12-26 12:08
作者：AI Assistant
修改摘要：創建 Webhook 相關的 Schema 定義
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from datetime import datetime

class WebhookEventRequest(BaseModel):
    """Webhook 事件請求"""
    event_type: Literal["document_updated", "knowledge_base_changed", "graph_updated", "cache_cleared"] = Field(
        ..., description="事件類型"
    )
    payload: Dict[str, Any] = Field(..., description="事件負載")
    timestamp: Optional[datetime] = Field(None, description="事件時間戳")
    signature: Optional[str] = Field(None, description="Webhook 簽名（可選）")

class WebhookEventResponse(BaseModel):
    """Webhook 事件回應"""
    status: str = "received"
    event_id: str
    processed_at: datetime

class WebhookStatusResponse(BaseModel):
    """Webhook 狀態回應"""
    status: str = "active"
    total_events: int = 0
    last_event_at: Optional[datetime] = None
    webhook_url: Optional[str] = None


