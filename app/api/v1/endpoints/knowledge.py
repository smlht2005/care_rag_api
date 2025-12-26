"""
知識庫 API 端點
更新時間：2025-12-26 18:12
作者：AI Assistant
修改摘要：實作 get_knowledge_sources 端點，從 GraphStore 獲取所有 Document 實體作為知識來源
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from app.core.orchestrator import GraphOrchestrator
from app.services.graph_builder import GraphBuilder
from app.services.vector_service import VectorService
from app.core.graph_store import GraphStore
from app.api.v1.schemas.knowledge import (
    KnowledgeQueryRequest,
    KnowledgeQueryResponse,
    KnowledgeSourceResponse,
    KnowledgeIngestRequest,
    KnowledgeIngestResponse
)
from app.api.v1.dependencies import (
    get_orchestrator,
    get_graph_builder,
    get_vector_service,
    get_graph_store
)
from app.core.graph_store import GraphStore
from app.utils.metrics import REQUEST_COUNTER, REQUEST_LATENCY
import logging
import uuid
from datetime import datetime

router = APIRouter()
logger = logging.getLogger("KnowledgeEndpoint")

@router.post("/query", response_model=KnowledgeQueryResponse)
async def knowledge_query(
    request: Request,
    query_request: KnowledgeQueryRequest,
    orchestrator: GraphOrchestrator = Depends(get_orchestrator)
):
    """知識庫查詢端點"""
    with REQUEST_LATENCY.labels(method="POST", endpoint="/api/v1/knowledge/query").time():
        REQUEST_COUNTER.labels(method="POST", endpoint="/api/v1/knowledge/query", status="200").inc()
        
        try:
            # 執行 GraphRAG 查詢
            result = await orchestrator.query(
                query_request.query,
                top_k=query_request.top_k or 3
            )
            
            response = KnowledgeQueryResponse(
                answer=result.get("answer", ""),
                sources=result.get("sources", []),
                graph_entities=result.get("graph_entities", []) if query_request.include_graph else [],
                graph_relations=result.get("graph_relations", []) if query_request.include_graph else [],
                query=result.get("query", query_request.query)
            )
            
            return JSONResponse(content=response.model_dump())
            
        except Exception as e:
            logger.error(f"Knowledge query error: {str(e)}")
            REQUEST_COUNTER.labels(method="POST", endpoint="/api/v1/knowledge/query", status="500").inc()
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "detail": str(e)}
            )

@router.get("/sources", response_model=KnowledgeSourceResponse)
async def get_knowledge_sources(
    request: Request,
    graph_store: GraphStore = Depends(get_graph_store)
):
    """取得知識來源列表"""
    try:
        # 從 GraphStore 獲取所有 Document 類型的實體
        document_entities = await graph_store.get_entities_by_type("Document", limit=1000)
        
        # 從 Document 實體中提取來源資訊
        sources = []
        seen_sources = set()  # 用於去重
        
        for entity in document_entities:
            # 從 properties 中獲取 source
            source = entity.properties.get("source", "")
            
            # 如果 source 為空，嘗試使用 entity.name 或 entity.id
            if not source:
                # 檢查是否是 PDF 文件名格式
                if entity.name and (entity.name.endswith(".pdf") or "pdf" in entity.name.lower()):
                    source = entity.name
                else:
                    # 使用 entity ID 作為備用
                    source = entity.id
            
            # 去重：只添加唯一的 source
            if source and source not in seen_sources:
                seen_sources.add(source)
                sources.append({
                    "id": entity.id,
                    "name": entity.name,
                    "source": source,
                    "type": entity.type,
                    "created_at": entity.created_at.isoformat() if entity.created_at else None,
                    "metadata": entity.properties
                })
        
        response = KnowledgeSourceResponse(
            sources=sources,
            total=len(sources)
        )
        
        return JSONResponse(content=response.model_dump(mode='json'))
        
    except Exception as e:
        logger.error(f"Get knowledge sources error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(e)}
        )

@router.post("/ingest", response_model=KnowledgeIngestResponse)
async def ingest_knowledge(
    request: Request,
    ingest_request: KnowledgeIngestRequest,
    graph_builder: GraphBuilder = Depends(get_graph_builder),
    vector_service: VectorService = Depends(get_vector_service)
):
    """知識庫攝取端點"""
    try:
        # 生成文件 ID（使用完整 UUID 避免碰撞）
        document_id = f"doc_{str(uuid.uuid4())}"
        
        # 1. 構建圖結構
        graph_result = await graph_builder.build_graph_from_text(
            ingest_request.content,
            document_id,
            entity_types=ingest_request.entity_types
        )
        
        # 2. 新增到向量資料庫
        await vector_service.add_documents([{
            "id": document_id,
            "content": ingest_request.content,
            "metadata": ingest_request.metadata or {},
            "source": ingest_request.source or "api"
        }])
        
        response = KnowledgeIngestResponse(
            document_id=document_id,
            entities_count=graph_result.get("entities_count", 0),
            relations_count=graph_result.get("relations_count", 0),
            status="success",
            created_at=datetime.now()
        )
        
        logger.info(
            f"Knowledge ingested: document_id={document_id}, "
            f"entities={graph_result.get('entities_count', 0)}, "
            f"relations={graph_result.get('relations_count', 0)}"
        )
        
        return JSONResponse(content=response.model_dump(mode='json'))
        
    except Exception as e:
        logger.error(f"Knowledge ingest error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(e)}
        )

