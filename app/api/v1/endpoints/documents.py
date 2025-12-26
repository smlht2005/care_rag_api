"""
文件管理 API 端點
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from app.services.vector_service import VectorService
from app.services.background_tasks import BackgroundTaskService
from app.services.graph_builder import GraphBuilder
from app.api.v1.dependencies import get_vector_service, get_graph_builder
from app.api.v1.schemas.document import (
    DocumentRequest,
    DocumentResponse,
    DocumentListRequest,
    DocumentListResponse
)
from app.api.v1.schemas.common import SuccessResponse
import logging
from datetime import datetime
import uuid

router = APIRouter()
logger = logging.getLogger("DocumentsEndpoint")

background_tasks = BackgroundTaskService()

@router.post("/documents", response_model=DocumentResponse)
async def add_document(
    request: Request,
    doc_request: DocumentRequest,
    vector_service: VectorService = Depends(get_vector_service),
    graph_builder: GraphBuilder = Depends(get_graph_builder)
):
    """新增單一文件"""
    try:
        document_id = str(uuid.uuid4())
        
        # 新增文件到向量資料庫
        result = await vector_service.add_documents([{
            "id": document_id,
            "content": doc_request.content,
            "metadata": doc_request.metadata or {},
            "source": doc_request.source
        }])
        
        # 構建圖結構
        try:
            await graph_builder.build_graph_from_text(
                doc_request.content,
                document_id
            )
            logger.info(f"Graph built for document: {document_id}")
        except Exception as graph_error:
            logger.warning(f"Failed to build graph for document {document_id}: {str(graph_error)}")
            # 不影響文件新增，只記錄警告
        
        response = DocumentResponse(
            id=document_id,
            content=doc_request.content,
            metadata=doc_request.metadata,
            source=doc_request.source,
            created_at=datetime.now().isoformat()
        )
        
        return JSONResponse(content=response.model_dump())
        
    except Exception as e:
        logger.error(f"Add document error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to add document", "detail": str(e)}
        )

@router.post("/documents/batch", response_model=DocumentListResponse)
async def add_documents_batch(request: Request, docs_request: DocumentListRequest):
    """批量新增文件"""
    try:
        documents = [
            {
                "id": str(uuid.uuid4()),
                "content": doc.content,
                "metadata": doc.metadata or {},
                "source": doc.source
            }
            for doc in docs_request.documents
        ]
        
        # 使用背景任務處理
        await background_tasks.process_documents(documents)
        
        document_ids = [doc["id"] for doc in documents]
        
        response = DocumentListResponse(
            status="success",
            count=len(documents),
            document_ids=document_ids
        )
        
        return JSONResponse(content=response.model_dump())
        
    except Exception as e:
        logger.error(f"Batch add documents error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to add documents", "detail": str(e)}
        )

@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """刪除文件"""
    try:
        result = await vector_service.delete_documents([document_id])
        
        return SuccessResponse(
            success=True,
            message=f"Document {document_id} deleted",
            data=result
        )
        
    except Exception as e:
        logger.error(f"Delete document error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to delete document", "detail": str(e)}
        )

