# 資料庫查詢問答

## Q: 如何查看 PDF 處理後的實體數據？

**A:** 使用查詢腳本：

### 方法 1: 使用 view_entities.py（推薦）

```powershell
python scripts\view_entities.py
```

**輸出內容**：
- 實體總數和關係總數
- 實體類型統計
- 文件實體列表
- 文件包含的實體
- 其他實體範例
- 關係類型統計

### 方法 2: 使用 check_db.py

```powershell
python scripts\check_db.py
```

**輸出內容**：
- 資料庫檔案資訊
- 資料表記錄數
- 實體類型統計
- 關係類型統計
- 索引資訊

### 方法 3: 使用 query_entities.py（非同步版本）

```powershell
python scripts\query_entities.py
```

**輸出內容**：
- 完整的實體和關係查詢
- 使用 GraphStore API

---

## Q: 從終端輸出看到什麼結果？

**A:** 根據終端輸出（行 856-1003）：

### PDF 處理結果

```
✅ 文字提取完成，總長度: 128197 字元
✅ 服務初始化完成
文件 ID: doc_1051219長期照護2.0核定本_95057e44
文字過長 (128197 字元)，進行分塊處理...
分為 65 個區塊
✅ 所有區塊處理完成
   總實體數: 65
   總關係數: 0
✅ 向量資料庫更新完成
```

### 分析

1. **PDF 處理成功**
   - 提取了 128,197 字元的文字
   - 分為 65 個區塊處理

2. **實體提取結果**
   - 總實體數: 65 個
   - 每個區塊提取了 1 個實體
   - 這些實體是通過降級方案（規則基礎提取）獲得的

3. **關係提取結果**
   - 總關係數: 0 個
   - 因為 LLM 服務是 Stub，無法提取真實的關係

4. **文件 ID**
   - `doc_1051219長期照護2.0核定本_95057e44`

---

## Q: 為什麼只有 65 個實體，沒有關係？

**A:** 原因分析：

### 1. 實體提取

**為什麼有 65 個實體**：
- 每個區塊（2000 字元）提取了 1 個實體
- 這些實體是通過 `_rule_based_entity_extraction()` 降級方案獲得的
- 規則基礎提取使用正則表達式提取大寫開頭的詞

**為什麼只有 1 個實體**：
- LLM 服務是 Stub，返回的不是 JSON 格式
- JSON 解析失敗，降級到規則基礎提取
- 規則基礎提取可能只提取到 1 個實體

### 2. 關係提取

**為什麼沒有關係**：
- 關係提取依賴於實體提取
- 如果實體提取失敗或實體數量少，關係提取也會失敗
- LLM 服務是 Stub，無法返回 JSON 格式的關係

---

## Q: 如何改善實體和關係提取？

**A:** 有幾個選項：

### 選項 1: 實作真正的 LLM 整合（推薦）

```python
# 在 LLMService 中實作真正的 API 呼叫
# 確保返回 JSON 格式的實體和關係
```

**優點**：
- 真正的 AI 功能
- 可以提取真實的實體和關係
- 準確度高

**缺點**：
- 需要 API Key
- 需要網路連線
- 可能產生費用

### 選項 2: 改進規則基礎提取

```python
# 在 _rule_based_entity_extraction() 中添加更多規則
# 例如：提取日期、數字、專有名詞等
```

**優點**：
- 不需要 API
- 可以提取更多實體

**缺點**：
- 準確度較低
- 無法提取關係

### 選項 3: 使用本地 LLM

```python
# 使用本地運行的 LLM（如 Ollama）
# 不需要網路連線，但需要本地資源
```

---

## Q: 如何驗證實體數據是否正確？

**A:** 檢查步驟：

### 1. 查看實體類型

```powershell
python scripts\view_entities.py
```

**應該看到**：
- Document 類型：1 個（主文件）
- Concept 類型：64 個（從規則基礎提取）

### 2. 查看實體名稱

檢查實體名稱是否合理：
- 是否包含 PDF 中的關鍵詞？
- 是否包含專有名詞？

### 3. 查看文件屬性

檢查文件實體的屬性：
- `source`: PDF 文件路徑
- `chunks`: 區塊數量（應該是 65）
- `total_length`: 總長度（應該是 128197）

---

## Q: CropBox 警告是什麼？

**A:** 這是 PDF 處理庫的警告訊息：

### 原因

```
CropBox missing from /Page, defaulting to MediaBox
```

- PDF 頁面缺少 `CropBox` 定義
- 處理庫自動使用 `MediaBox` 作為替代
- 這是**警告**，不是錯誤

### 影響

- **不影響功能**：文字提取仍能正常進行
- **可能影響格式**：頁面邊界可能不準確

### 解決方案

可以忽略這些警告，或：
1. 使用其他 PDF 處理庫
2. 在處理前修復 PDF 文件
3. 過濾警告訊息

---

## Q: 如何查詢特定實體的詳細資訊？

**A:** 使用 GraphStore API：

```python
import asyncio
from app.core.graph_store import SQLiteGraphStore
from app.config import settings

async def query_entity(entity_id):
    store = SQLiteGraphStore(settings.GRAPH_DB_PATH)
    await store.initialize()
    
    entity = await store.get_entity(entity_id)
    if entity:
        print(f"名稱: {entity.name}")
        print(f"類型: {entity.type}")
        print(f"屬性: {entity.properties}")
    
    await store.close()

# 使用
asyncio.run(query_entity("entity_id_here"))
```

---

## Q: 如何查詢實體間的關係？

**A:** 使用 GraphStore 的查詢方法：

```python
# 查詢鄰居
neighbors = await store.get_neighbors(entity_id)

# 查詢路徑
paths = await store.get_path(source_id, target_id)

# 查詢子圖
subgraph = await store.get_subgraph([entity_id1, entity_id2])
```

---

## 相關檔案

- `scripts/view_entities.py` - 查看實體數據（推薦）
- `scripts/check_db.py` - 檢查資料庫狀態
- `scripts/query_entities.py` - 完整查詢腳本
- `app/core/graph_store.py` - GraphStore API


