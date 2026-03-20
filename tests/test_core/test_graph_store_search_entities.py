"""
GraphStore.search_entities 之 include_type_match 行為測試
更新時間：2026-03-20 12:10
作者：AI Assistant
修改摘要：驗證 include_type_match=False 時不因 type=Organization 等 schema 類名而命中（missfind 假陽性）
"""
import pytest

from app.core.graph_store import Entity, MemoryGraphStore


@pytest.mark.asyncio
async def test_search_entities_organization_token_hits_type_when_match_enabled():
    """英文 Organization 與 type=Organization 匹配時，預設（include_type_match=True）會命中。"""
    store = MemoryGraphStore()
    await store.initialize()
    await store.add_entity(
        Entity(id="e1", type="Organization", name="批價管理系統", properties={})
    )
    hits = await store.search_entities("Organization", limit=10, include_type_match=True)
    assert len(hits) == 1
    assert hits[0].id == "e1"


@pytest.mark.asyncio
async def test_search_entities_organization_token_skips_type_when_match_disabled():
    """include_type_match=False 時僅比對 name；name 不含 Organization 則零命中。"""
    store = MemoryGraphStore()
    await store.initialize()
    await store.add_entity(
        Entity(id="e1", type="Organization", name="批價管理系統", properties={})
    )
    hits = await store.search_entities("Organization", limit=10, include_type_match=False)
    assert hits == []


@pytest.mark.asyncio
async def test_search_entities_name_only_still_finds_substring_in_name():
    """name 子字串仍可在 include_type_match=False 時命中。"""
    store = MemoryGraphStore()
    await store.initialize()
    await store.add_entity(
        Entity(id="e2", type="Concept", name="批價管理系統操作", properties={})
    )
    hits = await store.search_entities("批價", limit=10, include_type_match=False)
    assert len(hits) == 1
    assert hits[0].id == "e2"
