"""
WebSocket 端點（獨立檔案）
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.orchestrator import GraphOrchestrator
from app.services.llm_service import LLMService
from app.services.cache_service import CacheService
from app.services.rag_service import RAGService
from app.services.vector_service import VectorService
import asyncio
import logging

router = APIRouter()
logger = logging.getLogger("WebSocketEndpoint")

# 初始化服務
llm_service = LLMService()
cache_service = CacheService()
vector_service = VectorService()
rag_service = RAGService(llm_service, cache_service, vector_service)
orchestrator = GraphOrchestrator(rag_service)

@router.websocket("/ws/query")
async def websocket_query(websocket: WebSocket):
    """WebSocket 查詢端點"""
    await websocket.accept()
    logger.info("WebSocket query connection established")
    
    try:
        while True:
            # 接收查詢請求
            data = await websocket.receive_json()
            query_text = data.get("query", "")
            
            if not query_text:
                await websocket.send_json({
                    "error": "Query is required",
                    "type": "error"
                })
                continue
            
            # 發送開始訊息
            await websocket.send_json({
                "type": "start",
                "query": query_text
            })
            
            # 執行串流查詢
            index = 0
            async for chunk in orchestrator.stream_query(query_text):
                await websocket.send_json({
                    "type": "chunk",
                    "chunk": chunk,
                    "index": index,
                    "done": False
                })
                index += 1
                await asyncio.sleep(0.1)
            
            # 發送完成訊息
            await websocket.send_json({
                "type": "done",
                "index": index,
                "done": True
            })
            
    except WebSocketDisconnect:
        logger.info("WebSocket query connection closed")
    except Exception as e:
        logger.error(f"WebSocket query error: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "error": str(e)
        })
    finally:
        await websocket.close()


