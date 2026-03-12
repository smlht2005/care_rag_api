"""
Orchestrator 單次 LLM 修復驗證：有 graph_store 時只呼叫 retrieve + 一次 generate_answer_from_sources；無 graph_store 時只呼叫 query。
更新時間：2026-03-11
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.orchestrator import GraphOrchestrator, GraphEnhancementResult


@pytest.mark.asyncio
async def test_with_graph_store_calls_retrieve_once_and_generate_once_not_query():
    """有 graph_store 時：retrieve 1 次、generate_answer_from_sources 1 次、query 0 次。"""
    rag = MagicMock()
    rag.retrieve = AsyncMock(
        return_value={
            "sources": [{"id": "v1", "content": "vector source", "score": 0.8}],
            "query": "test query",
        }
    )
    rag.query = AsyncMock(
        return_value={"answer": "from query", "sources": [], "query": "test query"}
    )
    rag.generate_answer_from_sources = AsyncMock(return_value="final answer")

    graph_store = MagicMock()
    cache = None
    orchestrator = GraphOrchestrator(rag_service=rag, graph_store=graph_store, cache_service=cache)

    graph_sources = [{"id": "g1", "content": "graph source", "score": 0.9}]
    enhancement = GraphEnhancementResult(
        sources=graph_sources,
        entities=[],
        relations=[],
    )

    with patch.object(orchestrator, "_enhance_with_graph", new_callable=AsyncMock, return_value=enhancement):
        result = await orchestrator.query("test query", top_k=3, skip_cache=True)

    assert result.get("answer") == "final answer"
    rag.retrieve.assert_called_once()
    rag.retrieve.assert_awaited_once_with("test query", top_k=3)
    rag.query.assert_not_called()
    rag.generate_answer_from_sources.assert_called_once()
    call_args = rag.generate_answer_from_sources.call_args
    assert call_args[0][1] == "test query"
    sources_passed = call_args[0][0]
    assert len(sources_passed) >= 1
    ids = [s.get("id") for s in sources_passed]
    assert "g1" in ids or "v1" in ids


@pytest.mark.asyncio
async def test_without_graph_store_calls_query_once_not_retrieve_nor_generate():
    """無 graph_store 時：query 1 次、retrieve 0 次、generate_answer_from_sources 0 次。"""
    rag = MagicMock()
    rag.retrieve = AsyncMock(return_value={"sources": [], "query": "q"})
    rag.query = AsyncMock(
        return_value={
            "answer": "only answer",
            "sources": [{"id": "s1", "content": "c1"}],
            "query": "test query",
        }
    )
    rag.generate_answer_from_sources = AsyncMock(return_value="never used")

    orchestrator = GraphOrchestrator(rag_service=rag, graph_store=None, cache_service=None)

    result = await orchestrator.query("test query", top_k=3, skip_cache=True)

    assert result.get("answer") == "only answer"
    rag.query.assert_called_once()
    rag.query.assert_awaited_once_with("test query", top_k=3, skip_cache=True)
    rag.retrieve.assert_not_called()
    rag.generate_answer_from_sources.assert_not_called()
