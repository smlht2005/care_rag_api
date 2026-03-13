"""
StubEmbeddingService determinism 測試：
同一輸入多次呼叫應得到完全相同的向量，不受 Python hash randomization 影響。
更新時間：2026-03-11
"""
import asyncio
import pytest
from app.services.embedding_service import StubEmbeddingService


def test_stub_embedding_same_text_same_vector_multiple_calls():
    """同一文字多次 embed 應回傳完全相同向量。"""
    svc = StubEmbeddingService(dim=64)
    texts = ["IC卡 D12 錯誤", "hello world", ""]
    for text in texts:
        r1 = asyncio.run(svc.embed([text]))
        r2 = asyncio.run(svc.embed([text]))
        assert r1 == r2, f"向量不一致：{text!r}"


def test_stub_embedding_different_texts_different_vectors():
    """不同文字應回傳不同向量。"""
    svc = StubEmbeddingService(dim=64)
    r1 = asyncio.run(svc.embed(["text_a"]))
    r2 = asyncio.run(svc.embed(["text_b"]))
    assert r1 != r2


def test_stub_embedding_vector_length():
    """向量長度應符合設定的 dim。"""
    svc = StubEmbeddingService(dim=32)
    result = asyncio.run(svc.embed(["test"]))
    assert len(result) == 1
    assert len(result[0]) == 32


def test_stub_embedding_empty_text_does_not_crash():
    """空字串也應正常產生向量，不崩潰。"""
    svc = StubEmbeddingService(dim=16)
    result = asyncio.run(svc.embed([""]))
    assert len(result) == 1
    assert len(result[0]) == 16
