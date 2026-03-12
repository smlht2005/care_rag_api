"""
Refactor 後完整測試 runner：依序執行 Stub 檢查、Gemini LLM、整合測試、pytest API。
不含啟動 API 與 E2E（E2E 需手動啟動 API 後執行 scripts/test_graph_llm_qa.py）。
執行方式：在 care_rag_api 根目錄執行 python -m scripts.run_full_test_after_refactor
更新時間：2026-03-10
作者：AI Assistant
修改摘要：新增 Refactor 後完整測試 runner，依計畫執行步驟 1～4 並印出通過/失敗摘要
"""
import os
import sys
import subprocess

# 專案根目錄（care_rag_api）
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)


def step1_stub_check():
    """步驟 1：Stub 檢查，通過條件為 Embedding 與 LLM 皆非 Stub。"""
    from app.services.embedding_service import (
        get_default_embedding_service,
        GoogleGenAIEmbeddingService,
        StubEmbeddingService,
    )
    from app.services.llm_service import LLMService, GeminiLLM

    svc = get_default_embedding_service()
    emb_stub = isinstance(svc, StubEmbeddingService) or (
        isinstance(svc, GoogleGenAIEmbeddingService)
        and not getattr(svc, "_usable", False)
    )
    llm_svc = LLMService()
    client = llm_svc.client
    llm_stub = isinstance(client, GeminiLLM) and not getattr(
        client, "_use_real_api", False
    )
    return not emb_stub and not llm_stub


def step2_gemini_llm():
    """步驟 2：執行 test_gemini_llm.py，通過條件為 exit code 0。"""
    r = subprocess.run(
        [sys.executable, "-m", "scripts.test_gemini_llm"],
        cwd=ROOT,
        capture_output=False,
        timeout=120,
    )
    return r.returncode == 0


def step3_integration():
    """步驟 3：執行 test_integration.py，通過條件為 exit code 0。"""
    r = subprocess.run(
        [sys.executable, "-m", "scripts.test_integration"],
        cwd=ROOT,
        capture_output=False,
        timeout=60,
    )
    return r.returncode == 0


def step4_pytest():
    """步驟 4：執行 pytest tests/test_api/，通過條件為 exit code 0。"""
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_api/", "-v"],
        cwd=ROOT,
        capture_output=False,
        timeout=120,
    )
    return r.returncode == 0


def main():
    print("=" * 60)
    print("Refactor 後完整測試（步驟 1～4）")
    print("=" * 60)
    print(f"工作目錄: {ROOT}\n")

    results = []

    # 步驟 1
    print("[Step 1] Stub 檢查...")
    try:
        ok = step1_stub_check()
        results.append(("1. Stub 檢查", ok))
        print("  ->", "通過" if ok else "失敗（Embedding 或 LLM 為 Stub）")
    except Exception as e:
        results.append(("1. Stub 檢查", False))
        print(f"  -> 失敗: {e}")
    print()

    # 步驟 2
    print("[Step 2] Gemini LLM 測試 (scripts.test_gemini_llm)...")
    try:
        ok = step2_gemini_llm()
        results.append(("2. Gemini LLM", ok))
        print("  ->", "通過" if ok else "失敗（見上方輸出）")
    except subprocess.TimeoutExpired:
        results.append(("2. Gemini LLM", False))
        print("  -> 失敗: 逾時")
    except Exception as e:
        results.append(("2. Gemini LLM", False))
        print(f"  -> 失敗: {e}")
    print()

    # 步驟 3
    print("[Step 3] 整合測試 (scripts.test_integration)...")
    try:
        ok = step3_integration()
        results.append(("3. 整合測試", ok))
        print("  ->", "通過" if ok else "失敗（見上方輸出）")
    except subprocess.TimeoutExpired:
        results.append(("3. 整合測試", False))
        print("  -> 失敗: 逾時")
    except Exception as e:
        results.append(("3. 整合測試", False))
        print(f"  -> 失敗: {e}")
    print()

    # 步驟 4
    print("[Step 4] Pytest API (tests/test_api/)...")
    try:
        ok = step4_pytest()
        results.append(("4. Pytest API", ok))
        print("  ->", "通過" if ok else "失敗（見上方輸出）")
    except subprocess.TimeoutExpired:
        results.append(("4. Pytest API", False))
        print("  -> 失敗: 逾時")
    except Exception as e:
        results.append(("4. Pytest API", False))
        print(f"  -> 失敗: {e}")
    print()

    # 摘要
    print("=" * 60)
    print("摘要")
    print("=" * 60)
    for name, ok in results:
        status = "通過" if ok else "失敗"
        print(f"  {name}: {status}")
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"\n總計: {passed}/{total} 通過")
    if passed == total:
        print("\nE2E 請手動執行：先啟動 API，再執行 python scripts/test_graph_llm_qa.py")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
