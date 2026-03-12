"""
呼叫主線 GraphRAG API（POST /api/v1/query）測試 graph.db + LLM 問答
需先啟動 API：在 care_rag_api 目錄執行 scripts/run_api.bat 或 uvicorn app.main:app --host 0.0.0.0 --port 8000

更新時間：2026-03-09
作者：AI Assistant
修改摘要：先檢查 GET / 是否為 Care RAG API，若 404 或錯誤 app 則提示用 run_api.bat 從正確目錄啟動
更新時間：2026-03-06
作者：AI Assistant
修改摘要：新增腳本，方便以指令列測試 graph.db + LLM QA
"""
import argparse
import json
import sys
import os

try:
    import requests
except ImportError:
    print("請安裝 requests: pip install requests")
    sys.exit(1)

# 專案根目錄
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_API_KEY = "test-api-key"

# 若未傳入 --query，則使用以下預設問題（與 Thisqa / graph.db 相關）
DEFAULT_QUERIES = [
    "批價作業如何搜尋病患資料？",
    "日樺加沙颱風天災未具健保身分時要上傳什麼醫令代碼？",
    "IC 卡資料上傳錯誤代碼 [01] 代表什麼？",
]


def check_care_rag_api(base_url: str) -> tuple[bool, str]:
    """
    檢查 base_url 是否為 Care RAG API（GET / 應回 message 含 'Care RAG API'）。
    回傳 (True, "") 表示正確；(False, 錯誤說明) 表示非本專案或連線失敗。
    """
    url = f"{base_url.rstrip('/')}/"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 404:
            return False, "GET / 回傳 404，表示目前 port 8000 不是 Care RAG API。請關閉現有服務，在 care_rag_api 目錄執行： scripts\\run_api.bat  或  uvicorn app.main:app --host 0.0.0.0 --port 8000"
        r.raise_for_status()
        data = r.json()
        msg = (data.get("message") or "")
        if "Care RAG API" not in msg:
            return False, f"GET / 回傳的 message 不是 Care RAG API（目前為: {msg!r}）。請在 care_rag_api 目錄啟動 API： scripts\\run_api.bat"
        return True, ""
    except requests.exceptions.RequestException as e:
        return False, f"無法連線至 {url}：{e}。請先啟動 API（在 care_rag_api 目錄執行 scripts\\run_api.bat 或 uvicorn app.main:app --host 0.0.0.0 --port 8000）"


def run_query(base_url: str, api_key: str, query: str, top_k: int = 5, skip_cache: bool = True) -> dict:
    url = f"{base_url.rstrip('/')}/api/v1/query"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key,
    }
    payload = {"query": query, "top_k": top_k, "skip_cache": skip_cache}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "answer": None, "sources": [], "query": query}


def main():
    parser = argparse.ArgumentParser(
        description="測試 graph.db + LLM QA（呼叫 POST /api/v1/query）"
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="單一問題；不給則跑預設多題",
    )
    parser.add_argument(
        "--url",
        type=str,
        default=DEFAULT_BASE_URL,
        help=f"API 基礎 URL（預設: {DEFAULT_BASE_URL}）",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=DEFAULT_API_KEY,
        help="X-API-Key 表頭值",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="檢索筆數（預設: 5）",
    )
    args = parser.parse_args()

    queries = [args.query] if args.query else DEFAULT_QUERIES

    ok, err = check_care_rag_api(args.url)
    if not ok:
        print("GraphRAG QA 測試（graph.db + LLM）")
        print("=" * 60)
        print("[X]", err)
        sys.exit(1)

    print("GraphRAG QA 測試（graph.db + LLM）")
    print("=" * 60)
    for i, q in enumerate(queries, 1):
        print(f"\n[{i}] Q: {q}")
        result = run_query(args.url, args.api_key, q, top_k=args.top_k)
        if result.get("error"):
            print(f"    [X] 錯誤: {result['error']}")
            continue
        answer = result.get("answer") or "(無回答)"
        print(f"    A: {answer}")
        if "[Gemini Stub]" in (answer or "") or "[OpenAI Stub]" in (answer or "") or "[DeepSeek Stub]" in (answer or ""):
            print("    [提示] 目前為 Stub 回應；請重啟 API 後再測，或確認 stub 偵測已生效。")
        sources = result.get("sources") or []
        if sources:
            print(f"    來源數: {len(sources)}")
    print("\n" + "=" * 60)
    print("結束")


if __name__ == "__main__":
    main()
