"""
管理 API 結構定義
更新時間：2025-12-26 12:08
作者：AI Assistant
修改摘要：創建管理相關的 Schema 定義
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class SystemStatsResponse(BaseModel):
    """系統統計回應"""
    total_queries: int = 0
    total_documents: int = 0
    cache_hit_rate: float = 0.0
    average_response_time: float = 0.0
    uptime_seconds: int = 0
    timestamp: datetime

class CacheClearResponse(BaseModel):
    """快取清除回應"""
    status: str = "success"
    keys_cleared: int = 0
    cleared_at: datetime

class GraphStatsResponse(BaseModel):
    """圖結構統計回應"""
    total_entities: int = 0
    total_relations: int = 0
    entity_types: Dict[str, int] = {}
    relation_types: Dict[str, int] = {}
    timestamp: datetime


