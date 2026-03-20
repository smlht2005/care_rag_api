"""
驗證 missfind 修復：graph 關鍵字 fallback 不因 Organization 撞 type 而命中「批價管理系統」

更新時間：2026-03-20 12:15
作者：AI Assistant
修改摘要：可於 dev 手動執行；預期 graph keyword hits: 0（見 docs/bug/missfind.md）

用法（專案根目錄 care_rag_api）：
  python scripts/verify_missfind_graph_fallback.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.graph_store import Entity, MemoryGraphStore
from app.services.vector_service import VectorService


async def main() -> None:
    g = MemoryGraphStore()
    await g.initialize()
    await g.add_entity(
        Entity(id="e1", type="Organization", name="批價管理系統", properties={})
    )
    vs = VectorService(graph_store=g)
    q = "World Health Organization 在長期照護方面有什麼政策？"
    r = await vs._search_from_graph(q, top_k=5)
    print("query:", q)
    print("graph keyword hits:", len(r))
    if r:
        for x in r:
            print(" ", x.get("id"), repr(x.get("content", ""))[:100], x.get("metadata"))
        sys.exit(1)
    print("OK: zero hits (no false positive from Organization token vs type).")


if __name__ == "__main__":
    asyncio.run(main())
