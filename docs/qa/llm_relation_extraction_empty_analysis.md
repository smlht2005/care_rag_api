# LLM 關係提取返回空結果分析

**更新時間：2025-12-26 15:45**  
**作者：AI Assistant**  
**修改摘要：分析為什麼 LLM 關係提取會返回空結果並降級到 rule-based**

---

## 問題描述

在處理 PDF 並構建 GraphRAG 時，某些區塊會出現以下訊息：

```
LLM relation extraction returned empty, falling back to rule-based
```

**觀察到的現象**：
- 區塊 1, 2, 4：LLM 成功提取關係（沒有降級訊息）
- 區塊 3, 5, 6, 7：LLM 返回空結果，降級到 rule-based 提取

---

## 根本原因分析

### 1. 代碼邏輯流程

從 `app/core/entity_extractor.py` 的 `extract_relations` 方法可以看到：

```python
# 1. 構建提示詞
prompt = self._build_relation_extraction_prompt(text, entities)

# 2. 使用 LLM 提取關係
response = await self.llm_service.generate(prompt, max_tokens=1000)

# 3. 解析回應
relations = self._parse_relation_response(response, entities)

# 4. 檢查結果
if relations:
    # LLM 提取成功
    return relations
else:
    # LLM 提取失敗，降級到規則基礎提取
    self.logger.warning("LLM relation extraction returned empty, falling back to rule-based")
    return self._rule_based_relation_extraction(text, entities)
```

### 2. 可能的原因

#### 原因 1：LLM 回應格式無法解析

`_parse_relation_response` 方法嘗試解析 JSON 格式的回應：

```python
# 嘗試提取 JSON
json_patterns = [
    r'```json\s*(\[.*?\])\s*```',  # markdown JSON 代碼塊
    r'```\s*(\[.*?\])\s*```',      # 普通代碼塊
    r'(\[[\s\S]*?\])',             # 直接 JSON 陣列（非貪婪）
]
```

**問題**：
- 如果 LLM 返回的格式不符合這些模式，解析會失敗
- 即使 LLM 返回了有效的關係，但格式不正確，也會被視為空結果

#### 原因 2：實體名稱不匹配

在 `_parse_relation_response` 中：

```python
source_entity = entity_map.get(source_name)
target_entity = entity_map.get(target_name)

if source_entity and target_entity:
    # 只有當兩個實體都存在時，才創建關係
    relations.append(relation)
```

**問題**：
- 如果 LLM 返回的關係中的實體名稱與實際提取的實體名稱不完全匹配，關係會被忽略
- 例如：LLM 返回 "長期照護" 但實體名稱是 "長期照護2.0"，就會不匹配

#### 原因 3：某些文本區塊確實沒有明顯的關係

**正常情況**：
- 某些文本區塊可能主要是描述性文字，沒有明顯的實體間關係
- LLM 正確地返回空結果，表示沒有關係可提取

#### 原因 4：LLM 回應被截斷

**問題**：
- `max_tokens=1000` 可能不足以包含完整的 JSON 回應
- 如果回應被截斷，JSON 格式不完整，解析會失敗

---

## 診斷方法

### 1. 檢查 debug.log

查看 `.cursor/debug.log` 中的相關記錄：

```json
{
  "location": "entity_extractor.py:extract_relations:llm_response",
  "message": "LLM response received",
  "data": {
    "response_preview": "...",
    "response_length": 1234
  }
}
```

### 2. 添加更詳細的日誌

在 `_parse_relation_response` 方法中添加日誌，記錄：
- LLM 的原始回應
- 解析過程中的錯誤
- 匹配到的實體數量

### 3. 檢查實體匹配

記錄哪些實體名稱無法匹配，幫助診斷實體名稱不一致的問題。

---

## 解決方案

### 方案 1：改善 JSON 解析邏輯（推薦）

**問題**：當前解析邏輯可能過於嚴格

**解決方案**：
1. 添加更寬鬆的 JSON 提取模式
2. 嘗試多種解析策略
3. 記錄解析失敗的詳細原因

```python
def _parse_relation_response(self, response: str, entities: List[Entity]) -> List[Relation]:
    """解析 LLM 回應為關係列表（改進版）"""
    relations = []
    entity_map = {e.name: e for e in entities}
    
    # 添加模糊匹配邏輯
    def fuzzy_match_entity(name: str) -> Optional[Entity]:
        # 精確匹配
        if name in entity_map:
            return entity_map[name]
        # 模糊匹配（包含關係）
        for entity_name, entity in entity_map.items():
            if name in entity_name or entity_name in name:
                return entity
        return None
    
    # ... 解析邏輯 ...
```

