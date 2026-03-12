"""
QA 查詢 API 端點

更新時間：2026-03-06
作者：AI Assistant
修改摘要：依 QUERY_TYPE（sql | rag）分流；rag 時以檢索結果為 context 呼叫 LLM 產出單一回答
更新時間：2026-01-13 15:20
作者：AI Assistant
修改摘要：更新標頭註解日期
更新時間：2025-12-30 11:30
作者：AI Assistant
修改摘要：建立 QA 查詢 API 端點，查詢 graph_qa.db 中的問答對
"""
import os
import logging
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from app.api.v1.schemas.qa import (
    QASearchRequest, QASearchResponse, QAResult,
    QADocumentsResponse, QADocumentInfo, QAByDocumentRequest
)
from app.core.graph_store import SQLiteGraphStore
from app.config import get_query_type
from app.api.v1.dependencies import get_llm_service
from app.services.llm_service import LLMService
from app.utils.metrics import REQUEST_COUNTER, REQUEST_LATENCY

# RAG 模式：送入 LLM 的 context 最多筆數與最大字元數（避免超出 token 上限）
RAG_CONTEXT_MAX_ITEMS = 10
RAG_CONTEXT_MAX_CHARS = 4000

router = APIRouter()
logger = logging.getLogger("QAEndpoint")

# QA 資料庫路徑
QA_DB_PATH = "./data/graph_qa.db"


def get_qa_graph_store() -> SQLiteGraphStore:
    """取得 QA GraphStore 實例"""
    db_path = os.path.abspath(QA_DB_PATH)
    if not os.path.exists(db_path):
        raise HTTPException(
            status_code=404,
            detail=f"QA database not found: {db_path}. Please import QA data first."
        )
    return SQLiteGraphStore(db_path)


@router.get("/documents", response_model=QADocumentsResponse)
async def get_qa_documents(
    request: Request,
    graph_store: SQLiteGraphStore = Depends(get_qa_graph_store)
):
    """取得所有 QA 文件列表"""
    endpoint_path = "/api/v1/qa/documents"
    method = request.method
    
    with REQUEST_LATENCY.labels(method=method, endpoint=endpoint_path).time():
        try:
            await graph_store.initialize()
            
            # 查詢所有 Document 類型的實體
            documents = await graph_store.get_entities_by_type("Document", limit=1000)
            
            # 篩選出 qa_markdown 類型的文件
            qa_documents = []
            for doc in documents:
                props = doc.properties
                if props.get("type") == "qa_markdown":
                    qa_documents.append(QADocumentInfo(
                        id=doc.id,
                        name=doc.name,
                        type=props.get("type", "qa_markdown"),
                        qa_count=props.get("qa_count", 0),
                        source=props.get("source")
                    ))
            
            REQUEST_COUNTER.labels(method=method, endpoint=endpoint_path, status="200").inc()
            
            return QADocumentsResponse(
                total=len(qa_documents),
                documents=qa_documents
            )
            
        except Exception as e:
            logger.error(f"Get QA documents error: {str(e)}")
            REQUEST_COUNTER.labels(method=method, endpoint=endpoint_path, status="500").inc()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            await graph_store.close()


def _build_rag_context(results: list, max_items: int = RAG_CONTEXT_MAX_ITEMS, max_chars: int = RAG_CONTEXT_MAX_CHARS) -> str:
    """將 QA results 格式化成「Q: … A: …」字串，限制筆數與字元數。"""
    parts = []
    total_chars = 0
    for r in results[:max_items]:
        block = f"Q: {r.question}\nA: {r.answer}\n"
        if total_chars + len(block) > max_chars:
            break
        parts.append(block)
        total_chars += len(block)
    return "\n".join(parts) if parts else ""


