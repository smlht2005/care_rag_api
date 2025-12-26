"""
Care RAG API 主應用程式
更新時間：2025-12-26 16:50
作者：AI Assistant
修改摘要：修復 Ctrl+C 無法停止服務的問題，正確處理 CancelledError 和設置超時
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.core.logging import setup_logging
from app.utils.metrics import init_metrics_server
from app.api.v1.router import router

# 設定日誌
logger = setup_logging("INFO" if not settings.DEBUG else "DEBUG")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    # 啟動階段
    logger.info("Care RAG API starting up...")
    
    # 初始化 Prometheus 指標伺服器
    try:
        init_metrics_server()
        logger.info("Metrics server initialized")
    except Exception as e:
        logger.warning(f"Metrics server initialization failed: {str(e)}")
    
    # 初始化 GraphStore
    graph_store = None
    try:
        from app.api.v1.dependencies import get_graph_store
        graph_store = get_graph_store()
        await graph_store.initialize()
        logger.info("GraphStore initialized")
    except Exception as e:
        logger.warning(f"GraphStore initialization failed: {str(e)}")
    
    logger.info(f"Care RAG API started on {settings.HOST}:{settings.PORT}")
    
    try:
        yield  # 應用程式運行階段
    finally:
        # 關閉階段（確保在異常情況下也能執行）
        logger.info("Care RAG API shutting down...")
        
        # 清理 GraphStore 連接（設置超時避免阻塞）
        if graph_store:
            try:
                if hasattr(graph_store, 'close'):
                    # 設置 2 秒超時，避免關閉操作阻塞 Ctrl+C
                    try:
                        await asyncio.wait_for(
                            graph_store.close(),
                            timeout=2.0
                        )
                        logger.info("GraphStore closed")
                    except asyncio.TimeoutError:
                        logger.warning("GraphStore close timeout, forcing shutdown")
                    except asyncio.CancelledError:
                        # 如果被取消，記錄但不阻止退出
                        logger.info("GraphStore close cancelled, continuing shutdown")
                        raise  # 重新拋出 CancelledError，讓上層處理
            except asyncio.CancelledError:
                # 捕獲 CancelledError 並重新拋出，確保能正確退出
                logger.info("Shutdown cancelled by user (Ctrl+C)")
                raise
            except Exception as e:
                logger.warning(f"Error closing GraphStore: {str(e)}")
        
        logger.info("Care RAG API shutdown complete")

# 建立 FastAPI 應用程式
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# 註冊 API 路由
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    """根端點"""
    return {
        "message": "Care RAG API is running!",
        "version": settings.API_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health"
    }

@app.get("/docs-redirect")
async def docs_redirect():
    """API 文檔重定向"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")
