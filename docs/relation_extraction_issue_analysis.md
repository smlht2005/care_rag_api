# 關係提取問題分析與解決方案

## 更新時間
2025-12-26 12:45

## 作者
AI Assistant

## 問題描述

從終端輸出可以看到：
- ✅ 每個區塊都成功提取了 **1 個實體**
- ❌ 每個區塊都顯示 **0 個關係**
- 總結果：65 個實體，0 個關係

## 根本原因

### 原因 1: LLM 服務是 Stub（主要問題）

**位置**: `app/services/llm_service.py:52-54`

**問題**:
```python
# GeminiLLM.generate() 返回的是模擬文字，不是 JSON
return f"[Gemini] 回答: {prompt}\n\n這是一個基於 Gemini 模型的回答..."
```

**影響**:
- 關係提取需要 LLM 返回 JSON 格式的關係數據
- Stub 返回的是普通文字，無法解析為 JSON
- `_parse_relation_response()` 解析失敗，返回空列表

### 原因 2: 關係提取沒有降級方案

**位置**: `app/core/entity_extractor.py:60-93`

**問題**:
```python
async def extract_relations(...):
    try:
        # LLM 提取關係
        response = await self.llm_service.generate(prompt, max_tokens=1000)
        relations = self._parse_relation_response(response, entities)
        return relations
    except Exception as e:
        self.logger.error(f"Failed to extract relations: {str(e)}")
        return []  # ❌ 直接返回空列表，沒有降級方案
```

**對比實體提取**:
```python
async def extract_entities(...):
    try:
        # LLM 提取實體
        ...
    except Exception as e:
        # ✅ 有降級方案
        return self._rule_based_entity_extraction(text)
```

### 原因 3: JSON 解析失敗

**位置**: `app/core/entity_extractor.py:215-283`

**問題**:
- LLM 返回的文字不是 JSON 格式
- `json.loads()` 解析失敗
- 捕獲異常但只記錄日誌，不返回任何關係

## 解決方案

### 方案 1: 實作真正的 Gemini API（推薦 ⭐⭐⭐⭐⭐）

**優點**:
- ✅ 解決根本問題
- ✅ 可以提取多個實體和關係
- ✅ 準確度高
- ✅ 支援中文

**缺點**:
- ⚠️ 需要 Gemini API Key
- ⚠️ 需要網路連線
- ⚠️ 可能產生費用

**實作步驟**:

1. **獲取 Gemini API Key**:
   - 訪問 https://makersuite.google.com/app/apikey
   - 創建 API Key
   - 將 Key 添加到 `.env` 文件

2. **安裝依賴**:
   ```bash
   pip install google-generativeai
   ```

3. **實作真正的 Gemini API**:
   ```python
   # app/services/llm_service.py
   import google.generativeai as genai
   
   class GeminiLLM(BaseLLM):
       def __init__(self, api_key: Optional[str] = None):
           self.api_key = api_key or settings.GEMINI_API_KEY
           if not self.api_key:
               raise ValueError("GEMINI_API_KEY is required")
           
           genai.configure(api_key=self.api_key)
           self.model = genai.GenerativeModel('gemini-pro')
       
       async def generate(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> str:
           response = self.model.generate_content(
               prompt,
               generation_config={
                   "max_output_tokens": max_tokens,
                   "temperature": temperature
               }
           )
           return response.text
   ```

4. **配置環境變數**:
   ```bash
   # .env
   GEMINI_API_KEY=your_api_key_here
   LLM_PROVIDER=gemini
   ```

---

### 方案 2: 添加規則基礎關係提取（快速修復 ⭐⭐⭐⭐）

**優點**:
- ✅ 不需要 API Key
- ✅ 可以立即使用
- ✅ 提高系統穩定性

**缺點**:
- ⚠️ 準確度較低
- ⚠️ 只能提取簡單關係

**實作步驟**:

1. **添加規則基礎關係提取方法**:
   ```python
   # app/core/entity_extractor.py
   
   def _rule_based_relation_extraction(
       self, 
       text: str, 
       entities: List[Entity]
   ) -> List[Relation]:
       """規則基礎的關係提取（降級方案）"""
       relations = []
       
       if len(entities) < 2:
           return relations
       
       # 建立實體名稱映射
       entity_map = {e.name: e for e in entities}
       
       # 關係模式匹配
       patterns = [
           # A 在 B
           (r'([^，。\n]+)在([^，。\n]+)', 'LOCATED_IN'),
           # A 屬於 B
           (r'([^，。\n]+)屬於([^，。\n]+)', 'BELONGS_TO'),
           # A 是 B
           (r'([^，。\n]+)是([^，。\n]+)', 'IS_A'),
           # A 包含 B
           (r'([^，。\n]+)包含([^，。\n]+)', 'CONTAINS'),
           # A 與 B 相關
           (r'([^，。\n]+)與([^，。\n]+)相關', 'RELATED_TO'),
       ]
       
       for pattern, relation_type in patterns:
           matches = re.finditer(pattern, text)
           for match in matches:
               source_name = match.group(1).strip()
               target_name = match.group(2).strip()
               
               source_entity = entity_map.get(source_name)
               target_entity = entity_map.get(target_name)
               
               if source_entity and target_entity and source_entity.id != target_entity.id:
                   relation = Relation(
                       id=str(uuid.uuid4()),
                       source_id=source_entity.id,
                       target_id=target_entity.id,
                       type=relation_type,
                       properties={"extracted_by": "rule_based"},
                       weight=0.5,  # 規則基礎的權重較低
                       created_at=datetime.now()
                   )
                   relations.append(relation)
       
       return relations
   ```

