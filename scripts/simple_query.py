"""
簡單查詢資料庫實體
"""
import sqlite3
import json
from pathlib import Path

db_path = "./data/graph.db"

if not Path(db_path).exists():
    print(f"❌ 資料庫不存在: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=" * 60)
print("資料庫實體查詢結果")
print("=" * 60)

# 1. 總數統計
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
    LIMIT 5
""")
for row in cursor.fetchall():
    props = json.loads(row['properties'])
    print(f"  ID: {row['id']}")
    print(f"  名稱: {row['name']}")
    print(f"  屬性: {props}")
    print()

# 4. 其他實體範例
print(f"[其他實體範例（前 10 個）]")
cursor.execute("""
    SELECT id, name, type, properties 
    FROM entities 
    WHERE type != 'Document'
    ORDER BY created_at DESC
    LIMIT 10
""")
for i, row in enumerate(cursor.fetchall(), 1):
    props = json.loads(row['properties'])
    print(f"  {i}. {row['name']} ({row['type']})")
    if props:
        print(f"     屬性: {props}")

# 5. 關係統計
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

# 6. 查詢特定文件的實體
print(f"\n[查詢文件包含的實體]")
cursor.execute("""
    SELECT id FROM entities WHERE type = 'Document' LIMIT 1
""")
doc_row = cursor.fetchone()
if doc_row:
    doc_id = doc_row[0]
    print(f"  文件 ID: {doc_id}")
    
    cursor.execute("""
        SELECT target_id 
        FROM relations 
        WHERE source_id = ? AND type = 'CONTAINS'
        LIMIT 10
    """, (doc_id,))
    target_ids = [row[0] for row in cursor.fetchall()]
    
    print(f"  包含 {len(target_ids)} 個實體（顯示前 10 個）:")
    for i, entity_id in enumerate(target_ids, 1):
        cursor.execute("SELECT name, type FROM entities WHERE id = ?", (entity_id,))
        entity_row = cursor.fetchone()
        if entity_row:
            print(f"    {i}. {entity_row['name']} ({entity_row['type']})")

conn.close()

print("\n" + "=" * 60)
print("查詢完成！")
print("=" * 60)


