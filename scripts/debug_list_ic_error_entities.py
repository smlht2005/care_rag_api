"""
IC 錯誤碼 QA1 實體檢查工具
更新時間：2026-03-10
作者：AI Assistant
修改摘要：列出指定 IC 錯誤碼 QA1 實體（doc_thisqa_ic_error_qa_01 / _C001）之 type/name/properties，確認建圖是否正確
"""
import asyncio

from app.config import settings
from app.core.graph_store import SQLiteGraphStore


async def main() -> None:
    store = SQLiteGraphStore(settings.GRAPH_DB_PATH)
    await store.initialize()
    ids = [
        "doc_thisqa_ic_error_qa_01",
        "doc_thisqa_ic_error_qa_C001",
    ]
    for eid in ids:
        e = await store.get_entity(eid)
        print("ID:", eid)
        if not e:
            print("  NOT FOUND")
        else:
            print("  type:", e.type)
            print("  name:", e.name)
            props = e.properties or {}
            print("  code:", props.get("code"))
            print("  question:", (props.get("question") or "")[:80])
            print("  answer:", (props.get("answer") or "")[:80])
        print("-")
    await store.close()


if __name__ == "__main__":
    asyncio.run(main())