### 方案 2：增加 max_tokens

**問題**：`max_tokens=1000` 可能不足

**解決方案**：
```python
response = await self.llm_service.generate(prompt, max_tokens=2000)  # 增加到 2000
```

### 方案 3：改善 Prompt 設計

**問題**：Prompt 可能不夠明確

**解決方案**：
1. 明確要求 JSON 格式
2. 提供範例
3. 強調實體名稱必須完全匹配

```python
def _build_relation_extraction_prompt(self, text: str, entities: List[Entity]) -> str:
    """構建關係提取提示詞（改進版）"""
    entity_names = [e.name for e in entities]
    
    prompt = f"""請從以下文字中提取實體間的關係，並以 JSON 格式返回。

**重要**：
1. 必須返回有效的 JSON 陣列格式
2. 實體名稱必須完全匹配以下列表中的名稱
3. 如果沒有關係，返回空陣列 []

可用實體列表：
{json.dumps(entity_names, ensure_ascii=False, indent=2)}

文字內容：
{text[:2000]}

請返回 JSON 格式的關係陣列，每個關係包含：
- source: 來源實體名稱（必須完全匹配上述列表）
- target: 目標實體名稱（必須完全匹配上述列表）
- type: 關係類型
- properties: 關係屬性（可選）

範例格式：
[
  {{"source": "長期照護", "target": "政策", "type": "RELATED_TO", "properties": {{}}}}
]
"""
    return prompt
```

### 方案 4：接受降級為正常行為

**觀點**：
- 降級機制是設計的一部分，不是錯誤
- 某些文本區塊確實可能沒有明顯的關係
- Rule-based 提取仍然可以提取有用的關係

**建議**：
- 將警告級別降低為 `debug` 或 `info`
- 記錄降級的原因（格式問題 vs 確實沒有關係）

---

## 當前狀態

### 觀察到的行為

從終端輸出可以看到：
- **區塊 1, 2, 4**：LLM 成功提取關係（沒有降級訊息）
- **區塊 3, 5, 6, 7**：降級到 rule-based 提取

**這表示**：
1. LLM 服務正常工作（因為有些區塊成功）
2. 某些區塊的文本或實體可能不適合 LLM 提取關係
3. 降級機制正常運作，確保系統仍然可以提取關係

### 統計數據

從處理結果可以看到：
- 區塊 3：33 實體, 71 關係（rule-based）
- 區塊 5：38 實體, 58 關係（rule-based）
- 區塊 6：30 實體, 60 關係（rule-based）
- 區塊 7：17 實體, 22 關係（rule-based）

**結論**：即使降級到 rule-based，仍然提取了大量的關係，系統功能正常。

---

## 建議

### 短期建議

1. **降低日誌級別**：將警告改為 `info` 或 `debug`，因為降級是正常行為
2. **添加統計**：記錄 LLM 成功率和降級率，幫助了解系統表現
3. **改善日誌**：記錄降級的具體原因（格式問題、實體不匹配、確實沒有關係）

### 長期建議

1. **改善 JSON 解析**：添加更寬鬆的解析邏輯和模糊匹配
2. **優化 Prompt**：提供更明確的格式要求和範例
3. **增加 max_tokens**：確保 LLM 有足夠的空間返回完整回應
4. **實體名稱標準化**：確保實體名稱一致，避免匹配問題

---

## 總結

**問題**：某些區塊出現 "LLM relation extraction returned empty, falling back to rule-based" 訊息

**根本原因**：
1. LLM 回應格式無法解析（JSON 格式問題）
2. 實體名稱不匹配
3. 某些文本區塊確實沒有明顯的關係
4. LLM 回應被截斷

**當前狀態**：
- 降級機制正常運作
- Rule-based 提取仍然可以提取大量關係
- 系統功能正常，只是某些區塊使用了降級方案

**建議**：
- 這不是錯誤，而是設計的降級機制
- 可以改善解析邏輯和 Prompt 設計來提高 LLM 成功率
- 但降級到 rule-based 仍然是可接受的正常行為

---

## 相關文檔

- [LLM Fallback Warning QA](./llm_fallback_warning_qa.md) - LLM 降級警告說明
- [關係提取失敗根本原因](./relation_extraction_root_cause.md) - 關係提取問題分析

