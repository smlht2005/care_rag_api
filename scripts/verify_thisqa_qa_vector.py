"""
驗證 Thisqa QA 向量檢索是否可正確召回 QA Entity

更新時間：2026-03-09 15:22
作者：AI Assistant
修改摘要：新增 QA 向量檢索驗證腳本，透過 VectorService + GraphStore 檢查給定 query 能否召回對應的 QA Entity
"""
import sys
import os
from typing import List, Dict

# 專案根目錄
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.core.graph_store import SQLiteGraphStore
from app.services.vector_service import VectorService


async def verify_query(query: str, top_k: int = 5) -> None:
    """執行一次 QA 向量檢索，列出召回的 QA Entity。"""
    graph_store = SQLiteGraphStore(settings.GRAPH_DB_PATH)
    await graph_store.initialize()
    vector_service = VectorService(graph_store=graph_store)

    print("Thisqa QA 向量檢索驗證")
    print("=" * 60)
    print(f"Query: {query}")
    print(f"graph.db: {settings.GRAPH_DB_PATH}")
    print("-" * 60)

    try:
        results: List[Dict] = await vector_service.search(query, top_k=top_k)
    finally:
        try:
            await graph_store.close()
        except Exception:
            pass

    if not results:
        print("[X] 無任何 QA 被召回（sources 為空）")
        return

    for i, r in enumerate(results, 1):
        rid = r.get("id")
        score = r.get("score")
        content = (r.get("content") or "").strip()
        preview = content.replace("\n", " ")[:120]
        metadata = r.get("metadata") or {}
        doc_id = metadata.get("properties", {}).get("document_id")
        print(f"[{i}] id={rid} score={score:.4f} doc_id={doc_id}")
        print(f"     preview: {preview}")


def main() -> None:
    import asyncio
    import argparse

    parser = argparse.ArgumentParser(
        description="驗證 Thisqa QA 向量檢索是否可正確召回 QA Entity"
    )
    parser.add_argument(
        "--query",
        type=str,
        required=False,
        default="批價作業如何搜尋病患資料？",
        help="測試問題（預設：批價作業如何搜尋病患資料？）",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="檢索筆數（預設: 5）",
    )
    args = parser.parse_args()

    try:
        asyncio.run(verify_query(args.query, top_k=args.top_k))
    except KeyboardInterrupt:
        print("\n[WARN] 用戶中斷（Ctrl+C）")
        sys.exit(1)


if __name__ == "__main__":
    main()

