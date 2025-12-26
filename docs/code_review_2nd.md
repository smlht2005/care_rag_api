# 第二次代碼審查報告

## 更新時間
2025-12-26 12:25

## 作者
AI Assistant (GraphRAG & FastAPI Expert)

## 審查範圍

從 GraphRAG 架構設計和 FastAPI 最佳實踐角度，對重構後的代碼進行深度審查。

---

## 🔴 嚴重問題（必須修復）

### 問題 1: 圖查詢邏輯錯誤 - 實體 ID 提取不正確

**位置**: `app/core/orchestrator.py:120-125`

**問題描述**:
```python
# 從向量結果中提取實體 ID
entity_ids = []
for source in vector_sources:
    doc_id = source.get("id", "")
    if doc_id:
        entity_ids.append(doc_id)
```

**根本問題**:
- 向量檢索返回的是**文檔 ID**，不是**實體 ID**
- GraphStore 中存儲的是從文檔提取的**實體**，不是文檔本身
- 這導致圖查詢無法找到相關實體，圖增強功能失效

**正確做法**:
1. 從向量結果中提取文檔 ID
2. 查詢 GraphStore 中與該文檔相關的實體（通過 `CONTAINS` 關係）
3. 或使用實體名稱/類型進行語義搜索

**修復建議**:
```python
# 從向量結果中提取文檔 ID
doc_ids = [s.get("id", "") for s in vector_sources if s.get("id")]

# 查詢與文檔相關的實體
entity_ids = []
for doc_id in doc_ids:
    # 方法1: 通過關係查詢（推薦）
    doc_entity = await self.graph_store.get_entity(doc_id)
    if doc_entity:
        # 查詢該文檔包含的所有實體
        relations = await self.graph_store.get_neighbors(
            doc_id, 
            relation_type="CONTAINS",
            direction="outgoing"
        )
        entity_ids.extend([e.id for e in relations])
    
    # 方法2: 使用實體搜索（備選）
    # 從向量結果的 content 中提取關鍵詞，搜索實體
```

---

### 問題 2: 缺少實體語義匹配邏輯

**位置**: `app/core/orchestrator.py:_enhance_with_graph()`

**問題描述**:
- 圖增強只依賴文檔 ID，沒有使用查詢文本進行實體匹配
- 無法找到與查詢語義相關的實體

**修復建議**:
```python
async def _enhance_with_graph(
    self,
    query_text: str,  # 使用查詢文本
    vector_sources: List[Dict[str, Any]]
) -> GraphEnhancementResult:
    # 1. 從向量結果提取文檔 ID
    doc_ids = [s.get("id") for s in vector_sources if s.get("id")]
    
    # 2. 使用查詢文本搜索相關實體（新增）
    query_entities = await self.graph_store.search_entities(query_text, limit=10)
    
    # 3. 從文檔相關實體中查找
    doc_entities = []
    for doc_id in doc_ids:
        neighbors = await self.graph_store.get_neighbors(
            doc_id,
            relation_type="CONTAINS",
            direction="outgoing"
        )
        doc_entities.extend(neighbors)
    
    # 4. 合併並去重
    all_entities = list(set(query_entities + doc_entities))
```

---

### 問題 3: 關係提取結果未使用

**位置**: `app/core/orchestrator.py:_enhance_with_graph()`

**問題描述**:
- `graph_relations` 始終為空列表
- 圖增強只返回實體，沒有返回關係
- 缺少關係查詢邏輯

**修復建議**:
```python
# 查詢實體之間的關係
for entity in graph_entities:
    # 獲取該實體的所有關係
    entity_relations = await self._get_entity_relations(entity.id)
    graph_relations.extend(entity_relations)

async def _get_entity_relations(self, entity_id: str) -> List[Relation]:
    """獲取實體的所有關係"""
    # 需要新增 GraphStore 方法：get_relations_by_entity
    # 或通過 get_neighbors 獲取關係信息
    pass
```

---

### 問題 4: 圖查詢缺少並行處理

**位置**: `app/core/orchestrator.py:138-163`

**問題描述**:
- 使用順序 `for` 循環查詢實體和鄰居
- 每個查詢都是獨立的，可以並行執行
- 性能瓶頸，特別是當實體數量多時

**修復建議**:
```python
import asyncio

# 並行查詢實體
entity_tasks = [
    self.graph_store.get_entity(entity_id) 
    for entity_id in entity_ids[:max_entities]
]
entities = await asyncio.gather(*entity_tasks, return_exceptions=True)
graph_entities = [e for e in entities if isinstance(e, Entity)]

# 並行查詢鄰居
neighbor_tasks = [
    self.graph_store.get_neighbors(entity_id, direction="both")
    for entity_id in entity_ids[:max_entities]
]
neighbors_list = await asyncio.gather(*neighbor_tasks, return_exceptions=True)
```

