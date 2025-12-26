"""
查看資料庫中的實體數據
"""
import sqlite3
import json

db_path = "./data/graph.db"

try:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=" * 60)
    print("PDF 處理結果 - 實體數據查詢")
    print("=" * 60)
    
    # 1. 總數
    cursor.execute("SELECT COUNT(*) FROM entities")
    entity_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM relations")
    relation_count = cursor.fetchone()[0]
    
    print(f"\n[總計]")
    print(f"  實體總數: {entity_count}")
    print(f"  關係總數: {relation_count}")
    
    # 2. 實體類型統計
    print(f"\n[實體類型統計]")
    cursor.execute("""
        SELECT type, COUNT(*) as count 
        FROM entities 
        GROUP BY type 
        ORDER BY count DESC
    """)
    for row in cursor.fetchall():
        print(f"  {row['type']}: {row['count']} 個")
    
    # 3. 文件實體
    print(f"\n[文件實體]")
    cursor.execute("""
        SELECT id, name, properties, created_at 
        FROM entities 
        WHERE type = 'Document'
        ORDER BY created_at DESC
    """)
    docs = cursor.fetchall()
    print(f"  文件數量: {len(docs)}")
    for doc in docs[:3]:
        props = json.loads(doc['properties'])
        print(f"\n  📄 {doc['name']}")
        print(f"     ID: {doc['id']}")
        print(f"     建立時間: {doc['created_at']}")
        print(f"     屬性: {props}")
    
    # 4. 查詢文件包含的實體
    if docs:
        doc_id = docs[0][0]  # 第一個文件的 ID
        print(f"\n[文件 '{doc_id}' 包含的實體]")
        
        cursor.execute("""
            SELECT target_id 
            FROM relations 
            WHERE source_id = ? AND type = 'CONTAINS'
        """, (doc_id,))
        target_ids = [row[0] for row in cursor.fetchall()]
        
        print(f"  包含 {len(target_ids)} 個實體")
        print(f"\n  前 10 個實體:")
        for i, entity_id in enumerate(target_ids[:10], 1):
            cursor.execute("SELECT name, type, properties FROM entities WHERE id = ?", (entity_id,))
            entity = cursor.fetchone()
            if entity:
                props = json.loads(entity['properties']) if entity['properties'] else {}
                print(f"    {i}. {entity['name']} ({entity['type']})")
                if props:
                    print(f"       屬性: {props}")
    
    # 5. 其他實體範例
    print(f"\n[其他實體範例（前 10 個）]")
    cursor.execute("""
        SELECT name, type, properties 
        FROM entities 
        WHERE type != 'Document'
        ORDER BY created_at DESC
        LIMIT 10
    """)
    for i, row in enumerate(cursor.fetchall(), 1):
        props = json.loads(row['properties']) if row['properties'] else {}
        print(f"  {i}. {row['name']} ({row['type']})")
        if props:
            print(f"     屬性: {props}")
    
    # 6. 關係統計
    print(f"\n[關係類型統計]")
    cursor.execute("""
        SELECT type, COUNT(*) as count 
        FROM relations 
        GROUP BY type 
        ORDER BY count DESC
    """)
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(f"  {row['type']}: {row['count']} 個")
    else:
        print("  沒有關係數據")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("查詢完成！")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ 錯誤: {str(e)}")
    import traceback
    traceback.print_exc()


