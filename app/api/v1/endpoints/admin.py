"""
管理 API 端點
更新時間：2025-12-26 18:03
作者：AI Assistant
修改摘要：修正 datetime JSON 序列化問題，使用 model_dump(mode='json') 確保 datetime 正確序列化
"""
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from app.api.v1.schemas.admin import (
    SystemStatsResponse,
    CacheClearResponse,
    GraphStatsResponse
)
from app.core.security import verify_api_key
from app.services.cache_service import CacheService
from app.core.graph_store import GraphStore
from app.api.v1.dependencies import get_cache_service, get_graph_store
from app.utils.metrics import REQUEST_COUNTER
import logging
import time
from datetime import datetime

router = APIRouter()
logger = logging.getLogger("AdminEndpoint")

# 系統啟動時間（用於計算運行時間）
_start_time = time.time()

# 查詢統計（簡單實作，生產環境應使用資料庫或 Prometheus）
from typing import Dict, Any
_query_stats: Dict[str, int] = {
    "total_queries": 0,
    "total_documents": 0
}

@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    request: Request,
    api_key_verified: bool = Depends(verify_api_key)
):
    """取得系統統計資訊"""
    try:
        # 計算運行時間
        uptime_seconds = int(time.time() - _start_time)
        
        # TODO: 從 Prometheus 獲取實際指標
        # 目前使用簡單統計
        total_queries = _query_stats.get("total_queries", 0)
        total_documents = _query_stats.get("total_documents", 0)
        
        # TODO: 從快取服務獲取命中率
        cache_hit_rate = 0.0
        
        # TODO: 從 Prometheus 獲取平均回應時間
        average_response_time = 0.0
        
        response = SystemStatsResponse(
            total_queries=total_queries,
            total_documents=total_documents,
            cache_hit_rate=cache_hit_rate,
            average_response_time=average_response_time,
            uptime_seconds=uptime_seconds,
            timestamp=datetime.now()
        )
        
        return JSONResponse(content=response.model_dump(mode='json'))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get system stats error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(e)}
        )

@router.post("/cache/clear", response_model=CacheClearResponse)
async def clear_cache(
    request: Request,
    cache_service: CacheService = Depends(get_cache_service),
    api_key_verified: bool = Depends(verify_api_key)
):
    """清除快取"""
    try:
        # 清除快取
        keys_cleared = await cache_service.clear()
        
        response = CacheClearResponse(
            status="success",
            keys_cleared=keys_cleared if isinstance(keys_cleared, int) else 0,
            cleared_at=datetime.now()
        )
        
        logger.info(f"Cache cleared: {keys_cleared} keys")
        
        return JSONResponse(content=response.model_dump(mode='json'))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Clear cache error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(e)}
        )

@router.get("/graph/stats", response_model=GraphStatsResponse)
async def get_graph_stats(
    request: Request,
    graph_store: GraphStore = Depends(get_graph_store),
    api_key_verified: bool = Depends(verify_api_key)
):
    """取得圖結構統計資訊"""
    try:
        # 使用 GraphStore 的統計方法（封裝良好，不依賴具體實作）
        stats = await graph_store.get_statistics()
        
        total_entities = stats.get("total_entities", 0)
        total_relations = stats.get("total_relations", 0)
        entity_types = stats.get("entity_types", {})
        relation_types = stats.get("relation_types", {})
        
        response = GraphStatsResponse(
            total_entities=total_entities,
            total_relations=total_relations,
            entity_types=entity_types,
            relation_types=relation_types,
            timestamp=datetime.now()
        )
        
        return JSONResponse(content=response.model_dump(mode='json'))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get graph stats error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(e)}
        )

