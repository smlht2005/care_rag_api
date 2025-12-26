# 關係提取失敗根本原因分析

## 問題描述

從終端輸出可以看到：
- 每個區塊都顯示：`✅ 區塊 X 完成: 1 實體, 0 關係`
- 總關係數：0 個

## 根本原因分析

### 1. 代碼流程分析

#### 關係提取的依賴鏈

```
process_pdf_to_graph.py (第 163 行)
  └─> GraphBuilder.build_graph_from_text() (第 25 行)
      ├─> EntityExtractor.extract_entities() (第 46 行) ✅ 成功（但只有 1 個實體）
      └─> EntityExtractor.extract_relations() (第 66 行) ❌ 失敗（返回空列表）
```

#### 關鍵代碼位置

**`app/services/graph_builder.py` (第 65-66 行)**：
```python
# 4. 提取關係
relations = await self.entity_extractor.extract_relations(text, saved_entities)
```

**`app/core/entity_extractor.py` (第 60-75 行)**：
```python
async def extract_relations(
    self,
    text: str,
    entities: List[Entity]
) -> List[Relation]:
    if not entities:
        return []  # ⚠️ 如果沒有實體，直接返回空列表
    
    try:
        prompt = self._build_relation_extraction_prompt(text, entities)
        response = await self.llm_service.generate(prompt, max_tokens=1000)
        relations = self._parse_relation_response(response, entities)
        # ...
    except Exception as e:
        self.logger.error(f"Failed to extract relations (LLM-based): {str(e)}")
        return []  # ⚠️ 異常時返回空列表（沒有降級方案）
```

### 2. 問題分類

#### 問題 1: 實體數量不足（數據問題）

**原因**：
- LLM 服務是 Stub，返回的不是 JSON 格式
- JSON 解析失敗，降級到規則基礎提取
- 規則基礎提取只提取了 1 個實體/區塊

**證據**：
```python
# app/core/entity_extractor.py (第 300-328 行)
def _rule_based_entity_extraction(self, text: str) -> List[Entity]:
    """規則基礎實體提取（降級方案）"""
    entities = []
    # 只提取大寫開頭的英文詞（簡單規則）
    pattern = r'\b[A-Z][a-z]+\b'  # ⚠️ 只匹配英文，不匹配中文
    matches = re.findall(pattern, text)
    
    for match in set(matches):
        if len(match) > 2:
            entity = Entity(...)
            entities.append(entity)
    return entities  # ⚠️ 如果 PDF 是中文，可能匹配不到或很少
```

**實際問題**：
- PDF 內容是中文（"長期照護2.0核定本"）
- 規則基礎提取只匹配大寫開頭的**英文**單詞
- 中文內容無法匹配，所以每個區塊可能只提取到 1 個實體（或更少）

**影響**：
- 關係提取需要至少 2 個實體才能建立關係
- 如果只有 1 個實體，即使 LLM 返回了關係，也無法匹配（因為需要 source 和 target）

#### 問題 2: 關係提取沒有降級方案（代碼問題）

**原因**：
- 實體提取有降級方案（規則基礎提取）
- 關係提取沒有降級方案，失敗時直接返回空列表

**證據**：
```python
# app/core/entity_extractor.py (第 60-75 行)
async def extract_relations(...):
    if not entities:
        return []  # ⚠️ 沒有實體時，直接返回空列表
    
    try:
        # LLM 提取關係
        ...
    except Exception as e:
        self.logger.error(...)
        return []  # ⚠️ 異常時返回空列表（沒有降級方案）
```

**對比實體提取**：
```python
# app/core/entity_extractor.py (第 40-58 行)
async def extract_entities(...):
    try:
        # LLM 提取實體
        ...
    except Exception as e:
        self.logger.error(...)
        return self._rule_based_entity_extraction(text)  # ✅ 有降級方案
```

#### 問題 3: LLM 服務是 Stub（架構問題）

**原因**：
- LLM 服務返回的是固定文字，不是 JSON 格式
- JSON 解析失敗，導致實體和關係提取都失敗

**證據**：
```python
# app/services/llm_service.py (第 20-30 行)
async def generate(self, prompt: str, ...) -> str:
    await asyncio.sleep(0.1)
    if self.provider == "gemini":
        return f"[Gemini] 回答: {prompt}\n\n這是一個基於 Gemini 模型的回答..."
    # ⚠️ 返回的是文字，不是 JSON
```

**影響**：
- 實體提取：JSON 解析失敗 → 降級到規則基礎提取 → 只提取 1 個實體
- 關係提取：JSON 解析失敗 → 沒有降級方案 → 返回空列表

### 3. 根本原因總結

