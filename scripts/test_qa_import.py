"""
測試 QA 匯入結果
驗證新匯入的 QA 資料是否正確

更新時間：2026-01-13 15:20
作者：AI Assistant
修改摘要：更新標頭註解日期
更新時間：2025-12-30 10:30
作者：AI Assistant
修改摘要：建立 QA 匯入測試腳本，驗證資料完整性和正確性
"""
import os
import sys
import asyncio
from pathlib import Path
from typing import List, Dict, Any

# 設定 Windows 終端編碼
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.graph_store import SQLiteGraphStore, Entity


async def test_qa_by_document(doc_id: str, db_path: str = "./data/graph_qa.db"):
    """
    測試特定文件的 QA 匯入結果
    
    Args:
        doc_id: 文件 ID
        db_path: 資料庫路徑
    """
    if not os.path.exists(db_path):
        print(f"[ERROR] 資料庫不存在: {db_path}")
        return
    
    graph_store = SQLiteGraphStore(db_path)
    await graph_store.initialize()
    
    try:
        print("=" * 60)
        print(f"測試文件: {doc_id}")
        print("=" * 60)
        
        # 1. 檢查文件是否存在
        doc_entity = await graph_store.get_entity(doc_id)
        if not doc_entity:
            print(f"[ERROR] 找不到文件: {doc_id}")
            return
        
        print(f"\n[文件資訊]")
        print(f"  名稱: {doc_entity.name}")
        print(f"  ID: {doc_entity.id}")
        props = doc_entity.properties
        print(f"  類型: {props.get('type', 'N/A')}")
        print(f"  來源: {props.get('source', 'N/A')}")
        if 'qa_count' in props:
            print(f"  問答對數量: {props['qa_count']}")
        
        # 2. 查詢該文件的所有 QA
        print(f"\n[查詢 QA 實體]")
        all_qa = await graph_store.get_entities_by_type("QA", limit=10000)
        
        # 篩選屬於該文件的 QA
        doc_qa_list = []
        for qa in all_qa:
            if qa.id.startswith(f"{doc_id}_qa_"):
                doc_qa_list.append(qa)
        
        print(f"  找到 {len(doc_qa_list)} 個 QA 實體")
        
        # 3. 驗證每個 QA 的完整性
        print(f"\n[驗證 QA 完整性]")
        required_fields = ['question', 'answer', 'qa_number', 'qa_title']
        missing_fields_count = 0
        complete_count = 0
        
        for qa in doc_qa_list:
            props = qa.properties
            missing = []
            for field in required_fields:
                if field not in props or not props[field]:
                    missing.append(field)
            
            if missing:
                missing_fields_count += 1
                print(f"  [WARNING] QA {qa.id} 缺少欄位: {', '.join(missing)}")
            else:
                complete_count += 1
        
        print(f"  完整 QA: {complete_count}/{len(doc_qa_list)}")
        if missing_fields_count > 0:
            print(f"  不完整 QA: {missing_fields_count}/{len(doc_qa_list)}")
        
        # 4. 顯示 QA 範例
        print(f"\n[QA 範例 (前 3 個)]")
        for i, qa in enumerate(doc_qa_list[:3], 1):
            props = qa.properties
            print(f"\n  {i}. QA #{props.get('qa_number', 'N/A')}: {props.get('qa_title', 'N/A')}")
            print(f"     問題: {props.get('question', 'N/A')[:80]}...")
            print(f"     答案: {props.get('answer', 'N/A')[:100]}...")
            if 'keywords' in props and props['keywords']:
                print(f"     關鍵字: {', '.join(props['keywords'][:5])}")
            if 'metadata' in props:
                metadata = props['metadata']
                if 'category' in metadata:
                    print(f"     分類: {metadata['category']}")
        
        # 5. 檢查關係
        print(f"\n[檢查關係]")
        all_relations = await graph_store.get_all_relations(limit=10000)
        doc_relations = [r for r in all_relations if r.source_id == doc_id and r.type == "CONTAINS_QA"]
        print(f"  文件到 QA 的關係: {len(doc_relations)} 個")
        
        if len(doc_relations) != len(doc_qa_list):
            print(f"  [WARNING] 關係數量 ({len(doc_relations)}) 與 QA 數量 ({len(doc_qa_list)}) 不一致")
        else:
            print(f"  [OK] 關係數量與 QA 數量一致")
        
        print("\n" + "=" * 60)
        print("測試完成")
        print("=" * 60)
        
    finally:
        await graph_store.close()


