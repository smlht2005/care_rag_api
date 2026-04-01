"""
Webhook API 端點
更新時間：2026-03-31 14:10
作者：AI Assistant
修改摘要：補強 LINE Reply 實測可觀測性：記錄 replyToken/answer 狀態，避免 query 成功但未觸發 reply 造成「聊天室無回覆」難以排查
更新時間：2026-03-31 11:53
作者：AI Assistant
修改摘要：新增 `POST /api/v1/webhook/line/query`：驗證 LINE 簽章、轉呼叫 care-rag-api 查詢並可選擇用 LINE Reply API 回覆到聊天室
更新時間：2025-12-26 12:15
作者：AI Assistant
修改摘要：創建 Webhook 事件接收和狀態查詢端點，修復線程安全問題
"""
from fastapi import APIRouter, Request, Depends, HTTPException, Header
from fastapi.responses import JSONResponse
from app.api.v1.schemas.webhook import (
    WebhookEventRequest,
    WebhookEventResponse,
    WebhookStatusResponse,
    LineWebhookRequest,
    LineWebhookProxyResponse,
)
from app.services.rag_service import RAGService
from app.services.cache_service import CacheService
from app.api.v1.dependencies import get_rag_service, get_cache_service
from app.utils.metrics import REQUEST_COUNTER
import logging
import uuid
import asyncio
from typing import Dict, Optional, Any, Tuple
from datetime import datetime

import base64
import hashlib
import hmac

import httpx

from app.config import settings
from app.services.cloud_run_auth_service import CloudRunAuthService

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


def _verify_line_signature(raw_body: bytes, channel_secret: str, line_signature: Optional[str]) -> bool:
    if not line_signature:
        return False
    mac = hmac.new(channel_secret.encode("utf-8"), raw_body, hashlib.sha256).digest()
    expected = base64.b64encode(mac).decode("utf-8")
    return hmac.compare_digest(expected, line_signature)


def _extract_first_text_query(line_request: LineWebhookRequest) -> Tuple[Optional[str], Optional[str]]:
    """
    回傳 (query_text, reply_token)；只取第一筆 text message。
    """
    for event in line_request.events:
        if (event.type or "").lower() != "message":
            continue
        msg = event.message
        if not msg:
            continue
        if (msg.type or "").lower() != "text":
            continue
        if msg.text:
            return msg.text, event.replyToken
    return None, None


async def _line_reply(reply_token: str, text: str) -> Tuple[Optional[int], Optional[str]]:
    """
    呼叫 LINE Reply API，把文字回覆到聊天室。
    - 若未啟用或缺 token，回 (None, reason)
    - 成功回 (status_code, None)
    - 失敗回 (status_code, response_text)
    """
    if not settings.LINE_REPLY_ENABLED:
        return None, "LINE_REPLY_ENABLED=false"
    if not settings.LINE_CHANNEL_ACCESS_TOKEN:
        return None, "LINE_CHANNEL_ACCESS_TOKEN is missing"
    if not reply_token:
        return None, "replyToken is missing"

    # LINE text message 長度限制（保守截斷）
    reply_text = (text or "").strip()
    if len(reply_text) > 4900:
        reply_text = reply_text[:4900] + "…"

    url = "https://api.line.me/v2/bot/message/reply"
    access_token = settings.LINE_CHANNEL_ACCESS_TOKEN.strip()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": reply_text}],
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if 200 <= resp.status_code < 300:
                return resp.status_code, None
            return resp.status_code, resp.text[:2000]
    except Exception as e:
        return 0, f"reply exception: {type(e).__name__}: {str(e)}"


