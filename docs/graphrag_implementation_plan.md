# GraphRAG Graph Store 完整實作計劃

## 文檔版本
- **版本**: 1.0
- **建立日期**: 2025-12-26
- **最後更新**: 2025-12-26
- **狀態**: 待執行

---

## 目錄

1. [專案概述](#專案概述)
2. [架構設計](#架構設計)
3. [資料模型](#資料模型)
4. [實作步驟](#實作步驟)
5. [代碼審查發現](#代碼審查發現)
6. [改進建議](#改進建議)
7. [執行計劃](#執行計劃)
8. [測試策略](#測試策略)
9. [風險評估](#風險評估)

---

## 專案概述

### 目標
建立完整的 GraphRAG（Graph-based Retrieval-Augmented Generation）系統，實作圖結構儲存、實體提取、關係提取和圖查詢功能，並與現有的 RAG 系統整合。

### 核心功能
1. **圖結構儲存**：使用 SQLite 儲存實體和關係
2. **實體提取**：從文件內容中提取實體
3. **關係提取**：從文件內容中提取實體間的關係
4. **圖查詢**：支援多跳查詢、路徑查詢、鄰居查詢
5. **圖構建**：自動從文件構建圖結構
6. **查詢整合**：將圖查詢結果與向量檢索結果融合

---

## 架構設計

### 完整架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                        客戶端層                               │
│  REST Client | SSE Client | WebSocket Client                │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                         API 層                               │
│  query.py | documents.py | health.py                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                        核心層                                │
│  GraphOrchestrator ──→ GraphStore ──→ SQLiteGraphStore     │
│         │                    │                              │
│         └──→ EntityExtractor ──→ GraphBuilder              │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                        服務層                                │
│  RAGService ──→ VectorService ──→ LLMService              │
│       │              │                │                    │
│       └──→ CacheService                                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                        儲存層                                │
│  SQLite DB | Vector DB | Redis Cache                        │
└─────────────────────────────────────────────────────────────┘
```

### 資料流程

```
用戶查詢
  ↓
檢查快取
  ↓ (Miss)
向量檢索 → 取得相關文件
  ↓
實體提取 → 識別實體
  ↓
圖查詢 → 查詢相關實體和關係
  ├─→ 鄰居查詢
  ├─→ 路徑查詢
  └─→ 子圖查詢
  ↓
結果融合 → 合併向量和圖結果
  ↓
重排序 → 根據相關性排序
  ↓
LLM 生成 → 使用增強後的上下文
  ↓
存入快取
  ↓
返回結果
```

---

## 資料模型

### Entity (實體)

```python
@dataclass
class Entity:
    id: str                    # 唯一識別碼 (UUID)
    type: str                  # 實體類型 (Person, Document, Concept, etc.)
    name: str                  # 實體名稱
    properties: Dict[str, Any] # 實體屬性 (JSON)
    created_at: datetime       # 建立時間
    updated_at: datetime       # 更新時間
```

**實體類型範例**：
- `Person`: 人物
- `Document`: 文件
- `Concept`: 概念
- `Location`: 地點
- `Organization`: 組織
- `Event`: 事件

### Relation (關係)

```python
@dataclass
class Relation:
    id: str                    # 唯一識別碼 (UUID)
    source_id: str             # 來源實體 ID
    target_id: str             # 目標實體 ID
    type: str                  # 關係類型
    properties: Dict[str, Any] # 關係屬性 (JSON)
    weight: float              # 關係權重 (0.0-1.0)
    created_at: datetime       # 建立時間
```

**關係類型範例**：
- `CONTAINS`: 包含關係
- `RELATED_TO`: 相關關係
- `MENTIONS`: 提及關係
- `AUTHORED_BY`: 作者關係
- `LOCATED_IN`: 位置關係
- `PART_OF`: 部分關係

### 資料庫 Schema

```sql
-- Entities 表
CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    properties TEXT NOT NULL,  -- JSON 字串
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);

-- Relations 表
CREATE TABLE IF NOT EXISTS relations (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    type TEXT NOT NULL,
    properties TEXT NOT NULL,  -- JSON 字串
    weight REAL DEFAULT 1.0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (source_id) REFERENCES entities(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES entities(id) ON DELETE CASCADE,
    CHECK (source_id != target_id)  -- 防止自循環
);

CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source_id);
CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target_id);
CREATE INDEX IF NOT EXISTS idx_relations_type ON relations(type);
CREATE INDEX IF NOT EXISTS idx_relations_weight ON relations(weight);
```

---

## 實作步驟

### 階段一：核心基礎設施（高優先級）

#### 1.1 建立資料模型類別

**檔案**: `app/core/graph_store.py`

- [ ] 實作 `Entity` 類別（使用 `@dataclass`）
- [ ] 實作 `Relation` 類別（使用 `@dataclass`）
- [ ] 添加 Pydantic 驗證（選用）

#### 1.2 實作 GraphStore 抽象介面

**檔案**: `app/core/graph_store.py`

- [ ] 建立 `GraphStore` 抽象基類（ABC）
- [ ] 定義所有抽象方法：
  - `add_entity()`, `get_entity()`, `delete_entity()`
  - `add_relation()`, `get_relation()`, `delete_relation()`
  - `get_entities_by_type()`, `search_entities()`
  - `get_neighbors()`, `get_path()`, `get_subgraph()`
  - `initialize()` - 初始化資料庫

#### 1.3 實作 SQLiteGraphStore

**檔案**: `app/core/graph_store.py`

- [ ] 使用 `aiosqlite` 進行非同步操作
- [ ] 實作資料庫連線管理
- [ ] 實作 `initialize()` 方法（建立資料表）
- [ ] 實作所有 CRUD 操作
- [ ] 實作事務處理（批次操作）
- [ ] 實作 JSON 序列化/反序列化
- [ ] 實作級聯刪除

#### 1.4 實作 MemoryGraphStore（測試用）

**檔案**: `app/core/graph_store.py`

- [ ] 實作記憶體版本的 GraphStore
- [ ] 使用字典儲存實體和關係
- [ ] 實作所有查詢方法

### 階段二：實體和關係提取（高優先級）

#### 2.1 建立實體提取器

**檔案**: `app/core/entity_extractor.py` (新建)

- [ ] 建立 `EntityExtractor` 類別
- [ ] 實作 LLM-based 實體提取
- [ ] 實作基於規則的實體提取（選用）
- [ ] 實作實體去重和合併
- [ ] 實作實體類型分類

**方法簽名**：
```python
async def extract_entities(self, text: str) -> List[Entity]
async def extract_relations(self, text: str, entities: List[Entity]) -> List[Relation]
```

#### 2.2 建立圖構建服務

**檔案**: `app/services/graph_builder.py` (新建)

- [ ] 建立 `GraphBuilder` 類別
- [ ] 整合 `EntityExtractor` 和 `GraphStore`
- [ ] 實作文件到圖的轉換流程
- [ ] 實作批次處理
- [ ] 實作增量更新

**方法簽名**：
```python
async def build_graph_from_text(self, text: str, document_id: str) -> Dict
async def build_graph_from_document(self, document: Dict) -> Dict
async def update_graph_from_text(self, text: str, document_id: str) -> Dict
```

### 階段三：圖查詢方法（中優先級）

#### 3.1 實作基本查詢方法

**檔案**: `app/core/graph_store.py`

- [ ] `get_entity(entity_id)` - 取得單一實體
- [ ] `get_entities_by_type(entity_type)` - 依類型查詢
- [ ] `search_entities(query, limit)` - 搜尋實體
- [ ] `get_relations(source_id, relation_type)` - 取得關係
- [ ] `get_incoming_relations(target_id, relation_type)` - 取得反向關係

#### 3.2 實作進階查詢方法

**檔案**: `app/core/graph_store.py`

- [ ] `get_neighbors(entity_id, relation_type, direction)` - 取得鄰居
- [ ] `get_path(source_id, target_id, max_hops)` - BFS 路徑查詢
- [ ] `get_subgraph(entity_ids, max_depth)` - 子圖查詢
- [ ] `get_common_neighbors(entity_id1, entity_id2)` - 共同鄰居

#### 3.3 查詢優化

- [ ] 實作查詢快取
- [ ] 限制查詢深度
- [ ] 實作查詢超時
- [ ] 優化索引使用

### 階段四：整合到現有系統（高優先級）

#### 4.1 更新 GraphOrchestrator

**檔案**: `app/core/orchestrator.py`

- [ ] 添加 `GraphStore` 依賴
- [ ] 添加 `EntityExtractor` 依賴
- [ ] 實作圖查詢整合邏輯：
  1. 從向量結果提取實體
  2. 執行圖查詢
  3. 融合結果
  4. 重排序
  5. LLM 生成

#### 4.2 更新文件管理端點

**檔案**: `app/api/v1/endpoints/documents.py`

- [ ] 整合 `GraphBuilder`
- [ ] 文件新增時自動構建圖
- [ ] 文件更新時更新圖
- [ ] 文件刪除時清理圖

#### 4.3 更新依賴注入

**檔案**: `app/api/v1/dependencies.py` (新建)

- [ ] 添加 `get_graph_store()` 依賴
- [ ] 添加 `get_entity_extractor()` 依賴
- [ ] 添加 `get_graph_builder()` 依賴
- [ ] 更新所有端點使用依賴注入

### 階段五：資料庫初始化（中優先級）

#### 5.1 更新 init_graph_db.py

**檔案**: `scripts/init_graph_db.py`

- [ ] 整合 `SQLiteGraphStore.initialize()`
- [ ] 添加範例資料載入（選用）
- [ ] 添加資料庫遷移檢查
- [ ] 添加錯誤處理

#### 5.2 建立圖構建腳本

**檔案**: `scripts/build_graph_from_docs.py` (新建)

- [ ] 從現有文件構建圖
- [ ] 支援批次處理
- [ ] 顯示進度
- [ ] 錯誤恢復

### 階段六：測試和文檔（中優先級）

#### 6.1 單元測試

**檔案**: `tests/test_core/test_graph_store.py` (新建)

- [ ] 測試實體 CRUD
- [ ] 測試關係 CRUD
- [ ] 測試圖查詢方法
- [ ] 測試級聯刪除
- [ ] 測試事務處理

#### 6.2 整合測試

**檔案**: `tests/test_integration/test_graphrag.py` (新建)

- [ ] 測試文件到圖構建
- [ ] 測試查詢整合流程
- [ ] 測試端點整合

#### 6.3 效能測試

- [ ] 大量資料查詢效能
- [ ] 並發寫入測試
- [ ] 記憶體使用測試

---

## 代碼審查發現

### 原始計劃的優點

1. ✅ **架構清晰**：分層明確，職責清楚
2. ✅ **抽象設計**：使用抽象基類，易於擴展
3. ✅ **雙重實作**：SQLite（生產）+ Memory（測試）
4. ✅ **查詢方法完整**：涵蓋基本圖查詢需求
5. ✅ **整合考慮**：與現有 Orchestrator 整合

### 關鍵問題與改進

#### 問題 1: 缺少實體提取機制 ⚠️ 高優先級

**發現**：
- 計劃中提到了 `_extract_entities()`，但沒有實作細節
- 沒有說明如何從文字中提取實體和關係

**影響**：
- 無法自動構建圖結構
- 需要手動輸入實體和關係

**解決方案**：
- 建立 `EntityExtractor` 類別
- 使用 LLM 進行 NER（Named Entity Recognition）
- 實作關係提取（Relation Extraction）

#### 問題 2: 缺少文件到圖的轉換流程 ⚠️ 高優先級

**發現**：
- 沒有說明如何將文件內容轉換為圖結構
- `documents.py` 端點沒有整合圖構建

**影響**：
- 文件新增後無法自動構建圖
- 需要額外的處理步驟

**解決方案**：
- 建立 `GraphBuilder` 服務
- 在文件新增時自動提取實體和關係
- 實作增量更新機制

#### 問題 3: 查詢整合邏輯不完整 ⚠️ 中優先級

**發現**：
- `orchestrator.py` 中的整合邏輯過於簡化
- 沒有說明如何融合向量和圖結果

**影響**：
- 圖查詢結果無法有效利用
- 查詢品質可能不佳

**解決方案**：
- 實作結果融合策略
- 實作重排序（Re-ranking）
- 考慮圖結構的權重

#### 問題 4: 缺少事務處理 ⚠️ 中優先級

**發現**：
- SQLite 操作沒有事務保護
- 批次操作可能不一致

**影響**：
- 資料可能不一致
- 並發寫入可能出錯

**解決方案**：
- 使用 `aiosqlite` 的事務功能
- 批次操作使用事務
- 處理並發寫入

#### 問題 5: 缺少圖查詢優化 ⚠️ 中優先級

**發現**：
- 多跳查詢可能效能較差
- 沒有查詢快取

**影響**：
- 查詢速度慢
- 資源消耗高

**解決方案**：
- 實作查詢深度限制
- 使用快取常見查詢路徑
- 考慮使用圖演算法庫

#### 問題 6: 缺少資料驗證 ⚠️ 低優先級

**發現**：
- Entity 和 Relation 沒有驗證邏輯
- 沒有檢查循環關係

**影響**：
- 可能產生無效資料
- 查詢可能出錯

**解決方案**：
- 使用 Pydantic 進行驗證
- 檢查循環關係
- 驗證實體類型

---

## 改進建議

### 新增檔案清單

```
app/core/
├── graph_store.py          # GraphStore 實作（計劃已有）
├── entity_extractor.py     # 實體提取器（新增）⭐
└── graph_builder.py        # 圖構建服務（新增）⭐

app/services/
└── graph_builder.py        # 或放在 services（新增）⭐

scripts/
├── init_graph_db.py        # 更新（計劃已有）
└── build_graph_from_docs.py # 從文件構建圖（新增）⭐

tests/test_core/
├── test_graph_store.py     # GraphStore 測試（新建）
└── test_entity_extractor.py # 實體提取器測試（新建）

tests/test_integration/
└── test_graphrag.py        # GraphRAG 整合測試（新建）
```

### 改進後的查詢流程

```
1. 用戶查詢
   ↓
2. 檢查快取
   ↓ (Miss)
3. 向量檢索 → 取得相關文件
   ↓
4. 實體提取 → 識別實體（從文件內容）
   ↓
5. 圖查詢 → 查詢相關實體和關係
   ├─→ 鄰居查詢（1-hop）
   ├─→ 路徑查詢（2-hop, 3-hop）
   └─→ 子圖查詢
   ↓
6. 結果融合 → 合併向量和圖結果
   ├─→ 去重
   ├─→ 權重計算
   └─→ 排序
   ↓
7. 重排序 → 根據相關性排序
   ↓
8. LLM 生成 → 使用增強後的上下文
   ├─→ 包含向量檢索結果
   ├─→ 包含圖結構資訊
   └─→ 包含實體關係
   ↓
9. 存入快取
   ↓
10. 返回結果
```

---

## 執行計劃

### 執行順序

1. **階段一**：核心基礎設施（GraphStore）
   - 1.1-1.4：資料模型、抽象介面、SQLite 實作、Memory 實作

2. **階段二**：實體和關係提取
   - 2.1：EntityExtractor
   - 2.2：GraphBuilder

3. **階段三**：圖查詢方法
   - 3.1-3.3：基本查詢、進階查詢、優化

4. **階段四**：整合到現有系統
   - 4.1：更新 Orchestrator
   - 4.2：更新文件管理端點
   - 4.3：更新依賴注入

5. **階段五**：資料庫初始化
   - 5.1：更新 init_graph_db.py
   - 5.2：建立圖構建腳本

6. **階段六**：測試和文檔
   - 6.1-6.3：單元測試、整合測試、效能測試

### 依賴更新

**檔案**: `requirements.txt`

添加：
```
aiosqlite>=0.19.0      # SQLite 非同步支援
networkx>=3.0          # 圖演算法（選用）
```

---

## 測試策略

### 單元測試

1. **GraphStore 測試**
   - 實體 CRUD 操作
   - 關係 CRUD 操作
   - 圖查詢方法
   - 級聯刪除
   - 事務處理

2. **EntityExtractor 測試**
   - 實體提取準確度
   - 關係提取準確度
   - 處理邊界情況

3. **GraphBuilder 測試**
   - 文件到圖轉換
   - 批次處理
   - 增量更新

### 整合測試

1. **GraphRAG 整合測試**
   - 完整查詢流程
   - 結果融合
   - 端點整合

2. **效能測試**
   - 大量資料查詢
   - 並發寫入
   - 記憶體使用

---

## 風險評估

| 風險 | 嚴重程度 | 可能性 | 緩解措施 |
|------|---------|--------|---------|
| 實體提取準確度低 | 高 | 中 | 使用多種提取方法，人工校驗 |
| 圖查詢效能差 | 中 | 中 | 實作查詢快取，限制查詢深度 |
| 資料不一致 | 中 | 低 | 使用事務，實作驗證 |
| 記憶體使用過高 | 低 | 低 | 使用 SQLite，限制記憶體模式 |
| LLM API 成本高 | 中 | 中 | 快取提取結果，批次處理 |

---

## 驗證檢查清單

### 功能驗證

- [ ] GraphStore 可以新增和查詢實體
- [ ] GraphStore 可以新增和查詢關係
- [ ] 可以執行多跳查詢（2-hop, 3-hop）
- [ ] 可以查詢實體間的路徑
- [ ] 刪除實體時自動刪除相關關係（級聯刪除）
- [ ] EntityExtractor 可以從文字提取實體
- [ ] EntityExtractor 可以從文字提取關係
- [ ] GraphBuilder 可以從文件構建圖
- [ ] `init_graph_db.py` 可以成功初始化資料庫
- [ ] Orchestrator 可以整合 GraphStore 進行查詢
- [ ] 文件新增時自動構建圖
- [ ] 查詢結果正確融合向量和圖結果

### 效能驗證

- [ ] 單一實體查詢 < 10ms
- [ ] 多跳查詢（3-hop）< 100ms
- [ ] 批次新增 1000 個實體 < 5s
- [ ] 記憶體使用 < 500MB（10000 實體）

### 測試驗證

- [ ] 所有單元測試通過
- [ ] 所有整合測試通過
- [ ] 測試覆蓋率 > 80%

---

## 總結

### 計劃評分

- **架構設計**: 8/10（缺少實體提取和圖構建）
- **資料模型**: 9/10（設計良好）
- **查詢方法**: 7/10（基本完整，缺少優化）
- **整合設計**: 6/10（整合邏輯需要完善）
- **測試計劃**: 7/10（基本覆蓋，可加強）

**總體評分**: 7.4/10

### 優先改進建議

1. ⭐⭐⭐ **立即實作**：實體提取器（EntityExtractor）
2. ⭐⭐⭐ **立即實作**：文件到圖的轉換流程（GraphBuilder）
3. ⭐⭐ **高優先級**：完善查詢整合邏輯
4. ⭐⭐ **高優先級**：加入事務處理
5. ⭐ **中優先級**：查詢效能優化

---

## 附錄

### 參考資料

- [GraphRAG Paper](https://arxiv.org/abs/2404.16130)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [aiosqlite Documentation](https://aiosqlite.omnilib.dev/)

### 相關檔案

- `app/core/orchestrator.py` - GraphRAG 編排器
- `app/services/rag_service.py` - RAG 服務
- `app/api/v1/endpoints/documents.py` - 文件管理端點
- `scripts/init_graph_db.py` - 資料庫初始化腳本

---

**文檔結束**


