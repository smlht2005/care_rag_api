"""
測試導入和依賴
"""
import sys
import os

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("Python 版本:", sys.version)
print("Python 路徑:", sys.executable)
print("\n測試導入 aiosqlite...")

try:
    import aiosqlite
    print(f"✅ aiosqlite 導入成功，版本: {aiosqlite.__version__}")
except ImportError as e:
    print(f"❌ aiosqlite 導入失敗: {e}")
    sys.exit(1)

print("\n測試導入 GraphStore...")

try:
    from app.core.graph_store import SQLiteGraphStore, Entity, Relation
    print("✅ GraphStore 導入成功")
    
    # 測試實例化
    store = SQLiteGraphStore("./test.db")
    print("✅ SQLiteGraphStore 實例化成功")
    
except Exception as e:
    print(f"❌ GraphStore 導入或實例化失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n所有測試通過！")