@router.post("/line/query", response_model=LineWebhookProxyResponse)
async def line_query_webhook(
    request: Request,
    x_line_signature: Optional[str] = Header(None, alias="X-Line-Signature"),
):
    """
    LINE webhook → 驗簽 → 抽文字 → 呼叫 care-rag-api /api/v1/query（Bearer ID token + X-API-Key）→（可選）回覆 LINE。
    """
    event_id = str(uuid.uuid4())
    raw_body = await request.body()

    try:
        line_request = LineWebhookRequest.model_validate_json(raw_body)
    except Exception:
        return JSONResponse(
            status_code=400,
            content=LineWebhookProxyResponse(
                status="bad_request",
                event_id=event_id,
                forwarded=False,
                detail="Invalid JSON body",
            ).model_dump(),
        )

    if settings.LINE_WEBHOOK_REQUIRE_SIGNATURE:
        if not settings.LINE_CHANNEL_SECRET:
            return JSONResponse(
                status_code=500,
                content=LineWebhookProxyResponse(
                    status="error",
                    event_id=event_id,
                    forwarded=False,
                    detail="LINE_CHANNEL_SECRET is required when LINE_WEBHOOK_REQUIRE_SIGNATURE=true",
                ).model_dump(),
            )
        if not _verify_line_signature(raw_body, settings.LINE_CHANNEL_SECRET, x_line_signature):
            return JSONResponse(
                status_code=401,
                content=LineWebhookProxyResponse(
                    status="unauthorized",
                    event_id=event_id,
                    forwarded=False,
                    detail="Invalid LINE signature",
                ).model_dump(),
            )

    query_text, reply_token = _extract_first_text_query(line_request)
    if not query_text:
        return JSONResponse(
            status_code=200,
            content=LineWebhookProxyResponse(
                status="ok",
                event_id=event_id,
                forwarded=False,
                detail="No text message found",
            ).model_dump(),
        )

    if not settings.LINE_PROXY_QUERY_ENDPOINT or not settings.LINE_PROXY_TARGET_AUDIENCE:
        return JSONResponse(
            status_code=500,
            content=LineWebhookProxyResponse(
                status="error",
                event_id=event_id,
                forwarded=False,
                query=query_text,
                detail="LINE_PROXY_QUERY_ENDPOINT/LINE_PROXY_TARGET_AUDIENCE is missing",
            ).model_dump(),
        )

    try:
        auth = CloudRunAuthService()
        token = auth.get_id_token(
            target_audience=settings.LINE_PROXY_TARGET_AUDIENCE,
            invoker_service_account=settings.LINE_PROXY_INVOKER_SERVICE_ACCOUNT,
        )
    except Exception as exc:
        logger.error("Failed to mint Cloud Run ID token: %s", str(exc))
        return JSONResponse(
            status_code=500,
            content=LineWebhookProxyResponse(
                status="error",
                event_id=event_id,
                forwarded=False,
                query=query_text,
                detail=f"auth error: {type(exc).__name__}",
            ).model_dump(),
        )
    proxy_api_key = settings.LINE_PROXY_X_API_KEY or settings.API_KEY

    query_status: Optional[int] = None
    answer: Optional[str] = None
    detail: Optional[str] = None

    try:
        async with httpx.AsyncClient(timeout=settings.LINE_PROXY_TIMEOUT_SEC) as client:
            resp = await client.post(
                settings.LINE_PROXY_QUERY_ENDPOINT,
                headers={"Authorization": f"Bearer {token}", settings.API_KEY_HEADER: proxy_api_key},
                json={"query": query_text, "top_k": settings.LINE_PROXY_TOP_K},
            )
            query_status = resp.status_code
            if resp.status_code == 200:
                data = resp.json()
                answer = data.get("answer")
            else:
                detail = resp.text[:2000]
    except Exception as e:
        query_status = 0
        detail = f"proxy exception: {type(e).__name__}: {str(e)}"

    reply_status, reply_detail = (None, None)
    logger.info(
        "LINE webhook processed event_id=%s query_status=%s reply_enabled=%s reply_token_present=%s answer_present=%s",
        event_id,
        query_status,
        bool(settings.LINE_REPLY_ENABLED),
        bool(reply_token),
        answer is not None,
    )

    # 避免「query 成功但 answer 空字串/None」導致完全不嘗試 reply，讓實測時誤判成 webhook 沒打到
    if query_status == 200:
        reply_text = (answer or "").strip()
        if not reply_text:
            reply_text = "（系統未產生回覆內容，請稍後再試或換個問法）"
        reply_status, reply_detail = await _line_reply(reply_token or "", reply_text)

    return JSONResponse(
        status_code=200,
        content=LineWebhookProxyResponse(
            status="ok",
            event_id=event_id,
            forwarded=query_status == 200,
            query_status=query_status,
            query=query_text,
            answer=answer,
            detail=detail,
            reply_status=reply_status,
            reply_detail=reply_detail,
        ).model_dump(),
    )