---

### 問題 5: 硬編碼的圖結果權重

**位置**: `app/core/orchestrator.py:157`

**問題描述**:
```python
"score": 0.7,  # 圖結果的權重較低
```

**問題**:
- 權重應該根據實體與查詢的相關性動態計算
- 硬編碼權重無法反映實際相關性

**修復建議**:
```python
# 計算實體與查詢的相關性分數
def _calculate_entity_score(
    self, 
    entity: Entity, 
    query_text: str
) -> float:
    """計算實體與查詢的相關性分數"""
    # 方法1: 基於名稱匹配
    query_lower = query_text.lower()
    entity_name_lower = entity.name.lower()
    
    if query_lower in entity_name_lower:
        return 0.9
    elif any(word in entity_name_lower for word in query_lower.split()):
        return 0.7
    else:
        return 0.5
    
    # 方法2: 使用向量相似度（需要實體嵌入）
    # 方法3: 基於關係路徑長度
```

---

## 🟡 中等问题（建議修復）

### 問題 6: GraphStore 缺少關係查詢方法

**位置**: `app/core/graph_store.py`

**問題描述**:
- 缺少 `get_relations_by_entity()` 方法
- 缺少 `get_relations_by_type()` 方法
- 無法高效查詢關係

**修復建議**:
```python
@abstractmethod
async def get_relations_by_entity(
    self,
    entity_id: str,
    direction: str = "both"
) -> List[Relation]:
    """獲取實體的所有關係"""
    pass

@abstractmethod
async def get_relations_by_type(
    self,
    relation_type: str,
    limit: int = 100
) -> List[Relation]:
    """按類型查詢關係"""
    pass
```

---

### 問題 7: RAGService 快取鍵未使用安全生成

**位置**: `app/services/rag_service.py:29`

**問題描述**:
```python
cache_key = f"rag_query:{query}"
```

**問題**:
- 使用簡單字串拼接，可能衝突
- 未使用 `generate_cache_key()` 工具函數

**修復建議**:
```python
from app.utils.cache_utils import generate_cache_key

cache_key = generate_cache_key("rag_query", query)
```

---

### 問題 8: 缺少查詢結果排序邏輯

**位置**: `app/core/orchestrator.py:73-85`

**問題描述**:
- 向量結果和圖結果簡單合併，沒有排序
- 應該根據相關性分數排序

**修復建議**:
```python
# 合併並排序
all_sources = result.get("sources", []) + graph_enhanced_sources
all_sources.sort(key=lambda x: x.get("score", 0.0), reverse=True)
result["sources"] = all_sources[:top_k]  # 只返回 top_k
```

---

### 問題 9: 缺少圖查詢的錯誤恢復機制

**位置**: `app/core/orchestrator.py:64-71`

**問題描述**:
- 如果圖查詢失敗，整個查詢失敗
- 應該降級到純向量檢索

**修復建議**:
```python
try:
    if self.graph_store:
        graph_results = await self._enhance_with_graph(...)
except Exception as e:
    self.logger.warning(f"Graph enhancement failed, falling back to vector search: {str(e)}")
    graph_results = GraphEnhancementResult(sources=[], entities=[], relations=[])
```

---

### 問題 10: FastAPI 端點缺少請求驗證

**位置**: `app/api/v1/endpoints/query.py:49-53`

**問題描述**:
```python
@router.get("/query/stream")
async def query_stream(
    query: str,  # 缺少驗證
    ...
):
```

**問題**:
- 查詢參數沒有長度限制
- 沒有輸入驗證

**修復建議**:
```python
from pydantic import Field
from fastapi import Query

@router.get("/query/stream")
async def query_stream(
    query: str = Query(..., min_length=1, max_length=1000),
    ...
):
```

---

## 🟢 改進建議（可選）

### 建議 1: 添加圖查詢的 Prometheus 指標

**位置**: `app/core/orchestrator.py`

**建議**:
```python
from app.utils.metrics import (
    GRAPH_QUERY_COUNTER,
    GRAPH_QUERY_LATENCY,
    GRAPH_ENTITIES_COUNT,
    GRAPH_RELATIONS_COUNT
)

# 在 _enhance_with_graph 中添加指標
GRAPH_QUERY_COUNTER.inc()
with GRAPH_QUERY_LATENCY.time():
    # 圖查詢邏輯
    pass
GRAPH_ENTITIES_COUNT.observe(len(graph_entities))
GRAPH_RELATIONS_COUNT.observe(len(graph_relations))
```

