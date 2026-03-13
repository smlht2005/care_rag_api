"""
API v1 路由配置
更新時間：2026-01-13 15:20
作者：AI Assistant
修改摘要：更新標頭註解日期
更新時間：2025-12-30 11:30
作者：AI Assistant
修改摘要：註冊 QA 查詢路由
更新時間：2025-12-26 12:08
作者：AI Assistant
修改摘要：註冊新的 knowledge、webhook、admin 路由
"""
from fastapi import APIRouter
from app.api.v1.endpoints import query, documents, health, websocket, knowledge, webhook, admin, qa

router = APIRouter()

# 註冊所有端點
router.include_router(query.router, tags=["Query"])
router.include_router(documents.router, prefix="/documents", tags=["Documents"])
router.include_router(health.router, prefix="/health", tags=["Health"])
router.include_router(websocket.router, tags=["WebSocket"])
router.include_router(knowledge.router, prefix="/knowledge", tags=["Knowledge"])
router.include_router(webhook.router, prefix="/webhook", tags=["Webhook"])
router.include_router(admin.router, prefix="/admin", tags=["Admin"])
router.include_router(qa.router, prefix="/qa", tags=["QA"])

