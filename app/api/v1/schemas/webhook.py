"""
Webhook API 結構定義
更新時間：2026-03-31 11:53
作者：AI Assistant
修改摘要：新增 LINE webhook proxy 所需 schema（events/message/replyToken）與 proxy 回應格式
更新時間：2025-12-26 12:08
作者：AI Assistant
修改摘要：創建 Webhook 相關的 Schema 定義
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal, List
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


class LineWebhookMessage(BaseModel):
    type: str
    id: Optional[str] = None
    text: Optional[str] = None


class LineWebhookEvent(BaseModel):
    type: str
    replyToken: Optional[str] = None
    message: Optional[LineWebhookMessage] = None
    source: Optional[Dict[str, Any]] = None
    timestamp: Optional[int] = None


class LineWebhookRequest(BaseModel):
    events: List[LineWebhookEvent] = Field(default_factory=list)


class LineWebhookProxyResponse(BaseModel):
    status: str
    event_id: str
    forwarded: bool = False
    query_status: Optional[int] = None
    query: Optional[str] = None
    answer: Optional[str] = None
    detail: Optional[str] = None
    reply_status: Optional[int] = None
    reply_detail: Optional[str] = None