async def list_all_documents(db_path: str = "./data/graph_qa.db"):
    """
    列出所有文件
    
    Args:
        db_path: 資料庫路徑
    """
    if not os.path.exists(db_path):
        print(f"[ERROR] 資料庫不存在: {db_path}")
        return
    
    graph_store = SQLiteGraphStore(db_path)
    await graph_store.initialize()
    
    try:
        documents = await graph_store.get_entities_by_type("Document", limit=1000)
        
        print("=" * 60)
        print("所有文件列表")
        print("=" * 60)
        
        for i, doc in enumerate(documents, 1):
            props = doc.properties
            print(f"\n{i}. {doc.name}")
            print(f"   ID: {doc.id}")
            print(f"   類型: {props.get('type', 'N/A')}")
            if 'qa_count' in props:
                print(f"   QA 數量: {props['qa_count']}")
        
        print(f"\n總共 {len(documents)} 個文件")
        
    finally:
        await graph_store.close()


async def test_qa_search(query: str, db_path: str = "./data/graph_qa.db", limit: int = 5):
    """
    測試 QA 搜尋功能
    
    Args:
        query: 搜尋關鍵詞
        db_path: 資料庫路徑
        limit: 結果數量限制
    """
    if not os.path.exists(db_path):
        print(f"[ERROR] 資料庫不存在: {db_path}")
        return
    
    graph_store = SQLiteGraphStore(db_path)
    await graph_store.initialize()
    
    try:
        print("=" * 60)
        print(f"搜尋關鍵詞: {query}")
        print("=" * 60)
        
        all_qa = await graph_store.get_entities_by_type("QA", limit=10000)
        
        results = []
        for qa in all_qa:
            props = qa.properties
            question = props.get("question", "")
            answer = props.get("answer", "")
            keywords = props.get("keywords", [])
            
            # 搜尋問題、答案和關鍵字
            query_lower = query.lower()
            if (query_lower in question.lower() or 
                query_lower in answer.lower() or
                any(query_lower in str(k).lower() for k in keywords)):
                results.append({
                    "id": qa.id,
                    "qa_number": props.get("qa_number", "N/A"),
                    "question": question,
                    "answer": answer,
                    "keywords": keywords
                })
        
        print(f"\n找到 {len(results)} 個相關問答對\n")
        
        for i, result in enumerate(results[:limit], 1):
            print(f"{i}. QA #{result['qa_number']}")
            print(f"   問題: {result['question'][:100]}...")
            print(f"   答案: {result['answer'][:150]}...")
            if result['keywords']:
                print(f"   關鍵字: {', '.join(result['keywords'][:5])}")
            print()
        
    finally:
        await graph_store.close()


async def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="測試 QA 匯入結果")
    parser.add_argument(
        "--doc-id",
        type=str,
        default=None,
        help="要測試的文件 ID"
    )
    parser.add_argument(
        "--list-docs",
        action="store_true",
        help="列出所有文件"
    )
    parser.add_argument(
        "--search",
        type=str,
        default=None,
        help="搜尋關鍵詞"
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="./data/graph_qa.db",
        help="資料庫路徑（預設: ./data/graph_qa.db）"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="搜尋結果數量限制（預設: 5）"
    )
    
    args = parser.parse_args()
    
    if args.list_docs:
        await list_all_documents(args.db_path)
    elif args.search:
        await test_qa_search(args.search, args.db_path, args.limit)
    elif args.doc_id:
        await test_qa_by_document(args.doc_id, args.db_path)
    else:
        print("請指定 --doc-id, --list-docs 或 --search 參數")
        print("\n使用範例:")
        print("  py scripts/test_qa_import.py --list-docs")
        print("  py scripts/test_qa_import.py --doc-id registration_qa")
        print("  py scripts/test_qa_import.py --search 掛號")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[WARNING] 程式被用戶中斷（Ctrl+C）")
        sys.exit(0)
