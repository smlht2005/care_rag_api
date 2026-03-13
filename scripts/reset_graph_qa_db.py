"""
重置 QA Graph 資料庫（graph_qa.db）
刪除所有現有 QA / IC 規格數據，建立一個乾淨的 graph_qa.db

更新時間：2026-03-06 17:45
作者：AI Assistant
修改摘要：建立專用的 QA 圖資料庫重置腳本，僅針對 data/graph_qa.db 進行安全重建
"""
import asyncio
import os
import sys
import signal
from pathlib import Path

# 添加專案路徑，確保可以匯入 app.* 模組
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 專用 QA 圖資料庫路徑（與 QA API 端點一致）
QA_DB_PATH = "./data/graph_qa.db"


_interrupted = False


def signal_handler(signum, frame):
    """處理 Ctrl+C 信號"""
    global _interrupted
    _interrupted = True
    print("\n偵測到中斷信號（Ctrl+C），正在安全退出...")
    sys.exit(0)


async def check_db_lock(db_path: str) -> bool:
    """
    檢查資料庫是否被鎖定

    嘗試以 SQLiteGraphStore 開啟並關閉資料庫，若出現 locked/busy 類錯誤則視為鎖定。
    """
    from app.core.graph_store import SQLiteGraphStore

    try:
        store = SQLiteGraphStore(db_path)
        await store.initialize()
        await store.close()
        return False
    except Exception as e:
        error_msg = str(e).lower()
        if "locked" in error_msg or "busy" in error_msg or "32" in error_msg:
            return True
        return False


async def reset_graph_qa_db() -> bool:
    """
    重置 QA Graph 資料庫（僅針對 data/graph_qa.db）

    不再刪除檔案，而是使用 SQLite 直接清空 entities / relations 兩張表，
    避免 Windows 上因檔案鎖定導致 WinError 32。
    """
    from app.core.graph_store import SQLiteGraphStore

    global _interrupted

    print("=" * 60)
    print("重置 QA Graph 資料庫（graph_qa.db）")
    print("=" * 60)

    db_path = QA_DB_PATH
    db_file = Path(db_path)

    # 確保資料夾存在
    db_dir = db_file.parent
    db_dir.mkdir(parents=True, exist_ok=True)

    # 檢查鎖定狀態（若有其他進程使用則中止）
    if db_file.exists():
        print(f"\n發現現有 QA 資料庫: {db_path}")
        print(f"文件大小: {db_file.stat().st_size / 1024 / 1024:.2f} MB")
        print("\n檢查資料庫狀態...")
        is_locked = await check_db_lock(db_path)
        if is_locked:
            print("\n資料庫文件正被其他進程使用（可能是 API 服務或測試腳本）")
            print("請先停止相關服務後再重試。")
            return False
    else:
        print(f"\n找不到既有 QA 資料庫（將建立新的空資料庫）: {db_path}")

    if _interrupted:
        print("\n操作被用戶中斷")
        return False

    store = None
    try:
        store = SQLiteGraphStore(db_path)
        await store.initialize()

        # 重置前統計
        stats_before = await store.get_statistics()
        print("\n重置前 QA 圖統計：")
        print(f"  實體總數: {stats_before.get('total_entities', 0)}")
        print(f"  關係總數: {stats_before.get('total_relations', 0)}")
        print(f"  實體類型: {stats_before.get('entity_types', {})}")
        print(f"  關係類型: {stats_before.get('relation_types', {})}")

        # 直接刪除所有關係與實體
        print("\n正在清空 entities / relations 資料...")
        async with store.conn.cursor() as cursor:  # type: ignore[attr-defined]
            await cursor.execute("DELETE FROM relations")
            await cursor.execute("DELETE FROM entities")
            await store.conn.commit()  # type: ignore[attr-defined]

        # 重置後統計
        stats_after = await store.get_statistics()
        print("\n重置後 QA 圖統計：")
        print(f"  實體總數: {stats_after.get('total_entities', 0)}")
        print(f"  關係總數: {stats_after.get('total_relations', 0)}")
        print(f"  實體類型: {stats_after.get('entity_types', {})}")
        print(f"  關係類型: {stats_after.get('relation_types', {})}")

        await store.close()
        store = None
        return True
    except Exception as e:
        print(f"重置 QA Graph 資料庫失敗: {str(e)}")
        if store:
            try:
                await store.close()
            except Exception:
                pass
        return False


async def main() -> None:
    """主函數"""
    global _interrupted

    import argparse

    parser = argparse.ArgumentParser(description="重置 QA Graph 資料庫（data/graph_qa.db）")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="確認重置（跳過互動式確認）",
    )

    args = parser.parse_args()

    if not args.confirm:
        print("\n警告：此操作將刪除 QA Graph 資料庫中所有資料！")
        try:
            response = input("是否繼續？(yes/no): ")
            if response.lower() not in ("yes", "y"):
                print("操作已取消。")
                return
        except KeyboardInterrupt:
            print("\n操作被用戶取消。")
            return

    if _interrupted:
        return

    success = await reset_graph_qa_db()
    if success:
        print("\n" + "=" * 60)
        print("QA Graph 資料庫重置完成。")
        print("=" * 60)
        print("\n接下來可以執行 Thisqa 匯入流程，例如：")
        print("  python scripts/import_thisqa_markdown_batch.py --qa-dir \"data/Thisqa\" --db-path \"./data/graph_qa.db\"")
        print("  python scripts/import_ic_error_spec_to_qa_graph.py --spec-file \"data/Thisqa/IC卡資料上傳錯誤對照.txt\" --db-path \"./data/graph_qa.db\" --doc-id \"ic_error_spec_main\" --overwrite-doc")
    else:
        print("\n重置 QA Graph 資料庫失敗，請檢查前述錯誤訊息。")


if __name__ == "__main__":
    if sys.platform != "win32":
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程式被用戶中斷（Ctrl+C），正在退出...")
        sys.exit(0)
    except Exception as e:
        print(f"\n發生錯誤: {str(e)}")
        sys.exit(1)

