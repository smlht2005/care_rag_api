"""
skip_cache 行為測試：
- RAGService: skip_cache=True 不讀不寫快取；skip_cache=False 讀寫快取。
- GraphOrchestrator: skip_cache=True 不讀不寫快取；skip_cache=False 讀寫快取。
更新時間：2026-03-11
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.rag_service import RAGService, NO_MATCH_MESSAGE
from app.core.orchestrator import GraphOrchestrator, GraphEnhancementResult


# --- RAGService skip_cache 測試 ---

@pytest.mark.asyncio
async def test_rag_service_skip_cache_true_does_not_read_or_write_cache():
    """skip_cache=True 時不讀取、不寫入快取。"""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()

    vector = MagicMock()
    vector.search = AsyncMock(return_value=[])

    llm = MagicMock()
    llm.generate = AsyncMock(return_value="answer")

    svc = RAGService(llm_service=llm, cache_service=cache, vector_service=vector)
    await svc.query("test", top_k=3, skip_cache=True)

    cache.get.assert_not_called()
    cache.set.assert_not_called()


@pytest.mark.asyncio
async def test_rag_service_skip_cache_false_reads_and_writes_cache():
    """skip_cache=False 且快取未命中時，完成查詢後寫入快取。"""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()

    vector = MagicMock()
    vector.search = AsyncMock(return_value=[])

    llm = MagicMock()
    llm.generate = AsyncMock(return_value="answer")

    svc = RAGService(llm_service=llm, cache_service=cache, vector_service=vector)
    await svc.query("test", top_k=3, skip_cache=False)

    cache.get.assert_called_once()
    cache.set.assert_called_once()


@pytest.mark.asyncio
async def test_rag_service_skip_cache_false_returns_cached_result_without_llm():
    """skip_cache=False 且快取命中時，直接回傳快取結果，不呼叫 LLM 或向量檢索。"""
    cached_result = {"answer": "cached", "sources": [], "query": "test"}
    cache = MagicMock()
    cache.get = AsyncMock(return_value=cached_result)
    cache.set = AsyncMock()

    vector = MagicMock()
    vector.search = AsyncMock()

    llm = MagicMock()
    llm.generate = AsyncMock()

    svc = RAGService(llm_service=llm, cache_service=cache, vector_service=vector)
    result = await svc.query("test", top_k=3, skip_cache=False)

    assert result["answer"] == "cached"
    vector.search.assert_not_called()
    llm.generate.assert_not_called()
    cache.set.assert_not_called()


# --- GraphOrchestrator skip_cache 測試 ---

@pytest.mark.asyncio
async def test_orchestrator_skip_cache_true_does_not_read_or_write_cache():
    """skip_cache=True 時 orchestrator 層快取不讀不寫。"""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()

    rag = MagicMock()
    rag.query = AsyncMock(return_value={"answer": "ok", "sources": [], "query": "q"})

    orch = GraphOrchestrator(rag_service=rag, graph_store=None, cache_service=cache)
    await orch.query("q", top_k=3, skip_cache=True)

    cache.get.assert_not_called()
    cache.set.assert_not_called()


@pytest.mark.asyncio
async def test_orchestrator_skip_cache_false_reads_and_writes_cache():
    """skip_cache=False 且快取未命中時，完成後寫入 orchestrator 快取。"""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()

    rag = MagicMock()
    rag.query = AsyncMock(return_value={"answer": "ok", "sources": [], "query": "q"})

    orch = GraphOrchestrator(rag_service=rag, graph_store=None, cache_service=cache)
    await orch.query("q", top_k=3, skip_cache=False)

    cache.get.assert_called_once()
    cache.set.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrator_skip_cache_false_returns_cached_result():
    """skip_cache=False 且快取命中時，直接回傳快取結果，不呼叫 rag.query。"""
    cached_result = {"answer": "from_cache", "sources": [], "query": "q"}
    cache = MagicMock()
    cache.get = AsyncMock(return_value=cached_result)
    cache.set = AsyncMock()

    rag = MagicMock()
    rag.query = AsyncMock()

    orch = GraphOrchestrator(rag_service=rag, graph_store=None, cache_service=cache)
    result = await orch.query("q", top_k=3, skip_cache=False)

    assert result["answer"] == "from_cache"
    rag.query.assert_not_called()
    cache.set.assert_not_called()