---

### 建議 2: 添加圖查詢結果的快取

**位置**: `app/core/orchestrator.py:_enhance_with_graph()`

**建議**:
- 圖增強結果可以單獨快取
- 使用實體 ID 列表作為快取鍵

---

### 建議 3: 添加圖查詢的批次處理

**位置**: `app/core/orchestrator.py`

**建議**:
- 當有多個查詢時，可以批次查詢圖結構
- 減少資料庫查詢次數

---

### 建議 4: 改進實體搜索算法

**位置**: `app/core/graph_store.py:search_entities()`

**建議**:
- 當前使用簡單的字串匹配
- 可以改進為：
  - 模糊匹配（fuzzy matching）
  - 同義詞匹配
  - 向量相似度搜索（如果實體有嵌入）

---

### 建議 5: 添加圖查詢的配置選項

**位置**: `app/config.py`

**建議**:
```python
# 圖查詢配置
GRAPH_ENHANCEMENT_ENABLED: bool = True
GRAPH_ENTITY_SEARCH_LIMIT: int = 10
GRAPH_RELATION_SEARCH_LIMIT: int = 20
GRAPH_SCORE_THRESHOLD: float = 0.5  # 最低相關性分數
```

---

## 📊 問題統計

| 嚴重程度 | 數量 | 狀態 |
|---------|------|------|
| 🔴 嚴重問題 | 5 | 必須修復 |
| 🟡 中等问题 | 5 | 建議修復 |
| 🟢 改進建議 | 5 | 可選 |

---

## 🎯 優先級修復計劃

### Phase 1: 核心功能修復（高優先級）
1. ✅ 問題 1: 修復實體 ID 提取邏輯
2. ✅ 問題 2: 添加實體語義匹配
3. ✅ 問題 3: 修復關係提取使用

### Phase 2: 性能優化（中優先級）
4. ✅ 問題 4: 添加並行處理
5. ✅ 問題 5: 動態權重計算
6. ✅ 問題 8: 結果排序

### Phase 3: 架構完善（低優先級）
7. ✅ 問題 6: GraphStore 關係查詢方法
8. ✅ 問題 7: RAGService 快取鍵修復
9. ✅ 問題 9: 錯誤恢復機制
10. ✅ 問題 10: API 驗證

---

## 🔍 GraphRAG 架構評估

### 優點 ✅
1. **清晰的抽象層**: GraphStore 抽象介面設計良好
2. **模組化設計**: Orchestrator、GraphBuilder、EntityExtractor 分離清晰
3. **錯誤處理**: 有基本的錯誤處理和降級機制
4. **類型提示**: 使用 TypedDict 定義返回類型

### 缺點 ❌
1. **圖查詢邏輯不完整**: 實體 ID 提取錯誤
2. **缺少語義匹配**: 無法根據查詢文本找到相關實體
3. **關係未充分利用**: 關係提取結果未使用
4. **性能瓶頸**: 順序查詢，缺少並行處理
5. **權重計算簡單**: 硬編碼權重，無法反映真實相關性

---

## 🚀 FastAPI 最佳實踐評估

### 優點 ✅
1. **依賴注入**: 正確使用 FastAPI 的 Depends
2. **Schema 驗證**: 使用 Pydantic 進行數據驗證
3. **錯誤處理**: 基本的錯誤處理機制
4. **指標監控**: 集成 Prometheus 指標

### 缺點 ❌
1. **缺少請求驗證**: 某些端點缺少參數驗證
2. **錯誤響應不一致**: 不同端點錯誤格式不統一
3. **缺少速率限制**: 沒有 API 速率限制
4. **缺少請求 ID**: 沒有追蹤請求的唯一 ID

---

## 📝 總結

第二次代碼審查發現了 **10 個問題**（5 個嚴重，5 個中等）和 **5 個改進建議**。

**關鍵發現**:
1. 圖查詢邏輯存在根本性錯誤，導致圖增強功能無法正常工作
2. 缺少實體語義匹配，無法充分利用圖結構
3. 性能優化空間大，特別是並行處理

**建議**:
- 優先修復問題 1-3（核心功能）
- 然後優化問題 4-5（性能）
- 最後完善問題 6-10（架構）

---

## 🔗 相關文檔

- `docs/code_review_1st.md` - 第一次代碼審查
- `docs/refactor_summary.md` - 重構總結
- `docs/integration_summary.md` - 整合總結


