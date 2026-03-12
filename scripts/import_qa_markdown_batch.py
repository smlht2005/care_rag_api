"""
批次匯入 QA Markdown 檔案到乾淨的資料庫
只包含 QA Markdown 資料，不包含其他混雜資料

更新時間：2026-01-13 15:20
作者：AI Assistant
修改摘要：更新標頭註解日期
更新時間：2025-12-30 11:00
作者：AI Assistant
修改摘要：建立批次匯入腳本，處理 docs/example/qa 目錄下的所有 QA Markdown 檔案
"""
import os
import sys
import asyncio
from pathlib import Path

# 設定 Windows 終端編碼（使用環境變數方式，避免關閉問題）
if sys.platform == 'win32':
    import os
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.graph_store import SQLiteGraphStore, Entity, Relation
from scripts.parse_qa_markdown_to_graph import parse_qa_markdown


async def import_qa_markdown_batch(
    qa_dir: str = "docs/example/qa",
    db_path: str = "./data/graph_qa.db",
    clean_db: bool = True
):
    """
    批次匯入 QA Markdown 檔案
    
    Args:
        qa_dir: QA Markdown 檔案目錄
        db_path: 資料庫路徑
        clean_db: 是否刪除現有資料庫（建立乾淨的新資料庫）
    """
    script_dir = Path(__file__).parent.parent
    qa_dir_path = script_dir / qa_dir
    
    # 如果相對路徑不存在，嘗試絕對路徑
    if not qa_dir_path.exists():
        qa_dir_path = Path(qa_dir)
        if not qa_dir_path.exists():
            print(f"[ERROR] QA 目錄不存在: {script_dir / qa_dir}")
            return
    
    # 1. 刪除現有資料庫（如果存在且需要清理）
    if clean_db:
        db_path_obj = script_dir / db_path.lstrip('./')
        if db_path_obj.exists():
            print(f"[INFO] 刪除現有資料庫: {db_path_obj}")
            try:
                db_path_obj.unlink()
                print(f"[OK] 資料庫已刪除")
            except Exception as e:
                print(f"[WARNING] 無法刪除資料庫: {str(e)}")
    
    # 2. 查找所有 QA Markdown 檔案
    qa_files = list(qa_dir_path.glob("*.md"))
    
    if not qa_files:
        print(f"[WARNING] 在 {qa_dir_path} 中沒有找到 Markdown 檔案")
        return
    
    print("=" * 60)
    print("批次匯入 QA Markdown 檔案")
    print("=" * 60)
    print(f"\n找到 {len(qa_files)} 個 QA Markdown 檔案:")
    for i, file in enumerate(qa_files, 1):
        print(f"  {i}. {file.name}")
    
    # 3. 初始化資料庫（只初始化一次）
    print(f"\n初始化資料庫...")
    script_dir = Path(__file__).parent.parent
    db_path_obj = script_dir / db_path.lstrip('./')
    
    # 確保資料目錄存在
    db_dir = db_path_obj.parent
    if not db_dir.exists():
        db_dir.mkdir(parents=True)
        print(f"[OK] 建立資料目錄: {db_dir}")
    
    graph_store = SQLiteGraphStore(str(db_path_obj))
    await graph_store.initialize()
    print(f"[OK] 資料庫初始化完成: {db_path_obj}")
    
    # 4. 批次處理每個檔案
    print(f"\n開始匯入...")
    print("=" * 60)
    
    success_count = 0
    fail_count = 0
    
    try:
        for i, qa_file in enumerate(qa_files, 1):
            print(f"\n[{i}/{len(qa_files)}] 處理: {qa_file.name}")
            print("-" * 60)
            
            try:
                # 解析 Markdown 檔案
                print(f"  解析 Markdown 檔案...")
                parsed_data = parse_qa_markdown(str(qa_file.resolve()))
                print(f"  [OK] 解析完成，提取到 {parsed_data['qa_count']} 個問答對")
                
                # 從檔案名稱生成文件 ID
                file_stem = qa_file.stem
                # 簡化文件 ID（移除特殊字元）
                doc_id = file_stem.lower().replace(" ", "_").replace("-", "_")
                # 移除特殊字元，只保留字母、數字和底線
                doc_id = ''.join(c if c.isalnum() or c == '_' else '_' for c in doc_id)
                # 移除連續的底線
                while '__' in doc_id:
                    doc_id = doc_id.replace('__', '_')
                doc_id = doc_id.strip('_')
                
                # 如果太長，截斷
                if len(doc_id) > 50:
                    doc_id = doc_id[:50]
                
                print(f"  文件 ID: {doc_id}")
                
                # 建立文件實體
                doc_entity = Entity(
                    id=doc_id,
                    type="Document",
                    name=parsed_data["file_name"],
                    properties={
                        "source": str(qa_file.resolve()),
                        "type": "qa_markdown",
                        "qa_count": parsed_data["qa_count"],
                        "file_name": parsed_data["file_name"]
                    },
                    created_at=None
                )
                await graph_store.add_entity(doc_entity)
                print(f"  [OK] 建立文件實體")
                
                # 建立問答對實體和關係
                qa_count = 0
                for qa in parsed_data["qa_list"]:
                    qa_id = f"{doc_id}_qa_{qa['number']}"
                    
                    # 建立問答實體
                    qa_entity = Entity(
                        id=qa_id,
                        type="QA",
                        name=qa["title"][:100],  # 限制名稱長度
                        properties={
                            "question": qa["question"],
                            "answer": qa["answer"],
                            "scenario": qa["scenario"],
                            "keywords": qa["keywords"],
                            "steps": qa["steps"],
                            "notes": qa["notes"],
                            "qa_number": qa["number"],
                            "qa_title": qa["title"],
                            "metadata": qa["metadata"],
                            "source": "qa_markdown"
                        },
                        created_at=None
                    )
                    
                    if await graph_store.add_entity(qa_entity):
                        qa_count += 1
                        
                        # 建立文件到問答的關係
                        relation = Relation(
                            id=f"{doc_id}_to_{qa_id}",
                            source_id=doc_id,
                            target_id=qa_id,
                            type="CONTAINS_QA",
                            properties={
                                "qa_number": qa["number"],
                                "qa_index": qa["number"]
                            },
                            weight=1.0,
                            created_at=None
                        )
                        await graph_store.add_relation(relation)
                
                print(f"  [OK] 建立 {qa_count} 個問答實體和關係")
                success_count += 1
                print(f"[OK] {qa_file.name} 匯入成功")
                
            except Exception as e:
                fail_count += 1
                print(f"[ERROR] {qa_file.name} 匯入失敗: {str(e)}")
                import traceback
                traceback.print_exc()
    
    finally:
        # 關閉資料庫連線
        await graph_store.close()
        print(f"\n[OK] 資料庫連線已關閉")
    
    # 4. 匯總結果
    print("\n" + "=" * 60)
    print("批次匯入完成")
    print("=" * 60)
    print(f"成功: {success_count}/{len(qa_files)}")
    print(f"失敗: {fail_count}/{len(qa_files)}")
    print(f"資料庫路徑: {db_path}")
    print(f"\n可以使用以下命令測試:")
    print(f"  py scripts/test_qa_import.py --list-docs")
    print(f"  py scripts/query_qa_graph.py")


async def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="批次匯入 QA Markdown 檔案到乾淨的資料庫")
    parser.add_argument(
        "--qa-dir",
        type=str,
        default="docs/example/qa",
        help="QA Markdown 檔案目錄（預設: docs/example/qa）"
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="./data/graph_qa.db",
        help="資料庫路徑（預設: ./data/graph_qa.db）"
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="不清除現有資料庫（預設會清除）"
    )
    
    args = parser.parse_args()
    
    await import_qa_markdown_batch(
        qa_dir=args.qa_dir,
        db_path=args.db_path,
        clean_db=not args.no_clean
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[WARNING] 程式被用戶中斷（Ctrl+C）")
        print("正在退出...")
        sys.exit(0)
