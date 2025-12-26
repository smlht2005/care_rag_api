"""
查詢 API 端點（REST + SSE + WebSocket）
更新時間：2025-12-26 17:52
作者：AI Assistant
修改摘要：修正 Prometheus 指標標籤缺失問題，添加 method、endpoint、status 標籤
"""
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from app.core.orchestrator import GraphOrchestrator
from app.api.v1.schemas.query import QueryRequest, QueryResponse, StreamChunk
from app.api.v1.dependencies import get_orchestrator
from app.utils.metrics import REQUEST_COUNTER, REQUEST_LATENCY
import asyncio
import logging

router = APIRouter()
logger = logging.getLogger("QueryEndpoint")

@router.post("/query", response_model=QueryResponse)
async def query_endpoint(
    request: Request,
    query_request: QueryRequest,
    orchestrator: GraphOrchestrator = Depends(get_orchestrator)
):
    """REST 查詢端點"""
    endpoint_path = "/api/v1/query"
    method = request.method
    
    with REQUEST_LATENCY.labels(method=method, endpoint=endpoint_path).time():
        try:
            # 執行查詢
            result = await orchestrator.query(
                query_request.query,
                top_k=query_request.top_k or 3
            )
            
            response = QueryResponse(
                answer=result["answer"],
                sources=result.get("sources", []),
                query=result.get("query", query_request.query),
                provider=query_request.provider
            )
            
            # 記錄成功指標
            REQUEST_COUNTER.labels(method=method, endpoint=endpoint_path, status="200").inc()
            
            return JSONResponse(content=response.model_dump())
            
        except Exception as e:
            logger.error(f"Query endpoint error: {str(e)}")
            # 記錄錯誤指標
            REQUEST_COUNTER.labels(method=method, endpoint=endpoint_path, status="500").inc()
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "detail": str(e)}
            )

@router.get("/query/stream")
async def query_stream(
    query: str = Query(..., min_length=1, max_length=1000, description="查詢問題"),
    orchestrator: GraphOrchestrator = Depends(get_orchestrator)
):
    """
    SSE 串流查詢端點
    
    Args:
        query: 查詢問題（1-1000 字元）
    """
    async def event_generator():
        try:
            async for chunk in orchestrator.stream_query(query):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Stream query error: {str(e)}")
            yield f"data: Error: {str(e)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )

@router.websocket("/ws/chat")
async def websocket_endpoint(
    websocket: WebSocket,
    orchestrator: GraphOrchestrator = Depends(get_orchestrator)
):
    """WebSocket 聊天端點"""
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    try:
        while True:
            # 接收訊息
            data = await websocket.receive_json()
            query_text = data.get("query", "")
            
            if not query_text:
                await websocket.send_json({
                    "error": "Query is required"
                })
                continue
            
            # 執行串流查詢
            index = 0
            async for chunk in orchestrator.stream_query(query_text):
                await websocket.send_json({
                    "chunk": chunk,
                    "index": index,
                    "done": False
                })
                index += 1
                await asyncio.sleep(0.1)
            
            # 發送完成訊息
            await websocket.send_json({
                "chunk": "",
                "index": index,
                "done": True
            })
            
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.send_json({
            "error": str(e)
        })
    finally:
        await websocket.close()
