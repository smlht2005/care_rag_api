"""
單例 TOCTOU 修復驗證：多執行緒同時首次呼叫 get_* 時僅建立一個實例。
更新時間：2026-03-11
"""
import threading
import pytest

# 測試前重置單例，以重現「並發首次建立」
import app.api.v1.dependencies as deps


def test_singleton_llm_service_under_concurrent_first_calls():
    """多執行緒同時首次呼叫 get_llm_service() 時，所有執行緒取得同一實例。"""
    deps._llm_service = None
    results = []
    n = 10

    def get_once():
        svc = deps.get_llm_service()
        results.append(svc)

    threads = [threading.Thread(target=get_once) for _ in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == n
    ids = {id(r) for r in results}
    assert len(ids) == 1, "expected single LLMService instance under concurrent first calls"
