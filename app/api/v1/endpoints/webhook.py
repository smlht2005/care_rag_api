"""
Webhook API 端點
更新時間：2025-12-26 12:15
作者：AI Assistant
修改摘要：創建 Webhook 事件接收和狀態查詢端點，修復線程安全問題
"""
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from app.api.v1.schemas.webhook import (
    WebhookEventRequest,
    WebhookEventResponse,
    WebhookStatusResponse
)
from app.services.rag_service import RAGService
from app.services.cache_service import CacheService
from app.api.v1.dependencies import get_rag_service, get_cache_service
from app.utils.metrics import REQUEST_COUNTER
import logging
import uuid
import asyncio
from typing import Dict, Optional, Any
from datetime import datetime

router = APIRouter()
logger = logging.getLogger("WebhookEndpoint")

# Webhook 狀態追蹤（使用 asyncio.Lock 保護共享狀態，生產環境應使用資料庫）
_webhook_stats_lock = asyncio.Lock()
_webhook_stats: Dict[str, Any] = {
    "total_events": 0,
    "last_event_at": None,
    "status": "active"
}

async def update_webhook_stats(event_at: Optional[datetime] = None) -> Dict[str, Any]:
    """更新 Webhook 統計資訊（線程安全）"""
    async with _webhook_stats_lock:
        _webhook_stats["total_events"] += 1
        if event_at:
            _webhook_stats["last_event_at"] = event_at
        return _webhook_stats.copy()

async def get_webhook_stats() -> Dict[str, Any]:
    """取得 Webhook 統計資訊（線程安全）"""
    async with _webhook_stats_lock:
        return _webhook_stats.copy()

@router.post("/events", response_model=WebhookEventResponse)
async def receive_webhook_event(
    request: Request,
    event_request: WebhookEventRequest,
    rag_service: RAGService = Depends(get_rag_service),
    cache_service: CacheService = Depends(get_cache_service)
):
    """接收 Webhook 事件"""
    try:
        event_id = str(uuid.uuid4())
        processed_at = datetime.now()
        
        # 更新統計（線程安全）
        await update_webhook_stats(processed_at)
        
        # 根據事件類型處理
        if event_request.event_type == "document_updated":
            logger.info(f"Webhook: Document updated event received: {event_id}")
            # TODO: 處理文檔更新事件
            # 例如：清除相關快取、重新索引等
            
        elif event_request.event_type == "knowledge_base_changed":
            logger.info(f"Webhook: Knowledge base changed event received: {event_id}")
            # TODO: 處理知識庫變更事件
            
        elif event_request.event_type == "graph_updated":
            logger.info(f"Webhook: Graph updated event received: {event_id}")
            # TODO: 處理圖結構更新事件
            
        elif event_request.event_type == "cache_cleared":
            logger.info(f"Webhook: Cache cleared event received: {event_id}")
            # 清除快取
            await cache_service.clear()
            
        # 驗證簽名（如果提供）
        if event_request.signature:
            # TODO: 實作簽名驗證邏輯
            logger.debug(f"Webhook signature verification skipped (not implemented): {event_id})")
        
        response = WebhookEventResponse(
            status="received",
            event_id=event_id,
            processed_at=processed_at
        )
        
        REQUEST_COUNTER.labels(method="POST", endpoint="/api/v1/webhook/events", status="200").inc()
        
        return JSONResponse(content=response.model_dump())
        
    except Exception as e:
        logger.error(f"Webhook event processing error: {str(e)}")
        REQUEST_COUNTER.labels(method="POST", endpoint="/api/v1/webhook/events", status="500").inc()
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(e)}
        )

@router.get("/status", response_model=WebhookStatusResponse)
async def get_webhook_status(
    request: Request
):
    """取得 Webhook 狀態"""
    try:
        # 取得統計資訊（線程安全）
        stats = await get_webhook_stats()
        
        response = WebhookStatusResponse(
            status=stats.get("status", "active"),
            total_events=stats.get("total_events", 0),
            last_event_at=stats.get("last_event_at"),
            webhook_url=None  # TODO: 從配置中獲取
        )
        
        return JSONResponse(content=response.model_dump())
        
    except Exception as e:
        logger.error(f"Get webhook status error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(e)}
        )