@router.post("/search", response_model=QASearchResponse)
async def search_qa(
    request: Request,
    search_request: QASearchRequest,
    graph_store: SQLiteGraphStore = Depends(get_qa_graph_store),
    llm_service: LLMService = Depends(get_llm_service),
):
    """搜尋 QA（依 QUERY_TYPE：sql 回傳列表，rag 回傳 LLM 單一回答 + sources）"""
    endpoint_path = "/api/v1/qa/search"
    method = request.method
    query_type = get_query_type()

    with REQUEST_LATENCY.labels(method=method, endpoint=endpoint_path).time():
        try:
            await graph_store.initialize()

            # 查詢所有 QA 實體
            all_qa = await graph_store.get_entities_by_type("QA", limit=10000)

            # 如果指定了 doc_id，先篩選
            if search_request.doc_id:
                all_qa = [qa for qa in all_qa if qa.id.startswith(f"{search_request.doc_id}_qa_")]

            # 準備查詢 token（支援多關鍵字 AND）
            raw_query = search_request.query or ""
            tokens = [t.strip().lower() for t in raw_query.split() if t.strip()]
            simple_query = raw_query.lower()

            # 搜尋匹配的 QA
            results = []

            for qa in all_qa:
                props = qa.properties

                title = props.get("qa_title") or qa.name or ""
                scenario = props.get("scenario", "")
                keywords = props.get("keywords", [])
                keywords_text = ",".join(str(k) for k in keywords) if keywords else ""
                question = props.get("question", "")
                answer = props.get("answer", "")
                notes = props.get("notes", "")

                # 組合可搜尋文本
                search_text = "\n".join([
                    str(title),
                    str(scenario),
                    keywords_text,
                    str(question),
                    str(answer),
                    str(notes),
                ]).lower()

                matched = False
                if tokens:
                    matched = all(t in search_text for t in tokens)
                else:
                    if simple_query and (
                        simple_query in question.lower()
                        or simple_query in answer.lower()
                        or any(simple_query in str(k).lower() for k in keywords)
                    ):
                        matched = True

                if matched:
                    results.append(QAResult(
                        id=qa.id,
                        qa_number=props.get("qa_number"),
                        question=question,
                        answer=answer,
                        scenario=scenario,
                        keywords=keywords,
                        steps=props.get("steps", []),
                        notes=notes,
                        metadata=props.get("metadata", {})
                    ))

            # 限制結果數量
            results = results[:search_request.limit]

            # 依 QUERY_TYPE 分流
            if query_type == "sql":
                REQUEST_COUNTER.labels(method=method, endpoint=endpoint_path, status="200").inc()
                return QASearchResponse(
                    query=search_request.query,
                    total=len(results),
                    results=results,
                    answer=None,
                )

            # RAG 模式
            if not results:
                REQUEST_COUNTER.labels(method=method, endpoint=endpoint_path, status="200").inc()
                return QASearchResponse(
                    query=search_request.query,
                    total=0,
                    results=[],
                    answer="",
                )
            context = _build_rag_context(results)
            prompt = (
                f"以下為參考 Q&A：\n{context}\n\n"
                "請根據以上內容簡要回答使用者問題，若無法從參考中回答請註明。\n\n"
                f"使用者問題：{search_request.query}"
            )
            try:
                answer_text = await llm_service.generate(prompt, max_tokens=2000)
            except Exception as e:
                logger.warning(f"RAG LLM generate failed, fallback to results only: {e}", exc_info=True)
                answer_text = None
            REQUEST_COUNTER.labels(method=method, endpoint=endpoint_path, status="200").inc()
            return QASearchResponse(
                query=search_request.query,
                total=len(results),
                results=results,
                answer=answer_text or None,
            )

        except Exception as e:
            logger.error(f"Search QA error: {str(e)}")
            REQUEST_COUNTER.labels(method=method, endpoint=endpoint_path, status="500").inc()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            await graph_store.close()


@router.post("/by-document", response_model=QASearchResponse)
async def get_qa_by_document(
    request: Request,
    doc_request: QAByDocumentRequest,
    graph_store: SQLiteGraphStore = Depends(get_qa_graph_store)
):
    """根據文件 ID 取得所有 QA"""
    endpoint_path = "/api/v1/qa/by-document"
    method = request.method
    
    with REQUEST_LATENCY.labels(method=method, endpoint=endpoint_path).time():
        try:
            await graph_store.initialize()
            
            # 驗證文件是否存在
            doc_entity = await graph_store.get_entity(doc_request.doc_id)
            if not doc_entity:
                raise HTTPException(
                    status_code=404,
                    detail=f"Document not found: {doc_request.doc_id}"
                )
            
            # 查詢該文件的所有 QA
            all_qa = await graph_store.get_entities_by_type("QA", limit=10000)
            doc_qa_list = [qa for qa in all_qa if qa.id.startswith(f"{doc_request.doc_id}_qa_")]
            
            # 轉換為 QAResult
            results = []
            for qa in doc_qa_list[:doc_request.limit]:
                props = qa.properties
                results.append(QAResult(
                    id=qa.id,
                    qa_number=props.get("qa_number"),
                    question=props.get("question", ""),
                    answer=props.get("answer", ""),
                    scenario=props.get("scenario"),
                    keywords=props.get("keywords", []),
                    steps=props.get("steps", []),
                    notes=props.get("notes"),
                    metadata=props.get("metadata", {})
                ))
            
            REQUEST_COUNTER.labels(method=method, endpoint=endpoint_path, status="200").inc()
            
            return QASearchResponse(
                query=f"Document: {doc_request.doc_id}",
                total=len(results),
                results=results
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get QA by document error: {str(e)}")
            REQUEST_COUNTER.labels(method=method, endpoint=endpoint_path, status="500").inc()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            await graph_store.close()


@router.get("/search", response_model=QASearchResponse)
async def search_qa_get(
    request: Request,
    query: str = Query(..., description="搜尋關鍵詞", min_length=1, max_length=200),
    limit: int = Query(10, description="返回結果數量", ge=1, le=50),
    doc_id: str = Query(None, description="限制搜尋特定文件 ID"),
    graph_store: SQLiteGraphStore = Depends(get_qa_graph_store)
):
    """搜尋 QA (GET 方法)"""
    search_request = QASearchRequest(query=query, limit=limit, doc_id=doc_id)
    return await search_qa(request, search_request, graph_store)
