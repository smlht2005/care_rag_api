"""
VectorService IC QA guard 測試：
當 query 不具備「IC 上下文 + 明確代碼」時，應避免 QA embedding 命中 IC error/field QA 造成誤匹配。

更新時間：2026-04-23 16:15
作者：AI Assistant
修改摘要：新增 IC QA guard 測試並涵蓋 alias 正規化（IC錯誤01 / IC 01 改寫為 IC卡 [01]）
"""

import pytest

from app.services.vector_service import VectorService


class _FakeEntity:
    def __init__(self, entity_id: str, question: str, answer: str, code: str, *, entity_type: str = "QA1"):
        self.id = entity_id
        self.type = entity_type
        self.name = entity_id
        self.properties = {"question": question, "answer": answer, "code": code}


class _FakeGraphStore:
    async def get_entity(self, entity_id: str):
        # 回傳固定 entity（符合 VectorService 取 properties.question/answer 的需求）
        if entity_id == "doc_thisqa_ic_error_qa_16":
            return _FakeEntity(
                entity_id,
                "IC 卡資料上傳錯誤代碼 [16] 代表什麼？",
                "處方簽章驗證不通過",
                "16",
            )
        if entity_id == "doc_thisqa_ic_error_qa_01":
            return _FakeEntity(
                entity_id,
                "IC 卡資料上傳錯誤代碼 [01] 代表什麼？",
                "資料型態檢核錯誤",
                "01",
            )
        return None


class _FakeEmbedding:
    async def embed(self, texts):
        # 回傳非空向量即可；QAEmbeddingIndex.search 會被 mock，不會用到數值
        return [[0.1, 0.2, 0.3] for _ in texts]


@pytest.mark.asyncio
async def test_non_ic_query_filters_ic_error_qa_from_embedding_hits(monkeypatch):
    """
    non-IC query（沒有 IC 上下文 + 代碼）即使 embedding hit 是 IC error QA，也必須被過濾掉。
    """
    svc = VectorService(graph_store=_FakeGraphStore())
    monkeypatch.setattr(svc, "_embedding", _FakeEmbedding())
    monkeypatch.setattr(
        svc._qa_index,
        "search",
        lambda query_emb, top_k, min_score: [("doc_thisqa_ic_error_qa_16", 0.74, {})],
    )

    results = await svc._search_from_qa_embeddings("無法成功讀卡,出現多筆處方箋寫入作業-回傳簽章", top_k=3)
    assert results == [], "non-IC query 應過濾掉 ic_error_qa 命中，避免誤匹配"


@pytest.mark.asyncio
async def test_ic_query_with_code_allows_ic_error_qa_embedding_hit(monkeypatch):
    """
    IC + 代碼 query 仍允許命中 ic_error_qa（方案 C 放行條件）。
    """
    svc = VectorService(graph_store=_FakeGraphStore())
    monkeypatch.setattr(svc, "_embedding", _FakeEmbedding())
    monkeypatch.setattr(
        svc._qa_index,
        "search",
        lambda query_emb, top_k, min_score: [("doc_thisqa_ic_error_qa_16", 0.74, {})],
    )

    results = await svc._search_from_qa_embeddings("IC卡 [16] 代表什麼？", top_k=3)
    assert len(results) == 1
    assert results[0]["id"] == "doc_thisqa_ic_error_qa_16"
    assert "處方簽章驗證不通過" in (results[0].get("content") or "")


@pytest.mark.asyncio
async def test_ic_alias_mapping_allows_ic_error_code_query(monkeypatch):
    """
    alias 正規化：IC錯誤01 / IC 01 應改寫為 IC卡 [01]，讓守衛放行並命中 doc_thisqa_ic_error_qa_01。
    """
    svc = VectorService(graph_store=_FakeGraphStore())
    monkeypatch.setattr(svc, "_embedding", _FakeEmbedding())
    monkeypatch.setattr(
        svc._qa_index,
        "search",
        lambda query_emb, top_k, min_score: [("doc_thisqa_ic_error_qa_01", 0.80, {})],
    )

    r1 = await svc.search("IC錯誤01", top_k=3)
    assert r1 and r1[0]["id"] == "doc_thisqa_ic_error_qa_01"
    assert "資料型態檢核錯誤" in (r1[0].get("content") or "")

    r2 = await svc.search("IC 01", top_k=3)
    assert r2 and r2[0]["id"] == "doc_thisqa_ic_error_qa_01"

