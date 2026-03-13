"""
解析掛號QA Markdown 檔案並建立問答知識圖譜
從 Markdown 文件提取結構化問答對，建立專門的 graph_qa.db 圖資料庫

更新時間：2026-01-13 15:20
作者：AI Assistant
修改摘要：更新標頭註解日期
更新時間：2025-12-30 10:00
作者：AI Assistant
修改摘要：建立掛號QA Markdown 解析腳本，提取結構化問答對並建立 graph_qa.db
"""
import os
import sys
import asyncio
import uuid
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

# 設定 Windows 終端編碼
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.graph_store import SQLiteGraphStore, Entity, Relation


def parse_qa_markdown(md_path: str) -> Dict[str, Any]:
    """
    解析掛號QA Markdown 檔案
    
    Args:
        md_path: Markdown 檔案路徑
    
    Returns:
        包含文件資訊和 QA 列表的字典
    """
    # 使用 Path 檢查檔案存在性，避免中文編碼問題
    md_path_obj = Path(md_path)
    if not md_path_obj.exists():
        raise FileNotFoundError(f"Markdown 檔案不存在: {md_path}")
    
    # 使用 Path 開啟檔案，確保編碼正確
    with md_path_obj.open('r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取所有 QA 區塊
    # 情境一：原始掛號 QA 模板，使用 '---' 分隔每一題
    if re.search(r'^---\s*$', content, flags=re.MULTILINE):
        qa_blocks = re.split(r'^---\s*$', content, flags=re.MULTILINE)
    else:
        # 情境二：Thisqa 類型檔案，使用「## Q:」區分每一題
        # 使用前瞻確保每個區塊保留自己的標題列
        qa_blocks = re.split(r'(?=^##\s+Q:\s*)', content, flags=re.MULTILINE)
    
    qa_list = []
    
    for block in qa_blocks:
        block = block.strip()
        if not block:
            continue
        
        # 提取編號和標題
        # 1) 原始模板：## **1\. Q: 標題** 或 ## **1. Q: 標題**
        title_match = re.search(r'^##\s*\*\*(\d+)\\?\.\s*Q:\s*(.+?)\*\*', block, re.MULTILINE)
        if title_match:
            qa_number = int(title_match.group(1))
            qa_title = title_match.group(2).strip()
        else:
            # 2) Thisqa 模板：## Q: 標題？
            simple_title_match = re.search(r'^##\s+Q:\s*(.+)$', block, re.MULTILINE)
            if not simple_title_match:
                continue
            qa_title = simple_title_match.group(1).strip()
            # 沒有顯式編號時，依出現順序自動編號
            qa_number = len(qa_list) + 1
        
        # 提取使用情境
        scenario_match = re.search(r'\*\*使用情境\s*\(Scenario\)\*\*\s*[：:]\s*(.+?)(?=\*\*|$)', block, re.DOTALL)
        scenario = scenario_match.group(1).strip() if scenario_match else ""
        
        # 提取關鍵字
        keywords_match = re.search(r'\*\*關鍵字\s*\(Keywords\)\*\*\s*[：:]\s*(.+?)(?=\*\*|$)', block, re.DOTALL)
        keywords_text = keywords_match.group(1).strip() if keywords_match else ""
        keywords = [k.strip() for k in keywords_text.split(',') if k.strip()] if keywords_text else []
        
        # 提取問題
        question_match = re.search(r'\*\*Question\*\*\s*[：:]\s*(.+?)(?=\*\*|$)', block, re.DOTALL)
        question = question_match.group(1).strip() if question_match else ""
        
        # 提取答案
        answer_match = re.search(r'\*\*Answer\*\*\s*[：:]\s*(.+?)(?=\*\*步驟|$)', block, re.DOTALL)
        answer = answer_match.group(1).strip() if answer_match else ""
        # 清理答案中的列表標記
        answer = re.sub(r'^\*\s*', '', answer, flags=re.MULTILINE).strip()
        
        # 提取步驟
        steps_match = re.search(r'\*\*步驟\s*\(Steps\)\*\*\s*[：:]\s*(.+?)(?=\*\*Notes|$)', block, re.DOTALL)
        steps_text = steps_match.group(1).strip() if steps_match else ""
        # 提取步驟列表
        steps = []
        if steps_text:
            step_items = re.findall(r'^\d+\.\s*(.+?)(?=^\d+\.|$)', steps_text, re.MULTILINE)
            steps = [s.strip() for s in step_items if s.strip()]
        
        # 提取備註
        notes_match = re.search(r'\*\*Notes\*\*\s*[：:]\s*(.+?)(?=\*\*Metadata|$)', block, re.DOTALL)
        notes = notes_match.group(1).strip() if notes_match else ""
        
        # 提取 Metadata
        metadata_match = re.search(r'\*\*Metadata\*\*\s*[：:]\s*(.+?)(?=---|$)', block, re.DOTALL)
        metadata_text = metadata_match.group(1).strip() if metadata_match else ""
        
        # 解析 Metadata 欄位
        metadata = {}
        if metadata_text:
            metadata_lines = metadata_text.split('\n')
            for line in metadata_lines:
                line = line.strip()
                if not line or not line.startswith('*'):
                    continue
                # 移除開頭的 * 和空白
                line = re.sub(r'^\*\s*', '', line).strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    metadata[key] = value
        
        qa_item = {
            "number": qa_number,
            "title": qa_title,
            "scenario": scenario,
            "keywords": keywords,
            "question": question,
            "answer": answer,
            "steps": steps,
            "notes": notes,
            "metadata": metadata
        }
        
        qa_list.append(qa_item)
    
    return {
        "source_file": md_path,
        "file_name": Path(md_path).name,
        "qa_count": len(qa_list),
        "qa_list": qa_list
    }


async def process_qa_markdown_to_graph(
    md_path: str,
    document_id: Optional[str] = None,
    db_path: str = "./data/graph_qa.db"
):
    """
    處理掛號QA Markdown 檔案並構建問答知識圖譜
    
    Args:
        md_path: Markdown 檔案路徑
        document_id: 文件 ID（如果為 None，則自動生成）
        db_path: 圖資料庫路徑
    """
    graph_store = None
    try:
        print("=" * 60)
        print("掛號QA Markdown 問答知識圖譜構建")
        print("=" * 60)
        
        # 1. 解析 Markdown 檔案
        print(f"\n[步驟 1/4] 解析 Markdown 檔案...")
        print(f"檔案路徑: {md_path}")
        
        try:
            parsed_data = parse_qa_markdown(md_path)
            print(f"[OK] 解析完成，提取到 {parsed_data['qa_count']} 個問答對")
        except Exception as e:
            print(f"[ERROR] Markdown 解析失敗: {str(e)}")
            import traceback
            traceback.print_exc()
            return
        
        # 2. 初始化問答圖資料庫
        print(f"\n[步驟 2/4] 初始化問答圖資料庫...")
        print(f"資料庫路徑: {db_path}")
        
        # 確保資料目錄存在
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            print(f"[OK] 建立資料目錄: {db_dir}")
        
        graph_store = SQLiteGraphStore(db_path)
        await graph_store.initialize()
        print("[OK] 問答圖資料庫初始化完成")
        
        # 3. 生成文件 ID
        if document_id is None:
            md_name = Path(md_path).stem
            document_id = f"qa_doc_{md_name}_{str(uuid.uuid4())[:8]}"
        
        print(f"\n[步驟 3/4] 文件 ID: {document_id}")
        
        # 4. 建立圖結構
        print(f"\n[步驟 4/4] 建立圖結構...")
        
        # 4.1 建立文件實體
        doc_entity = Entity(
            id=document_id,
            type="Document",
            name=parsed_data["file_name"],
            properties={
                "source": md_path,
                "type": "qa_markdown",
                "qa_count": parsed_data["qa_count"],
                "file_name": parsed_data["file_name"]
            },
            created_at=None
        )
        await graph_store.add_entity(doc_entity)
        print(f"[OK] 建立文件實體: {document_id}")
        
        # 4.2 建立問答對實體和關係
        qa_count = 0
        for qa in parsed_data["qa_list"]:
            qa_id = f"{document_id}_qa_{qa['number']}"
            
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
                    id=f"{document_id}_to_{qa_id}",
                    source_id=document_id,
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
        
        print(f"[OK] 建立 {qa_count} 個問答實體和關係")
        
        print("\n" + "=" * 60)
        print("處理完成！")
        print("=" * 60)
        print(f"\n文件 ID: {document_id}")
        print(f"問答對數量: {qa_count}")
        print(f"資料庫路徑: {db_path}")
        print(f"\n可以使用以下命令查詢圖結構:")
        print(f"  python scripts/query_qa_graph.py")
        print(f"  python scripts/query_qa_graph.py --search \"衛材\"")
        
    except KeyboardInterrupt:
        print(f"\n[WARNING] 處理被用戶中斷（Ctrl+C）")
        print(f"正在清理資源...")
    except Exception as e:
        print(f"\n[ERROR] 處理失敗: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 確保關閉連線
        if graph_store:
            try:
                await graph_store.close()
                print("[OK] 資源清理完成")
            except Exception as e:
                print(f"[WARNING] 清理資源時發生錯誤: {str(e)}")


async def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="解析掛號QA Markdown 檔案並建立問答知識圖譜")
    parser.add_argument(
        "--md-file",
        type=str,
        default="docs/example/掛號QA.md",
        help="Markdown 檔案路徑（預設: docs/example/掛號QA.md）"
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="./data/graph_qa.db",
        help="圖資料庫路徑（預設: ./data/graph_qa.db）"
    )
    parser.add_argument(
        "--doc-id",
        type=str,
        default=None,
        help="文件 ID（如果未指定，則自動生成）"
    )
    
    args = parser.parse_args()
    
    # 使用 Path 處理路徑，避免中文編碼問題
    script_dir = Path(__file__).parent.parent
    
    # 如果檔案不存在，嘗試在 docs/example 目錄中尋找匹配的檔案
    md_path_obj = Path(args.md_file)
    if not md_path_obj.is_absolute():
        md_path_obj = script_dir / args.md_file
    
    # 如果檔案不存在，嘗試在 docs/example 和 docs/example/qa 目錄中尋找匹配的檔案
    if not md_path_obj.exists():
        # 先嘗試 qa 子目錄
        qa_dir = script_dir / "docs" / "example" / "qa"
        if qa_dir.exists():
            for file in qa_dir.glob("*.md"):
                # 檢查檔案名稱是否匹配
                if args.md_file in file.name or file.name in args.md_file:
                    md_path_obj = file
                    print(f"[INFO] 找到匹配檔案: {file.name}")
                    break
        
        # 如果還沒找到，嘗試 example 目錄
        if not md_path_obj.exists():
            example_dir = script_dir / "docs" / "example"
            if example_dir.exists():
                # 從參數中提取關鍵字進行匹配
                search_keywords = []
                if "掛號" in args.md_file or "registration" in args.md_file.lower():
                    search_keywords = ["掛號", "QA"]
                elif "衛材" in args.md_file or "material" in args.md_file.lower() or "TAMIS" in args.md_file:
                    search_keywords = ["衛材", "TAMIS", "供應中心"]
                
                # 嘗試尋找包含關鍵字的檔案
                for file in example_dir.glob("*.md"):
                    if any(keyword in file.name for keyword in search_keywords):
                        md_path_obj = file
                        print(f"[INFO] 找到匹配檔案: {file.name}")
                        break
    
    md_path = str(md_path_obj.resolve())
    
    await process_qa_markdown_to_graph(
        md_path=md_path,
        document_id=args.doc_id,
        db_path=args.db_path
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[WARNING] 程式被用戶中斷（Ctrl+C）")
        print("正在退出...")
        sys.exit(0)
