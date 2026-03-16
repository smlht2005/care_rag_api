# 資料庫 Schema 比較說明

**更新時間**：2025-12-29 18:25  
**目的**：說明兩個 PDF 處理腳本使用的資料庫規則

## 結論

**是的，兩個腳本使用相同的資料庫規則（schema）**

## 詳細說明

### 1. 使用的類別

兩個腳本都使用相同的 `SQLiteGraphStore` 類別：

```python
# process_pdf_to_graph.py
graph_store = SQLiteGraphStore(settings.GRAPH_DB_PATH)  # 預設: ./data/graph.db
await graph_store.initialize()

# parse_clinic_manual_pdfs_to_qa_graph.py
graph_store = SQLiteGraphStore(db_path)  # 預設: ./data/graph_qa.db
await graph_store.initialize()
```

### 2. 資料庫 Schema

兩個腳本都調用 `initialize()` 方法，該方法會建立相同的資料表結構：

#### Entities 表
```sql
CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    properties TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)

CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type)
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name)
```

#### Relations 表
```sql
CREATE TABLE IF NOT EXISTS relations (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    type TEXT NOT NULL,
    properties TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (source_id) REFERENCES entities(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES entities(id) ON DELETE CASCADE,
    CHECK (source_id != target_id)
)

CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source_id)
CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target_id)
CREATE INDEX IF NOT EXISTS idx_relations_type ON relations(type)
```

### 3. 資料結構

兩個腳本都使用相同的資料類別：

- `Entity` - 實體類別（id, type, name, properties, created_at, updated_at）
- `Relation` - 關係類別（id, source_id, target_id, type, properties, weight, created_at）

### 4. 唯一差異

**只有資料庫檔案路徑不同**：

| 腳本 | 預設資料庫路徑 | 用途 |
|------|---------------|------|
| `process_pdf_to_graph.py` | `./data/graph.db` | 通用 GraphRAG 圖譜 |
| `parse_clinic_manual_pdfs_to_qa_graph.py` | `./data/graph_qa.db` | 問答知識圖譜 |

## 設計優勢

1. **Schema 一致性**：兩個資料庫使用相同的結構，便於維護和查詢
2. **資料分離**：不同用途的資料儲存在不同檔案，避免混淆
3. **可擴展性**：可以輕鬆添加新的資料庫檔案，使用相同的 schema
4. **工具重用**：查詢工具可以適用於任何使用相同 schema 的資料庫

## 驗證方法

可以通過以下方式驗證兩個資料庫使用相同的 schema：

```python
import asyncio
from app.core.graph_store import SQLiteGraphStore

async def compare_schemas():
    # 檢查 graph.db
    store1 = SQLiteGraphStore("./data/graph.db")
    await store1.initialize()
    stats1 = await store1.get_statistics()
    await store1.close()
    
    # 檢查 graph_qa.db
    store2 = SQLiteGraphStore("./data/graph_qa.db")
    await store2.initialize()
    stats2 = await store2.get_statistics()
    await store2.close()
    
    print("兩個資料庫都使用相同的 schema")
    print(f"graph.db 統計: {stats1}")
    print(f"graph_qa.db 統計: {stats2}")

asyncio.run(compare_schemas())
```

## 結論

兩個腳本使用**完全相同的資料庫規則（schema）**，只是儲存在不同的檔案中。這是正確的設計，確保了：

- ✅ Schema 一致性
- ✅ 資料分離
- ✅ 工具重用性
- ✅ 維護便利性

