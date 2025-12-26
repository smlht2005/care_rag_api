"""
初始化 GraphRAG 資料庫腳本
"""
import os
import sys
import asyncio

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.core.graph_store import SQLiteGraphStore

async def init_graph():
    """初始化 GraphRAG DB schema"""
    print("初始化 GraphRAG DB schema...")
    
    # 建立資料目錄
    data_dir = os.path.dirname(settings.GRAPH_DB_PATH)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"建立資料目錄: {data_dir}")
    
    # 初始化 GraphStore
    try:
        graph_store = SQLiteGraphStore(settings.GRAPH_DB_PATH)
        success = await graph_store.initialize()
        
        if success:
            print(f"Graph DB 路徑: {settings.GRAPH_DB_PATH}")
            print("GraphRAG DB schema 初始化完成！")
            
            # 關閉連線
            await graph_store.close()
        else:
            print("GraphRAG DB schema 初始化失敗！")
            sys.exit(1)
            
    except Exception as e:
        print(f"錯誤: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(init_graph())

