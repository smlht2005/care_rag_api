"""
API v1 依賴注入
"""
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
        _llm_service = LLMService()
    return _llm_service


def get_cache_service() -> CacheService:
    """取得快取服務實例"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def get_vector_service() -> VectorService:
    """取得向量服務實例"""
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorService()
    return _vector_service


def get_graph_store() -> GraphStore:
    """取得 GraphStore 實例"""
    global _graph_store
    if _graph_store is None:
        _graph_store = SQLiteGraphStore(settings.GRAPH_DB_PATH)
        # 注意：initialize() 需要在應用啟動時呼叫
    return _graph_store


def get_rag_service(
    llm: LLMService = Depends(get_llm_service),
    cache: CacheService = Depends(get_cache_service),
    vector: VectorService = Depends(get_vector_service)
) -> RAGService:
    """取得 RAG 服務實例"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService(llm, cache, vector)
    return _rag_service


def get_entity_extractor(
    llm: LLMService = Depends(get_llm_service)
) -> EntityExtractor:
    """取得實體提取器實例"""
    global _entity_extractor
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
        _orchestrator = GraphOrchestrator(rag, graph_store, cache)
    return _orchestrator

