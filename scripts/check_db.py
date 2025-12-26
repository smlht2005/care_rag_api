"""
檢查資料庫結構和狀態
"""
import sqlite3
import sys
import os

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

def check_database():
    """檢查資料庫狀態"""
    db_path = settings.GRAPH_DB_PATH
    
    if not os.path.exists(db_path):
        print(f"❌ 資料庫檔案不存在: {db_path}")
        return False
    
    print(f"✅ 資料庫檔案存在: {db_path}")
    print(f"   檔案大小: {os.path.getsize(db_path)} bytes")
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 檢查資料表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"\n📊 資料表 ({len(tables)} 個):")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   - {table}: {count} 筆記錄")
        
        # 實體類型統計
        print(f"\n📈 實體類型統計:")
        cursor.execute("""
            SELECT type, COUNT(*) as count 
            FROM entities 
            GROUP BY type 
            ORDER BY count DESC
        """)
        for row in cursor.fetchall():
            print(f"   - {row['type']}: {row['count']} 個")
        
        # 關係類型統計
        print(f"\n🔗 關係類型統計:")
        cursor.execute("""
            SELECT type, COUNT(*) as count 
            FROM relations 
            GROUP BY type 
            ORDER BY count DESC
        """)
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                print(f"   - {row['type']}: {row['count']} 個")
        else:
            print("   - 沒有關係數據")
        
        # 文件實體範例
        print(f"\n📄 文件實體範例（前 3 個）:")
        cursor.execute("""
            SELECT id, name, properties 
            FROM entities 
            WHERE type = 'Document'
            ORDER BY created_at DESC
            LIMIT 3
        """)
        for row in cursor.fetchall():
            import json
            props = json.loads(row['properties'])
            print(f"   - {row['name']}")
            print(f"     ID: {row['id']}")
            print(f"     屬性: {props}")
        
        # 其他實體範例
        print(f"\n🏷️ 其他實體範例（前 5 個）:")
        cursor.execute("""
            SELECT name, type, properties 
            FROM entities 
            WHERE type != 'Document'
            ORDER BY created_at DESC
            LIMIT 5
        """)
        for row in cursor.fetchall():
            import json
            props = json.loads(row['properties'])
            print(f"   - {row['name']} ({row['type']})")
            if props:
                print(f"     屬性: {props}")
        
        # 檢查索引
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
        indexes = [row[0] for row in cursor.fetchall()]
        print(f"\n🔍 索引 ({len(indexes)} 個):")
        for idx in indexes:
            print(f"   - {idx}")
        
        conn.close()
        print("\n✅ 資料庫檢查完成！")
        return True
        
    except Exception as e:
        print(f"❌ 檢查資料庫時發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_database()

