# PDF 重複處理時的數據行為分析

**更新時間：2025-12-26 16:20**  
**作者：AI Assistant**  
**修改摘要：分析重複轉換 PDF 到 GraphRAG 資料庫時，數據是追加還是覆蓋的行為**

---

## 問題

重複執行 PDF 轉換腳本時，表格數據是**追加（append）**還是**覆蓋（override）**？

## 核心發現

### 1. 資料庫操作：使用 `INSERT OR REPLACE`

**位置**：`app/core/graph_store.py`

**實體保存**（行 324）：
```python
await cursor.execute("""
    INSERT OR REPLACE INTO entities (id, type, name, properties, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?)
""", (...))
```

**關係保存**（行 389）：
```python
await cursor.execute("""
    INSERT OR REPLACE INTO relations 
    (id, source_id, target_id, type, properties, weight, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", (...))
```

**關鍵點**：
- `INSERT OR REPLACE` 表示：如果 ID 已存在，會**覆蓋**（REPLACE）現有記錄
- 如果 ID 不存在，會**插入**（INSERT）新記錄

### 2. 文件 ID 生成邏輯

**位置**：`scripts/process_pdf_to_graph.py`（行 154-156）

```python
if document_id is None:
    pdf_name = Path(pdf_path).stem
    document_id = f"doc_{pdf_name}_{str(uuid.uuid4())[:8]}"
```

**行為**：
- 如果**沒有指定** `--doc-id` 參數，每次運行都會生成**新的 UUID**
- 例如：`doc_1051219長期照護2.0核定本_a79f3355` → `doc_1051219長期照護2.0核定本_4c986a6d`
- 如果**指定了** `--doc-id`，則使用指定的 ID

### 3. 實體 ID 生成邏輯

**位置**：`app/core/entity_extractor.py`

```python
entity = Entity(
    id=str(uuid.uuid4()),  # 每次提取都生成新的 UUID
    type=item.get("type", "Concept"),
    name=item.get("name", ""),
    ...
)
```

**行為**：
- 每個實體都使用 `uuid.uuid4()` 生成**唯一的 ID**
- **即使實體名稱相同**，每次提取都會生成**不同的 ID**
- 例如：第一次提取 "張文瓊" → ID: `abc-123-def`
- 第二次提取 "張文瓊" → ID: `xyz-789-ghi`（不同的 ID）

### 4. 關係 ID 生成邏輯

**位置**：`app/core/entity_extractor.py` 和 `app/services/graph_builder.py`

**提取的關係**（entity_extractor.py）：
```python
relation = Relation(
    id=str(uuid.uuid4()),  # 每次提取都生成新的 UUID
    ...
)
```

**CONTAINS 關係**（graph_builder.py 行 109）：
```python
relation = Relation(
    id=f"{document_id}_contains_{entity.id}",  # 基於 document_id 和 entity.id
    ...
)
```

**行為**：
- 提取的關係：每次提取都生成新的 UUID
- CONTAINS 關係：基於 `document_id` 和 `entity.id`，如果兩者都相同，ID 會相同

## 實際行為分析

### 場景 1：使用預設行為（不指定 `--doc-id`）

**第一次運行**：
```
document_id = "doc_1051219長期照護2.0核定本_a79f3355"
實體 "張文瓊" → ID: "abc-123-def"
關係 → ID: "rel-001"
```

**第二次運行**（相同 PDF）：
```
document_id = "doc_1051219長期照護2.0核定本_4c986a6d"  ← 新的 UUID
實體 "張文瓊" → ID: "xyz-789-ghi"  ← 新的 UUID
關係 → ID: "rel-002"  ← 新的 UUID
```

**結果**：**追加**（因為所有 ID 都不同）

### 場景 2：指定相同的 `--doc-id`

**第一次運行**：
```bash
python scripts/process_pdf_to_graph.py "file.pdf" --doc-id "my_doc_001"
```
```
document_id = "my_doc_001"
實體 "張文瓊" → ID: "abc-123-def"
CONTAINS 關係 → ID: "my_doc_001_contains_abc-123-def"
```

**第二次運行**（相同 `--doc-id`）：
```bash
python scripts/process_pdf_to_graph.py "file.pdf" --doc-id "my_doc_001"
```
```
document_id = "my_doc_001"  ← 相同
實體 "張文瓊" → ID: "xyz-789-ghi"  ← 新的 UUID（因為實體 ID 是隨機生成的）
CONTAINS 關係 → ID: "my_doc_001_contains_xyz-789-ghi"  ← 不同（因為 entity.id 不同）
```

**結果**：
- **實體**：追加（因為實體 ID 是隨機生成的，即使名稱相同）
- **CONTAINS 關係**：追加（因為 entity.id 不同）
- **提取的關係**：追加（因為關係 ID 是隨機生成的）

### 場景 3：實體去重邏輯

**位置**：`app/core/entity_extractor.py`（`_deduplicate_entities` 方法）

```python
def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
    """實體去重和合併"""
    seen = {}
    result = []
    
    for entity in entities:
        # 使用 name 和 type 作為唯一鍵
        key = (entity.name.lower(), entity.type)
        
        if key not in seen:
            seen[key] = entity
            result.append(entity)
        else:
            # 合併屬性
            existing = seen[key]
            existing.properties.update(entity.properties)
    
    return result
```