| 問題類型 | 具體問題 | 影響 | 嚴重程度 |
|---------|---------|------|---------|
| **數據問題** | 實體數量不足（只有 1 個/區塊） | 無法建立關係（需要至少 2 個實體） | 🔴 高 |
| **代碼問題** | 關係提取沒有降級方案 | 失敗時直接返回空列表 | 🟡 中 |
| **架構問題** | LLM 服務是 Stub | 無法返回真正的 JSON 格式 | 🔴 高 |

### 4. 為什麼關係提取依賴實體提取？

#### 技術原因

1. **關係需要實體 ID**：
   ```python
   # app/core/entity_extractor.py (第 263-276 行)
   source_entity = entity_map.get(source_name)  # 需要從實體列表中查找
   target_entity = entity_map.get(target_name)  # 需要從實體列表中查找
   
   if source_entity and target_entity:
       relation = Relation(
           source_id=source_entity.id,  # ⚠️ 需要實體的 ID
           target_id=target_entity.id,   # ⚠️ 需要實體的 ID
           ...
       )
   ```

2. **實體名稱匹配**：
   - LLM 返回的關係包含實體名稱（如 "張三"、"醫院"）
   - 需要從已提取的實體列表中匹配，獲取實體的 ID
   - 如果實體提取失敗，無法匹配，關係就無法建立

3. **邏輯順序**：
   - 先提取實體（知道有哪些實體）
   - 再提取關係（知道實體間的關係）
   - 這是標準的知識圖譜構建流程

#### 設計原因

1. **避免孤立關係**：
   - 如果先提取關係，可能提取到不存在的實體
   - 先提取實體，確保關係只連接已存在的實體

2. **提高準確度**：
   - 實體提取可以驗證實體的存在性
   - 關係提取可以基於已驗證的實體

## 解決方案

### 方案 1: 實作真正的 LLM 整合（推薦）

**優點**：
- 解決根本問題
- 可以提取多個實體和關係
- 準確度高

**缺點**：
- 需要 API Key
- 需要網路連線
- 可能產生費用

**實作步驟**：
1. 在 `LLMService` 中實作真正的 API 呼叫
2. 確保返回 JSON 格式
3. 處理 API 錯誤和重試

### 方案 2: 改進規則基礎提取

**優點**：
- 不需要 API
- 可以提取更多實體（包括中文）

**缺點**：
- 準確度較低
- 無法提取關係（關係需要語義理解）

**實作步驟**：
1. 改進 `_rule_based_entity_extraction()` 支援中文實體提取
   ```python
   # 添加中文實體提取規則
   # 例如：提取專有名詞、日期、數字等
   ```
2. 添加規則基礎關係提取（基於關鍵詞匹配）
   ```python
   # 例如：提取 "A 在 B"、"A 屬於 B" 等模式
   ```

### 方案 3: 添加關係提取降級方案

**優點**：
- 即使 LLM 失敗，也能提取一些關係
- 提高系統穩定性

**缺點**：
- 準確度較低
- 只能提取簡單關係

**實作步驟**：
```python
async def extract_relations(...):
    try:
        # LLM 提取關係
        ...
    except Exception as e:
        self.logger.error(...)
        # ✅ 添加降級方案
        return self._rule_based_relation_extraction(text, entities)

def _rule_based_relation_extraction(self, text: str, entities: List[Entity]) -> List[Relation]:
    """規則基礎關係提取（降級方案）"""
    relations = []
    # 基於關鍵詞匹配提取關係
    # 例如：提取 "A 在 B"、"A 屬於 B" 等模式
    ...
    return relations
```

### 方案 4: 改進分塊策略

**優點**：
- 每個區塊包含更多上下文
- 可能提取更多實體

**缺點**：
- 不解決根本問題
- 只是改善數據質量

**實作步驟**：
1. 使用語義分塊（而不是固定長度）
2. 確保每個區塊包含完整句子
3. 避免在實體中間分塊

## 結論

### 根本原因

**主要問題**：LLM 服務是 Stub，無法返回真正的 JSON 格式
- 導致實體提取失敗（降級到規則基礎提取，只提取 1 個實體）
- 導致關係提取失敗（沒有降級方案，返回空列表）

**次要問題**：
- 關係提取沒有降級方案
- 規則基礎實體提取只提取 1 個實體

### 優先級建議

1. **高優先級**：實作真正的 LLM 整合
2. **中優先級**：添加關係提取降級方案
3. **低優先級**：改進規則基礎提取

### 當前狀態

- ✅ 代碼邏輯正確（關係提取依賴實體提取是正確的設計）
- ❌ 數據問題（實體數量不足）
- ❌ 架構問題（LLM 服務是 Stub）
- ⚠️ 代碼問題（關係提取沒有降級方案）

## 相關文檔

- `docs/qa/stub_qa.md` - Stub 相關問答
- `docs/qa/json_parse_error_qa.md` - JSON 解析錯誤問答
- `docs/pdf_to_entity_result.md` - PDF 處理結果分析

