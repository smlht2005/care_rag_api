"""
查詢資料庫中的實體數據
"""
import asyncio
import sys
import os

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.core.graph_store import SQLiteGraphStore

async def query_entities():
    """查詢實體數據"""
    print("=" * 60)
    print("查詢資料庫中的實體數據")
    print("=" * 60)
    
    graph_store = SQLiteGraphStore(settings.GRAPH_DB_PATH)
    await graph_store.initialize()
    
    try:
        # 1. 查詢所有文件實體
        print("\n[1] 文件實體:")
        documents = await graph_store.get_entities_by_type("Document", limit=10)
        print(f"  總數: {len(documents)}")
        for doc in documents[:5]:  # 只顯示前 5 個
            print(f"  - ID: {doc.id}")
            print(f"    名稱: {doc.name}")
            print(f"    屬性: {doc.properties}")
            print()
        
        # 2. 統計各類型實體
        print("\n[2] 實體類型統計:")
        conn = graph_store.conn
        async with conn.cursor() as cursor:
            await cursor.execute("""
                SELECT type, COUNT(*) as count 
                FROM entities 
                GROUP BY type 
                ORDER BY count DESC
            """)
            rows = await cursor.fetchall()
            for row in rows:
                print(f"  {row['type']}: {row['count']} 個")
        
        # 3. 查詢特定文件的所有實體
        if documents:
            doc_id = documents[0].id
            print(f"\n[3] 文件 '{doc_id}' 的實體:")
            
            # 取得文件的關係（CONTAINS）
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT target_id 
                    FROM relations 
                    WHERE source_id = ? AND type = 'CONTAINS'
                """, (doc_id,))
                target_rows = await cursor.fetchall()
                target_ids = [row[0] for row in target_rows]
            
            print(f"  包含 {len(target_ids)} 個實體")
            for i, entity_id in enumerate(target_ids[:10], 1):  # 只顯示前 10 個
                entity = await graph_store.get_entity(entity_id)
                if entity:
                    print(f"  {i}. {entity.name} ({entity.type})")
                    if entity.properties:
                        props = {k: v for k, v in list(entity.properties.items())[:3]}
                        print(f"     屬性: {props}")
        
        # 4. 查詢關係統計
        print("\n[4] 關係類型統計:")
        async with conn.cursor() as cursor:
            await cursor.execute("""
                SELECT type, COUNT(*) as count 
                FROM relations 
                GROUP BY type 
                ORDER BY count DESC
            """)
            rows = await cursor.fetchall()
            if rows:
                for row in rows:
                    print(f"  {row['type']}: {row['count']} 個")
            else:
                print("  沒有關係數據")
        
        # 5. 查詢總數
        print("\n[5] 總計:")
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT COUNT(*) FROM entities")
            row = await cursor.fetchone()
            entity_count = row[0] if row else 0
            
            await cursor.execute("SELECT COUNT(*) FROM relations")
            row = await cursor.fetchone()
            relation_count = row[0] if row else 0
            
            print(f"  實體總數: {entity_count}")
            print(f"  關係總數: {relation_count}")
        
        # 6. 查詢最近的實體（按建立時間）
        print("\n[6] 最近的實體（前 10 個）:")
        async with conn.cursor() as cursor:
            await cursor.execute("""
                SELECT id, name, type, created_at 
                FROM entities 
                ORDER BY created_at DESC 
                LIMIT 10
            """)
            rows = await cursor.fetchall()
            for i, row in enumerate(rows, 1):
                print(f"  {i}. {row['name']} ({row['type']}) - {row['created_at']}")
        
    except Exception as e:
        print(f"❌ 查詢錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await graph_store.close()
    
    print("\n" + "=" * 60)
    print("查詢完成！")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(query_entities())