**行為**：
- 在**單次提取**中，會根據 `(name, type)` 去重
- 但去重後的實體仍然使用**原始的 UUID**（第一次出現的實體 ID）
- **跨次運行**：不會去重（因為是不同次運行）

## 問題總結

### 當前行為

1. **預設行為（不指定 `--doc-id`）**：
   - ✅ **追加**：每次運行生成新的 document_id，所有實體和關係 ID 都不同
   - ⚠️ **問題**：會產生重複的實體（相同名稱但不同 ID）

2. **指定相同 `--doc-id`**：
   - ✅ **追加**：實體和關係 ID 仍然是隨機生成的，會追加
   - ⚠️ **問題**：無法真正覆蓋舊數據，會產生重複

3. **資料庫層面**：
   - ✅ 使用 `INSERT OR REPLACE`，如果 ID 相同會覆蓋
   - ⚠️ 但由於 ID 是隨機生成的，實際上不會覆蓋

## 建議的改進方案

### 方案 1：實體 ID 基於名稱和類型（推薦）

**修改**：`app/core/entity_extractor.py`

```python
import hashlib

# 生成確定性的實體 ID
def generate_entity_id(name: str, type: str) -> str:
    """基於名稱和類型生成確定性的 ID"""
    key = f"{type}:{name}".lower()
    hash_obj = hashlib.md5(key.encode('utf-8'))
    return hash_obj.hexdigest()[:16]  # 16 字元 ID

entity = Entity(
    id=generate_entity_id(item.get("name", ""), item.get("type", "Concept")),
    ...
)
```

**優點**：
- 相同名稱和類型的實體會有相同的 ID
- 重複處理時會覆蓋舊實體（更新屬性）
- 避免重複實體

**缺點**：
- 如果實體名稱有變化（如 "張文瓊" vs "張 文瓊"），會生成不同的 ID

### 方案 2：添加文件級別的清理選項

**修改**：`scripts/process_pdf_to_graph.py`

```python
async def process_pdf_to_graph(
    pdf_path: str,
    document_id: Optional[str] = None,
    chunk_size: int = 2000,
    overwrite: bool = False  # 新增參數
):
    if overwrite and document_id:
        # 刪除舊的文件實體和相關關係
        await graph_store.delete_entity(document_id)
        # 刪除相關的 CONTAINS 關係
        # ...
```

**優點**：
- 明確控制是否覆蓋
- 保留靈活性

**缺點**：
- 需要手動指定 `--overwrite` 和 `--doc-id`

### 方案 3：實體名稱模糊匹配去重

**修改**：在保存實體前，檢查是否有相似名稱的實體

```python
# 在 add_entity 前檢查
existing_entity = await graph_store.search_entities(entity.name)
if existing_entity and is_similar(entity.name, existing_entity.name):
    # 更新現有實體而不是創建新的
    entity.id = existing_entity.id
```

**優點**：
- 自動處理相似實體
- 減少重複

**缺點**：
- 需要定義相似度閾值
- 可能誤合併不同實體

## 當前狀態總結

| 場景 | 實體行為 | 關係行為 | 結果 |
|------|---------|---------|------|
| 預設（不指定 `--doc-id`） | 追加（新 UUID） | 追加（新 UUID） | ✅ 追加，但會重複 |
| 指定相同 `--doc-id` | 追加（新 UUID） | 追加（新 UUID） | ✅ 追加，但會重複 |
| 指定相同 `--doc-id` + 相同實體 ID | 覆蓋（REPLACE） | 覆蓋（REPLACE） | ⚠️ 但實體 ID 是隨機的，不會發生 |

## 相關文件

- [GraphStore 實作](../app/core/graph_store.py)
- [PDF 處理腳本](../scripts/process_pdf_to_graph.py)
- [圖構建服務](../app/services/graph_builder.py)

## 解決方案實作

### 已實作：`--overwrite` 選項

**位置**：`scripts/process_pdf_to_graph.py`

**使用方法**：
```bash
python scripts/process_pdf_to_graph.py "data/example/file.pdf" --overwrite
```

**行為**：
1. 在處理 PDF 前，檢查是否存在相同來源的 Document 實體
2. 如果找到匹配的實體（通過 `properties.source` 字段），會：
   - 刪除所有相關的 chunk 實體（`{document_id}_chunk_*`）
   - 刪除主文件實體（級聯刪除會自動刪除 CONTAINS 關係）
3. 然後繼續正常處理 PDF

**注意事項**：
- 只會刪除 Document 類型的實體和相關的 CONTAINS 關係
- 其他實體（Person、Organization 等）不會被刪除，因為它們可能被多個文件共享
- 如果實體 ID 是隨機生成的，即使名稱相同，也不會被刪除（這是預期行為）

**範例輸出**：
```
[步驟 2.5/5] 檢查現有數據...
  發現現有文件實體: doc_file_abc123 (來源: C:\path\to\file.pdf)
    ✅ 已刪除區塊實體: doc_file_abc123_chunk_1
    ✅ 已刪除區塊實體: doc_file_abc123_chunk_2
    ...
    ✅ 已刪除文件實體: doc_file_abc123
  ✅ 已清理 66 個現有實體（包含 1 個文件實體）
```

## 更新歷史

- **2025-12-26 16:27**: 實作 `--overwrite` 選項，當重複處理相同來源 PDF 時自動清理現有數據
- **2025-12-26 16:20**: 初始分析，發現當前行為是追加而非覆蓋，並提供改進建議

