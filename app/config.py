"""
應用程式配置檔案
更新時間：2025-12-26 15:00
作者：AI Assistant
修改摘要：簡化配置，移除 GEMINI_API_KEY 和 GOOGLE_CLOUD_PROJECT，統一使用 GOOGLE_API_KEY，添加 load_dotenv() 確保環境變數載入
更新時間：2025-12-26 14:03
作者：AI Assistant
修改摘要：將預設 Gemini 模型名稱從 gemini-1.5-flash 改為 gemini-3.0-flash-preview
更新時間：2025-12-26 13:57
作者：AI Assistant
修改摘要：添加 GEMINI_MODEL_NAME 配置項，支援可配置 Gemini 模型名稱（預設 gemini-1.5-flash）
更新時間：2025-12-26 13:44
作者：AI Assistant
修改摘要：添加 GOOGLE_API_KEY 欄位支援，解決 Pydantic 驗證錯誤（Extra inputs are not permitted）
"""
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import Optional

# 確保 .env 檔案在 Settings 初始化前已載入（與 care_rag 一致）
load_dotenv()

class Settings(BaseSettings):
    """應用程式設定"""
    
    # API 設定
    API_TITLE: str = "Care RAG API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "企業級 RAG API - REST / SSE / WebSocket"
    
    # 伺服器設定
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    DEBUG: bool = False
    
    # CORS 設定
    CORS_ORIGINS: list = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]
    
    # API Key 設定
    API_KEY: Optional[str] = "test-api-key"
    API_KEY_HEADER: str = "X-API-Key"
    
    # LLM 設定
    LLM_PROVIDER: str = "gemini"  # gemini, openai, deepseek
    LLM_MAX_TOKENS: int = 2000
    LLM_TEMPERATURE: float = 0.7
    GOOGLE_API_KEY: Optional[str] = None  # Google Gemini API Key（與 care_rag 一致）
    GEMINI_MODEL_NAME: str = "gemini-2.0-flash"  # gemini-3.0-flash, gemini-1.5-flash (快) 或 gemini-1.5-pro (強)
    DEEPSEEK_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    
    # Redis 設定
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_TTL: int = 3600
    
    # Prometheus 設定
    METRICS_PORT: int = 8001
    
    # GraphRAG 設定
    GRAPH_DB_PATH: str = "./data/graph.db"
    VECTOR_DIMENSION: int = 768
    TOP_K_RESULTS: int = 3
    GRAPH_QUERY_MAX_ENTITIES: int = 5  # 圖查詢時最多處理的實體數量
    GRAPH_QUERY_MAX_NEIGHBORS: int = 3  # 每個實體最多查詢的鄰居數量
    GRAPH_CACHE_TTL: int = 3600  # 圖查詢快取 TTL（秒）
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

