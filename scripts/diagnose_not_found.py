"""
診斷「未找到」根本原因：檢索是否有帶出預期實體？若有，則問題在 LLM；若無，則問題在檢索。
執行：python -m scripts.diagnose_not_found [--query "問題"]
更新時間：2026-03-10
作者：AI Assistant
修改摘要：新增診斷腳本，列出檢索得到的 source ids 與預覽，判斷是檢索未命中或 LLM 回未找到
"""
import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.core.graph_store import SQLiteGraphStore
from app.services.vector_service import VectorService


async def main():
    parser = argparse.ArgumentParser(description="診斷「未找到」根因：檢索結果是否含預期實體")
    parser.add_argument(
        "--query",
        type=str,
        default="IC 卡資料上傳錯誤代碼 [01] 代表什麼？",
        help="查詢語句",
    )
    parser.add_argument("--top-k", type=int, default=5, help="檢索筆數")
    args = parser.parse_args()

    graph_store = SQLiteGraphStore(settings.GRAPH_DB_PATH)
    await graph_store.initialize()
    vector = VectorService(graph_store=graph_store)

    print("=" * 60)
    print("診斷：為何會「未找到」？")
    print("=" * 60)
    print(f"查詢: {args.query}")
    print(f"top_k: {args.top_k}")
    print(f"GRAPH_DB_PATH: {settings.GRAPH_DB_PATH}")
    print()

    sources = await vector.search(args.query, top_k=args.top_k)
    print(f"檢索結果筆數: {len(sources)}")
    if not sources:
        print()
        print("根因: 檢索回傳 0 筆 → 「未找到」來自「無來源」分支，未呼叫 LLM。")
        print("建議: 檢查 qa_vectors.db 是否已建、graph 是否有 QA 實體、embedding 是否正常。")
        await graph_store.close()
        return

    print()
    print("檢索到的來源（送給 LLM 的 context 即為以下內容）：")
    print("-" * 60)
    for i, s in enumerate(sources, 1):
        sid = s.get("id", "")
        score = s.get("score", 0)
        content = (s.get("content") or "")[:200]
        print(f"  [{i}] id={sid!r} score={score}")
        print(f"      content 預覽: {content!r}...")
        print()
    print("-" * 60)

    # 若查詢含 [CODE]，檢查對應 IC QA 實體是否在檢索結果中（支援數字與英數錯誤碼）
    import re
    code_match = re.search(r"\[\s*([A-Za-z0-9]+)\s*\]", args.query)
    if code_match:
        raw_code = code_match.group(1)
        code = re.sub(r"\s+", "", raw_code).upper()
        prefix = settings.GRAPH_IC_ERROR_QA_ENTITY_ID_PREFIX
        expected_id = f"{prefix}{code}"
        ids = [s.get("id") for s in sources]
        found = expected_id in ids
        print(f"預期實體（依查詢錯誤代碼）: {expected_id}")
        print(f"該實體是否在檢索結果中: {'是' if found else '否'}")
        print()
        if not found:
            print("根因: 檢索未帶出該筆 QA → 「未找到」可能因為送給 LLM 的 context 裡沒有這題答案。")
            print("建議: 檢查 qa_vectors.db 是否含該 entity_id、或調整 top_k/embedding 排序。")
        else:
            print("根因: 檢索已帶出該筆 QA，若仍回「未找到」則為 LLM 或 prompt 行為（模型回傳未找到）。")
            print("建議: 檢查 LLM 是否為 Stub、或調整 prompt 讓模型依參考資料作答。")
    else:
        print("（查詢無 [CODE] 錯誤代碼，未檢查特定實體 id）")

    await graph_store.close()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