2. **修改 extract_relations 方法**:
   ```python
   async def extract_relations(
       self,
       text: str,
       entities: List[Entity]
   ) -> List[Relation]:
       if not entities:
           return []
       
       try:
           # LLM 提取關係
           prompt = self._build_relation_extraction_prompt(text, entities)
           response = await self.llm_service.generate(prompt, max_tokens=1000)
           relations = self._parse_relation_response(response, entities)
           
           if relations:  # 如果 LLM 提取成功
               self.logger.info(f"Extracted {len(relations)} relations from text (LLM-based)")
               return relations
           else:
               # LLM 提取失敗，降級到規則基礎提取
               self.logger.warning("LLM relation extraction returned empty, falling back to rule-based")
               return self._rule_based_relation_extraction(text, entities)
               
       except Exception as e:
           self.logger.error(f"Failed to extract relations (LLM-based): {str(e)}")
           # 降級到規則基礎提取
           return self._rule_based_relation_extraction(text, entities)
   ```

---

### 方案 3: 改進 Stub 返回格式（臨時方案 ⭐⭐⭐）

**優點**:
- ✅ 不需要 API Key
- ✅ 可以測試關係提取邏輯
- ✅ 快速實作

**缺點**:
- ⚠️ 返回的是模擬數據，不真實
- ⚠️ 無法用於生產環境

**實作步驟**:

修改 `GeminiLLM.generate()` 方法，檢測是否為實體/關係提取提示詞，返回模擬 JSON：

```python
async def generate(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> str:
    # 檢測是否為實體提取提示詞
    if "提取所有實體" in prompt or "extract entities" in prompt.lower():
        # 返回模擬實體 JSON
        return '''[
  {"name": "長期照護", "type": "Concept", "properties": {}},
  {"name": "核定本", "type": "Document", "properties": {}}
]'''
    
    # 檢測是否為關係提取提示詞
    if "提取關係" in prompt or "extract relations" in prompt.lower():
        # 返回模擬關係 JSON
        return '''[
  {"source": "長期照護", "target": "核定本", "type": "CONTAINS", "properties": {}}
]'''
    
    # 其他情況返回模擬文字
    return f"[Gemini] 回答: {prompt}"
```

---

## 推薦方案

### 短期（立即修復）
**方案 2**: 添加規則基礎關係提取降級方案
- 可以立即使用
- 不需要 API Key
- 提高系統穩定性

### 長期（生產環境）
**方案 1**: 實作真正的 Gemini API
- 準確度高
- 支援複雜關係提取
- 適合生產環境

---

## 驗證步驟

### 測試規則基礎關係提取

1. **實作方案 2**
2. **重新處理 PDF**:
   ```bash
   python scripts/process_pdf_to_graph.py data/example/1051219長期照護2.0核定本.pdf
   ```
3. **檢查結果**:
   - 應該能看到關係數量 > 0
   - 檢查資料庫中的關係

### 測試 Gemini API

1. **配置 API Key**:
   ```bash
   # .env
   GEMINI_API_KEY=your_key_here
   ```
2. **實作方案 1**
3. **重新處理 PDF**
4. **檢查結果**:
   - 應該能看到更多實體和關係
   - 關係類型更豐富

---

## 相關文檔

- `docs/qa/relation_extraction_root_cause.md` - 關係提取根本原因分析
- `docs/json_parse_error_fix.md` - JSON 解析錯誤修復
- `app/core/entity_extractor.py` - 實體提取器實作

---

## 總結

**問題**: LLM 服務是 Stub，返回的不是 JSON 格式，導致關係提取失敗。

**解決方案**:
1. ✅ **立即**: 添加規則基礎關係提取降級方案
2. ✅ **長期**: 實作真正的 Gemini API

**是否需要 Gemini API Key**: 
- 如果使用方案 1（推薦），**需要** API Key
- 如果使用方案 2（快速修復），**不需要** API Key


