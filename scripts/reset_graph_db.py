"""
重置 GraphRAG 資料庫
刪除所有現有數據，創建一個乾淨的 graph.db

更新時間：2025-12-26 16:40
作者：AI Assistant
修改摘要：修復資料庫鎖定錯誤和 Ctrl+C 無法停止的問題
"""
import asyncio
import sys
import os
import signal
import time
from pathlib import Path

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.core.graph_store import SQLiteGraphStore

# 全局變數用於追蹤中斷信號
_interrupted = False


def signal_handler(signum, frame):
    """處理 Ctrl+C 信號"""
    global _interrupted
    _interrupted = True
    print("\n\n⚠️  檢測到中斷信號（Ctrl+C），正在安全退出...")
    sys.exit(0)


async def check_db_lock(db_path: str) -> bool:
    """檢查資料庫是否被鎖定"""
    try:
        # 嘗試以只讀模式打開資料庫
        test_store = SQLiteGraphStore(db_path)
        await test_store.initialize()
        await test_store.close()
        return False  # 未鎖定
    except Exception as e:
        error_msg = str(e).lower()
        if "locked" in error_msg or "busy" in error_msg or "32" in error_msg:
            return True  # 被鎖定
        return False


async def reset_graph_db():
    """重置 GraphRAG 資料庫"""
    global _interrupted
    
    print("=" * 60)
    print("重置 GraphRAG 資料庫")
    print("=" * 60)
    
    db_path = settings.GRAPH_DB_PATH
    db_file = Path(db_path)
    
    # 檢查資料庫文件是否存在
    if db_file.exists():
        print(f"\n發現現有資料庫: {db_path}")
        print(f"文件大小: {db_file.stat().st_size / 1024 / 1024:.2f} MB")
        
        # 檢查資料庫是否被鎖定
        print("\n檢查資料庫狀態...")
        is_locked = await check_db_lock(db_path)
        
        if is_locked:
            print("\n❌ 資料庫文件正被其他進程使用（可能被 API 服務鎖定）")
            print("\n解決方案：")
            print("  1. 停止所有正在運行的 API 服務（uvicorn）")
            print("  2. 關閉所有可能使用資料庫的腳本")
            print("  3. 等待幾秒後重試")
            print("\n提示：可以使用以下命令檢查是否有 Python 進程正在使用資料庫：")
            print("  Windows: tasklist | findstr python")
            print("  Linux/Mac: ps aux | grep python")
            return False
        
        # 先連接到資料庫獲取統計信息
        graph_store = None
        try:
            graph_store = SQLiteGraphStore(db_path)
            await graph_store.initialize()
            stats = await graph_store.get_statistics()
            
            print(f"\n當前數據統計:")
            print(f"  實體總數: {stats.get('total_entities', 0)}")
            print(f"  關係總數: {stats.get('total_relations', 0)}")
            print(f"  實體類型: {stats.get('entity_types', {})}")
            print(f"  關係類型: {stats.get('relation_types', {})}")
            
            # 確保連接已關閉
            await graph_store.close()
            graph_store = None
            
            # 等待一小段時間確保連接完全釋放
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"⚠️  讀取統計信息失敗: {str(e)}")
            if graph_store:
                try:
                    await graph_store.close()
                except:
                    pass
        
        # 刪除資料庫文件
        print(f"\n正在刪除資料庫文件...")
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            if _interrupted:
                print("\n⚠️  操作被用戶中斷")
                return False
                
            try:
                # 再次檢查是否被鎖定
                if await check_db_lock(db_path):
                    if attempt < max_retries - 1:
                        print(f"  資料庫仍被鎖定，等待 {retry_delay} 秒後重試 ({attempt + 1}/{max_retries})...")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # 指數退避
                        continue
                    else:
                        print(f"❌ 資料庫仍被鎖定，無法刪除")
                        return False
                
                db_file.unlink()
                print(f"✅ 已刪除資料庫文件: {db_path}")
                break
                
            except PermissionError as e:
                if attempt < max_retries - 1:
                    print(f"  權限錯誤，等待 {retry_delay} 秒後重試 ({attempt + 1}/{max_retries})...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    print(f"❌ 刪除資料庫文件失敗（權限錯誤）: {str(e)}")
                    print("\n提示：請確保沒有其他進程正在使用資料庫文件")
                    return False
            except Exception as e:
                print(f"❌ 刪除資料庫文件失敗: {str(e)}")
                return False
    else:
        print(f"\nℹ️  資料庫文件不存在: {db_path}")
    
    # 創建新的資料庫
    if _interrupted:
        print("\n⚠️  操作被用戶中斷")
        return False
    
    print(f"\n創建新的資料庫...")
    graph_store = None
    try:
        graph_store = SQLiteGraphStore(db_path)
        await graph_store.initialize()
        await graph_store.close()
        graph_store = None
        
        # 驗證新資料庫
        graph_store2 = SQLiteGraphStore(db_path)
        await graph_store2.initialize()
        stats = await graph_store2.get_statistics()
        await graph_store2.close()
        
        print(f"✅ 新資料庫創建成功")
        print(f"  實體總數: {stats.get('total_entities', 0)}")
        print(f"  關係總數: {stats.get('total_relations', 0)}")
        
        return True
    except Exception as e:
        print(f"❌ 創建新資料庫失敗: {str(e)}")
        if graph_store:
            try:
                await graph_store.close()
            except:
                pass
        return False


async def main():
    """主函數"""
    global _interrupted
    
    import argparse
    
    parser = argparse.ArgumentParser(description="重置 GraphRAG 資料庫")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="確認重置（跳過確認提示）"
    )
    
    args = parser.parse_args()
    
    if not args.confirm:
        print("\n⚠️  警告：此操作將刪除所有現有數據！")
        try:
            response = input("是否繼續？(yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("操作已取消")
                return
        except KeyboardInterrupt:
            print("\n\n⚠️  操作被用戶取消")
            return
    
    if _interrupted:
        return
    
    try:
        success = await reset_graph_db()
        
        if success:
            print("\n" + "=" * 60)
            print("重置完成！")
            print("=" * 60)
            print("\n現在可以使用以下命令重新導入 PDF:")
            print("  python scripts/process_pdf_to_graph.py \"data/example/your_file.pdf\"")
        else:
            print("\n❌ 重置失敗，請檢查錯誤信息")
    except asyncio.CancelledError:
        print("\n\n⚠️  操作被取消")
    except KeyboardInterrupt:
        print("\n\n⚠️  程式被用戶中斷（Ctrl+C）")
        print("正在安全退出...")
    except Exception as e:
        print(f"\n❌ 發生未預期的錯誤: {str(e)}")


if __name__ == "__main__":
    # 註冊信號處理器（僅在非 Windows 系統上）
    if sys.platform != "win32":
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  程式被用戶中斷（Ctrl+C）")
        print("正在退出...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 發生錯誤: {str(e)}")
        sys.exit(1)

