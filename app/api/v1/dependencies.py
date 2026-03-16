"""
API v1 依賴注入
更新時間：2026-03-11
作者：AI Assistant
修改摘要：單例建立加 threading.Lock 消除 TOCTOU 競態，避免多請求同時首次呼叫時重複建立實例
更新時間：2026-03-11
作者：AI Assistant
修改摘要：單例建立加 threading.Lock 消除 TOCTOU 競態，避免多請求同時首次呼叫時重複建立實例
"""
import threading
import threading
from fastapi import Depends
from app.services.llm_service import LLMService
from app.services.cache_service import CacheService
from app.services.vector_service import VectorService
from app.services.rag_service import RAGService
from app.core.graph_store import GraphStore, SQLiteGraphStore
from app.core.entity_extractor import EntityExtractor
from app.core.orchestrator import GraphOrchestrator
from app.services.graph_builder import GraphBuilder
from app.config import settings

# 單例建立鎖（消除 TOCTOU：檢查 None 與賦值之間僅允許一執行緒）
_init_lock = threading.Lock()

# 單例建立鎖（消除 TOCTOU：檢查 None 與賦值之間僅允許一執行緒）
_init_lock = threading.Lock()

# 服務實例（單例模式）
_llm_service: LLMService = None
_cache_service: CacheService = None
_vector_service: VectorService = None
_rag_service: RAGService = None
_graph_store: GraphStore = None
_entity_extractor: EntityExtractor = None
_graph_builder: GraphBuilder = None
_orchestrator: GraphOrchestrator = None


def get_llm_service() -> LLMService:
    """取得 LLM 服務實例"""
    global _llm_service
    if _llm_service is None:
        with _init_lock:
            if _llm_service is None:
                _llm_service = LLMService()
    if _llm_service is None:
        with _init_lock:
            if _llm_service is None:
                _llm_service = LLMService()
    return _llm_service


def get_cache_service() -> CacheService:
    """取得快取服務實例"""
    global _cache_service
    if _cache_service is None:
        with _init_lock:
            if _cache_service is None:
                _cache_service = CacheService()
    return _cache_service


def get_vector_service(
    graph_store: GraphStore = Depends(get_graph_store)
) -> VectorService:
    """取得向量服務實例；graph_store 由 FastAPI 依賴注入，可覆寫。"""
    global _vector_service
    if _vector_service is None:
        with _init_lock:
            if _vector_service is None:
                _vector_service = VectorService(graph_store=graph_store)
    return _vector_service


def get_graph_store() -> GraphStore:
    """取得 GraphStore 實例"""
    global _graph_store
    if _graph_store is None:
        with _init_lock:
            if _graph_store is None:
                _graph_store = SQLiteGraphStore(settings.GRAPH_DB_PATH)
        # 注意：initialize() 需要在應用啟動時呼叫
    return _graph_store


def get_vector_service(
    graph_store: GraphStore = Depends(get_graph_store)
) -> VectorService:
    """取得向量服務實例；graph_store 由 FastAPI 依賴注入，可覆寫。"""
    global _vector_service
    if _vector_service is None:
        with _init_lock:
            if _vector_service is None:
                _vector_service = VectorService(graph_store=graph_store)
    return _vector_service
 
 
def get_rag_service(
    llm: LLMService = Depends(get_llm_service),
    cache: CacheService = Depends(get_cache_service),
    vector: VectorService = Depends(get_vector_service)
) -> RAGService:
    """取得 RAG 服務實例"""
    global _rag_service
    if _rag_service is None:
        with _init_lock:
            if _rag_service is None:
                _rag_service = RAGService(llm, cache, vector)
    if _rag_service is None:
        with _init_lock:
            if _rag_service is None:
                _rag_service = RAGService(llm, cache, vector)
    return _rag_service


def get_entity_extractor(
    llm: LLMService = Depends(get_llm_service)
) -> EntityExtractor:
    """取得實體提取器實例"""
    global _entity_extractor
    if _entity_extractor is None:
        with _init_lock:
            if _entity_extractor is None:
        with _init_lock:
            if _entity_extractor is None:
                        _entity_extractor = EntityExtractor(llm)
    return _entity_extractor


def get_graph_builder(
    graph_store: GraphStore = Depends(get_graph_store),
    entity_extractor: EntityExtractor = Depends(get_entity_extractor)
) -> GraphBuilder:
    """取得圖構建服務實例"""
    global _graph_builder
    if _graph_builder is None:
        with _init_lock:
            if _graph_builder is None:
                _graph_builder = GraphBuilder(graph_store, entity_extractor)
    if _graph_builder is None:
        with _init_lock:
            if _graph_builder is None:
                _graph_builder = GraphBuilder(graph_store, entity_extractor)
    return _graph_builder


def get_orchestrator(
    rag: RAGService = Depends(get_rag_service),
    graph_store: GraphStore = Depends(get_graph_store),
    cache: CacheService = Depends(get_cache_service)
) -> GraphOrchestrator:
    """取得 GraphOrchestrator 實例"""
    global _orchestrator
    if _orchestrator is None:
        with _init_lock:
            if _orchestrator is None:
                _orchestrator = GraphOrchestrator(rag, graph_store, cache)
    if _orchestrator is None:
        with _init_lock:
            if _orchestrator is None:
                _orchestrator = GraphOrchestrator(rag, graph_store, cache)
    return _orchestrator

