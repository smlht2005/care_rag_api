"""
查詢問答知識圖譜
查詢 graph_qa.db 中的問答對和知識點

更新時間：2025-12-30 10:30
作者：AI Assistant
修改摘要：修正 Windows 終端編碼問題，移除 emoji 並設定 UTF-8 編碼
更新時間：2025-12-29 18:37
作者：AI Assistant
修改摘要：修復 get_all_entities 和 get_all_relations 方法調用錯誤，使用 get_statistics() 獲取總數
更新時間：2025-12-29 15:05
作者：AI Assistant
修改摘要：建立問答圖譜查詢腳本
"""
import os
import sys
import asyncio
from pathlib import Path

# 設定 Windows 終端編碼
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.graph_store import SQLiteGraphStore


async def query_qa_graph(db_path: str = "./data/graph_qa.db"):
    """
    查詢問答知識圖譜
    
    Args:
        db_path: 圖資料庫路徑
    """
    if not os.path.exists(db_path):
        print(f"[ERROR] 資料庫不存在: {db_path}")
        print(f"請先執行: python scripts/parse_clinic_manual_pdfs_to_qa_graph.py")
        return
    
    graph_store = SQLiteGraphStore(db_path)
    await graph_store.initialize()
    
    try:
        print("=" * 60)
        print("問答知識圖譜查詢")
        print("=" * 60)
        
        # 1. 統計資訊
        print("\n[統計資訊]")
        
        # 文件數量
        documents = await graph_store.get_entities_by_type("Document", limit=1000)
        print(f"文件數量: {len(documents)}")
        
        # 問答對數量
        qa_entities = await graph_store.get_entities_by_type("QA", limit=10000)
        print(f"問答對數量: {len(qa_entities)}")
        
        # 知識點數量
        kp_entities = await graph_store.get_entities_by_type("KnowledgePoint", limit=10000)
        print(f"知識點數量: {len(kp_entities)}")
        
        # 總實體數和總關係數（使用統計方法）
        stats = await graph_store.get_statistics()
        print(f"總實體數: {stats.get('total_entities', 0)}")
        print(f"總關係數: {stats.get('total_relations', 0)}")
        
        # 獲取所有關係（用於關係類型統計）
        all_relations = await graph_store.get_all_relations(limit=10000)
        
        # 2. 顯示文件列表
        print("\n[文件列表]")
        for i, doc in enumerate(documents[:10], 1):
            print(f"{i}. {doc.name}")
            print(f"   ID: {doc.id}")
            props = doc.properties
            if "qa_pairs_count" in props:
                print(f"   問答對: {props['qa_pairs_count']}")
            if "knowledge_points_count" in props:
                print(f"   知識點: {props['knowledge_points_count']}")
        
        # 3. 顯示問答對範例
        print("\n[問答對範例]")
        for i, qa in enumerate(qa_entities[:5], 1):
            print(f"\n{i}. {qa.name[:80]}...")
            props = qa.properties
            if "question" in props:
                question = props["question"][:100]
                print(f"   問題: {question}...")
            if "answer" in props:
                answer = props["answer"][:150]
                print(f"   答案: {answer}...")
        
        # 4. 顯示知識點範例
        print("\n[知識點範例]")
        for i, kp in enumerate(kp_entities[:5], 1):
            print(f"\n{i}. {kp.name}")
            props = kp.properties
            if "keywords" in props and props["keywords"]:
                print(f"   關鍵詞: {', '.join(props['keywords'][:5])}")
        
        # 5. 關係統計
        print("\n[關係類型統計]")
        relation_types = {}
        for rel in all_relations:
            rel_type = rel.type
            relation_types[rel_type] = relation_types.get(rel_type, 0) + 1
        
        for rel_type, count in sorted(relation_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {rel_type}: {count}")
        
    finally:
        await graph_store.close()


async def search_qa(query: str, db_path: str = "./data/graph_qa.db", limit: int = 10):
    """
    搜尋問答對
    
    Args:
        query: 搜尋關鍵詞
        db_path: 圖資料庫路徑
        limit: 返回結果數量限制
    """
    if not os.path.exists(db_path):
        print(f"[ERROR] 資料庫不存在: {db_path}")
        return
    
    graph_store = SQLiteGraphStore(db_path)
    await graph_store.initialize()
    
    try:
        print(f"搜尋關鍵詞: {query}")
        print("=" * 60)
        
        # 將查詢字串拆成多個 token（以空白分隔），全部轉小寫
        tokens = [t.strip().lower() for t in query.split() if t.strip()]
        simple_query = query.lower()
        
        # 搜尋問答對
        qa_entities = await graph_store.get_entities_by_type("QA", limit=10000)
        
        results = []
        for qa in qa_entities:
            props = qa.properties
            
            title = props.get("qa_title") or getattr(qa, "name", "") or ""
            scenario = props.get("scenario", "")
            keywords = props.get("keywords", [])
            keywords_text = ",".join(str(k) for k in keywords) if keywords else ""
            question = props.get("question", "")
            answer = props.get("answer", "")
            notes = props.get("notes", "")
            
            # 建立可搜尋文本，涵蓋標題 / 情境 / 關鍵字 / 問題 / 答案 / 備註
            search_text = "\n".join([
                str(title),
                str(scenario),
                keywords_text,
                str(question),
                str(answer),
                str(notes),
            ]).lower()
            
            matched = False
            if tokens:
                # AND 模式：所有 token 都需出現在 search_text 中
                matched = all(t in search_text for t in tokens)
            else:
                # 沒有有效 token 時，退回單一字串在 question/answer 中的比對
                if simple_query and (
                    simple_query in question.lower() or simple_query in answer.lower()
                ):
                    matched = True
            
            if matched:
                results.append({
                    "id": qa.id,
                    "question": question,
                    "answer": answer
                })
        
        print(f"\n找到 {len(results)} 個相關問答對\n")
        
        for i, result in enumerate(results[:limit], 1):
            print(f"{i}. 問題: {result['question'][:100]}...")
            print(f"   答案: {result['answer'][:200]}...")
            print()
        
    finally:
        await graph_store.close()


async def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="查詢問答知識圖譜")
    parser.add_argument(
        "--db-path",
        type=str,
        default="./data/graph_qa.db",
        help="圖資料庫路徑（預設: ./data/graph_qa.db）"
    )
    parser.add_argument(
        "--search",
        type=str,
        default=None,
        help="搜尋關鍵詞"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="搜尋結果數量限制（預設: 10）"
    )
    
    args = parser.parse_args()
    
    if args.search:
        await search_qa(args.search, args.db_path, args.limit)
    else:
        await query_qa_graph(args.db_path)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[WARNING] 程式被用戶中斷（Ctrl+C）")
        sys.exit(0)

