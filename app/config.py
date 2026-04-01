"""
應用程式配置檔案
更新時間：2026-03-31 11:53
作者：AI Assistant
修改摘要：新增 LINE Reply API 所需設定（LINE_CHANNEL_ACCESS_TOKEN 等），供 LINE webhook proxy 在取得答案後回覆到 LINE 聊天室
更新時間：2026-03-11 00:00
作者：AI Assistant
修改摘要：新增 QA_MIN_SCORE（float，預設 0.60）控制 QA embedding 搜尋相似度門檻，低於此值的結果將被過濾，避免負向查詢誤報
更新時間：2026-03-10
作者：AI Assistant
修改摘要：載入 .env 後若同時設有 GEMINI_API_KEY 與 GOOGLE_API_KEY 則移除 GEMINI_API_KEY，避免 google-genai SDK 重複印出提示
更新時間：2026-03-09 19:00
作者：AI Assistant
修改摘要：新增 USE_GOOGLE_GENAI_SDK、GEMINI_EMBEDDING_MODEL 供 Embedding 使用新 SDK（text-embedding-004）
更新時間：2026-03-06
作者：AI Assistant
修改摘要：新增 QUERY_TYPE（sql | rag）控制 QA 搜尋行為；支援 .env.local 覆寫
更新時間：2025-12-26 18:18
作者：AI Assistant
修改摘要：修正 PORT 預設值從 8080 改為 8000，與 uvicorn 預設端口和實際運行端口保持一致
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
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import Optional

# 確保 .env 檔案在 Settings 初始化前已載入（與 care_rag 一致）
load_dotenv()
# 若存在 .env.local 則載入並覆寫 .env
if Path(".env.local").exists():
    load_dotenv(".env.local")
# 僅保留 GOOGLE_API_KEY，避免 google-genai SDK 重複印出 "Both GOOGLE_API_KEY and GEMINI_API_KEY are set..."
import os as _os
if _os.environ.get("GEMINI_API_KEY") and _os.environ.get("GOOGLE_API_KEY"):
    _os.environ.pop("GEMINI_API_KEY", None)

class Settings(BaseSettings):
    """應用程式設定"""
    
    # API 設定
    API_TITLE: str = "Care RAG API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "企業級 RAG API - REST / SSE / WebSocket"
    
    # 伺服器設定
    HOST: str = "0.0.0.0"
    PORT: int = 8000  # 預設端口 8000（與 uvicorn 預設一致）
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
    # Embedding：使用新 SDK（google.genai）時設為 true，可搭配 text-embedding-004
    USE_GOOGLE_GENAI_SDK: bool = False
    GEMINI_EMBEDDING_MODEL: Optional[str] = None  # 新 SDK 預設 text-embedding-004；舊 SDK 預設 models/embedding-001
    DEEPSEEK_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    
    # Redis 設定
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_TTL: int = 3600
    
    # Prometheus 設定
    METRICS_PORT: int = 8001
    
    # QA 查詢模式：sql=僅回傳 QA 列表；rag=以檢索結果為 context 呼叫 LLM 產出單一回答
    QUERY_TYPE: str = "sql"

    # GraphRAG 設定
    GRAPH_DB_PATH: str = "./data/graph.db"
    # 查詢含錯誤代碼 [01] 等時，用此 prefix + 數字組實體 id 從 graph 取 QA（須與建圖腳本一致，空字串則停用）
    GRAPH_IC_ERROR_QA_ENTITY_ID_PREFIX: str = "doc_thisqa_ic_error_qa_"
    VECTOR_DIMENSION: int = 768
    TOP_K_RESULTS: int = 3
    GRAPH_QUERY_MAX_ENTITIES: int = 5  # 圖查詢時最多處理的實體數量
    GRAPH_QUERY_MAX_NEIGHBORS: int = 3  # 每個實體最多查詢的鄰居數量
    GRAPH_CACHE_TTL: int = 3600  # 圖查詢快取 TTL（秒）
    # QA embedding 搜尋相似度門檻；低於此值視為無相關 QA，避免不相關查詢（如「火星探測車」）誤觸 QA 回答
    QA_MIN_SCORE: float = 0.60

    # =============================================================================
    # LINE Webhook Proxy（Service A）
    # =============================================================================
    LINE_CHANNEL_SECRET: Optional[str] = None
    LINE_WEBHOOK_REQUIRE_SIGNATURE: bool = True
    LINE_PROXY_QUERY_ENDPOINT: Optional[str] = None
    LINE_PROXY_TARGET_AUDIENCE: Optional[str] = None
    LINE_PROXY_INVOKER_SERVICE_ACCOUNT: Optional[str] = None
    LINE_PROXY_X_API_KEY: Optional[str] = None
    LINE_PROXY_TOP_K: int = 3
    LINE_PROXY_TIMEOUT_SEC: float = 30.0

    # LINE Reply API（把答案回覆到聊天室）
    LINE_REPLY_ENABLED: bool = False
    LINE_CHANNEL_ACCESS_TOKEN: Optional[str] = None

    # 僅供本機測試腳本使用（不影響雲端商用邏輯）
    LINE_WEBHOOK_TEST_BASE_URL: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


def get_query_type() -> str:
    """取得有效的 QUERY_TYPE：僅接受 sql / rag（小寫），否則 fallback sql。"""
    raw = getattr(settings, "QUERY_TYPE", "sql") or "sql"
    t = str(raw).strip().lower()
    if t not in ("sql", "rag"):
        import logging
        logging.getLogger("config").warning(
            f"QUERY_TYPE 無效: {raw!r}，fallback 為 sql。僅接受 sql 或 rag。"
        )
        return "sql"
    return t


settings = Settings()

