"""
健康檢查端點
更新時間：2025-12-26 17:46
作者：AI Assistant
修改摘要：修正路由前綴重複問題，將 /health 改為 /，使實際路徑為 /api/v1/health
"""
from fastapi import APIRouter
from datetime import datetime
from app.api.v1.schemas.common import SuccessResponse

router = APIRouter()

@router.get("/")
async def health_check():
    """健康檢查端點"""
    return SuccessResponse(
        success=True,
        message="Care RAG API is healthy",
        data={
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }
    )

@router.get("/ready")
async def readiness_check():
    """就緒檢查端點"""
    return SuccessResponse(
        success=True,
        message="Service is ready",
        data={"ready": True}
    )

@router.get("/live")
async def liveness_check():
    """存活檢查端點"""
    return SuccessResponse(
        success=True,
        message="Service is alive",
        data={"alive": True}
    )


