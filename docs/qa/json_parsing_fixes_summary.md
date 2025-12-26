# JSON 解析問題修復總結

**更新時間：2025-12-26 16:15**  
**作者：AI Assistant**  
**修改摘要：修復 LLM 實體提取返回空和 JSON 解析問題的完整總結**

---

## 問題概述

在 PDF 處理過程中，頻繁出現以下問題：
1. "LLM entity extraction returned empty, falling back to rule-based"
2. "LLM relation extraction returned empty, falling back to rule-based"
3. "Failed to extract relations (LLM-based): cannot access local variable 'json' where it is not associated with a value"

## 根本原因分析

### 問題 1：JSON 提取正則表達式使用非貪婪匹配導致截斷

**證據**：
- debug.log 顯示 LLM 返回了有效的 JSON（包含多個實體）
- 但解析後返回空列表
- 正則表達式 `r'(\[[\s\S]*?\])'` 使用非貪婪匹配 `*?`，可能只匹配到第一個 `]`，導致 JSON 不完整

**影響**：
- JSON 陣列被截斷，只匹配到部分內容
- JSON 解析失敗，返回空列表
- 觸發降級到 rule-based 提取

### 問題 2：變數作用域問題 - "cannot access local variable 'json'"

**證據**：
- 終端顯示：`Failed to extract relations (LLM-based): cannot access local variable 'json' where it is not associated with a value`
- 在 `_parse_relation_response` 方法中，有些地方使用 `import json`，有些地方使用 `import json as json_module`
- 當在 except 塊中使用 `json` 時，如果之前沒有執行到 `import json`，就會報錯

**影響**：
- 關係提取失敗
- 觸發降級到 rule-based 提取

### 問題 3：JSON 解析失敗時缺少詳細日誌

**證據**：
- debug.log 只記錄了 response_preview（200 字元），不足以診斷完整的 JSON 解析問題
- 沒有記錄提取到的 json_str 和解析錯誤的詳細信息

**影響**：
- 難以診斷 JSON 解析失敗的根本原因
- 無法追蹤匹配到的正則表達式模式

## 修復方案

### 修復 1：改善 JSON 提取正則表達式

**文件**：`app/core/entity_extractor.py`

**修改位置**：
- `_parse_entity_response` 方法（約行 370-373）
- `_parse_relation_response` 方法（約行 512-516）

**修改內容**：
```python
# 修改前：
json_patterns = [
    r'```json\s*(\[.*?\])\s*```',  # markdown JSON 代碼塊（非貪婪）
    r'```\s*(\[.*?\])\s*```',      # 普通代碼塊（非貪婪）
    r'(\[[\s\S]*?\])',             # 直接 JSON 陣列（非貪婪）- 問題所在
]

# 修改後：
json_patterns = [
    (r'```json\s*(\[.*?\])\s*```', 'markdown_json_codeblock'),  # markdown JSON 代碼塊（非貪婪，但代碼塊內完整）
    (r'```\s*(\[.*?\])\s*```', 'codeblock'),      # 普通代碼塊（非貪婪，但代碼塊內完整）
    (r'(\[[\s\S]*\])', 'direct_array'),              # 直接 JSON 陣列（貪婪匹配，匹配到最後一個 ]）
]
```

**關鍵改變**：
- 第三個模式從 `*?`（非貪婪）改為 `*`（貪婪），確保匹配完整的 JSON 陣列
- 添加模式名稱追蹤，記錄匹配到的正則表達式模式

### 修復 2：統一 json 模組導入，修復變數作用域問題

**文件**：`app/core/entity_extractor.py`

**修改位置**：
- 文件頂部已統一導入 `import json`
- 移除所有局部的 `import json` 和 `import json as json_module`

**修改內容**：
- 移除 `extract_entities` 方法中的 3 處局部 `import json`（行 68, 99, 122）
- 移除 `extract_relations` 方法中的 1 處局部 `import json`（行 168）
- 移除 `_rule_based_relation_extraction` 方法中的 1 處局部 `import json`（行 814）
- 所有使用 `json` 的地方都使用文件頂部統一導入的模組

### 修復 3：增強 JSON 解析失敗的日誌記錄

**文件**：`app/core/entity_extractor.py`

**修改位置**：
- `_parse_entity_response` 方法（約行 408-466）
- `_parse_relation_response` 方法（約行 549-705）

**修改內容**：
1. 記錄提取到的 json_str（前 1000 字元）
2. 記錄 JSON 解析錯誤的詳細信息
3. 記錄原始回應的完整長度
4. 記錄匹配到的正則表達式模式（matched_pattern）
5. 記錄 JSON 字符串長度

**新增日誌字段**：
- `json_str_preview`: 提取到的 JSON 字符串預覽
- `json_str_length`: JSON 字符串長度
- `matched_pattern`: 匹配到的正則表達式模式名稱
- `response_length`: 原始回應長度

### 修復 4：添加 JSON 完整性驗證

**文件**：`app/core/entity_extractor.py`

**修改位置**：
- `_parse_entity_response` 方法（約行 400-423）
- `_parse_relation_response` 方法（約行 540-562）

**修改內容**：
在解析 JSON 前，驗證 JSON 字符串的完整性（平衡括號）

```python
if json_str:
    json_str = json_str.strip()
    
    # 驗證 JSON 完整性：檢查 [ 和 ] 數量是否匹配
    open_brackets = json_str.count('[')
    close_brackets = json_str.count(']')
    if open_brackets != close_brackets:
        self.logger.warning(
            f"JSON string appears incomplete: {open_brackets} opening brackets, "
            f"{close_brackets} closing brackets"
        )
        # 記錄到 debug.log
        # ...
        return entities/relations  # 返回空列表，觸發降級
    
    # 嘗試解析 JSON
    data = json.loads(json_str)
```

## 修復效果

### 預期改善

1. **減少實體提取返回空的情況**：
   - 修復 JSON 解析問題後，應該能正確解析 LLM 返回的 JSON
   - 貪婪匹配確保匹配完整的 JSON 陣列

2. **消除變數作用域錯誤**：
   - 統一導入後，不再出現 "cannot access local variable 'json'" 錯誤

3. **更好的診斷能力**：
   - 詳細的日誌記錄幫助診斷剩餘的解析問題
   - 記錄匹配到的正則表達式模式，便於追蹤問題

4. **提高 GraphRAG 品質**：
   - 正確提取實體後，關係提取也會更準確
   - 減少降級到 rule-based 提取的情況

### 測試建議

1. **運行 PDF 處理腳本**：
   ```bash
   python scripts/process_pdf_to_graph.py "data/example/1051219長期照護2.0核定本.pdf"
   ```

2. **檢查 debug.log**：
   - 查看是否有 "JSON string appears incomplete" 警告
   - 查看 matched_pattern 字段，確認匹配模式
   - 查看 json_str_preview，確認提取到的 JSON 是否完整

3. **驗證實體提取成功率**：
   - 統計 "LLM entity extraction returned empty" 出現次數
   - 對比修復前後的降級頻率

## 相關文檔

- [正則表達式：貪婪匹配 vs 非貪婪匹配詳細說明](./regex_greedy_vs_non_greedy_explanation.md)
- [LLM 關係提取返回空結果分析](./llm_relation_extraction_empty_analysis.md)
- [LLM 實體提取返回空結果分析](./llm_entity_extraction_empty_analysis.md)（待創建）

## 技術細節

### 正則表達式對比

**非貪婪匹配** `*?`：
- 盡可能匹配更少字元
- 遇到第一個 `]` 就停止
- 可能截斷 JSON 陣列

**貪婪匹配** `*`：
- 盡可能匹配更多字元
- 匹配到最後一個 `]` 才停止
- 確保匹配完整的 JSON 陣列

### JSON 完整性驗證

**檢查項目**：
- `[` 和 `]` 數量是否匹配
- JSON 字符串是否完整
- 是否包含有效的 JSON 結構

**處理方式**：
- 如果括號不匹配，記錄警告並返回空列表
- 觸發降級到 rule-based 提取
- 記錄詳細信息到 debug.log

## 更新歷史

- **2025-12-26 16:15**: 完成所有修復，包括正則表達式、json 導入、日誌記錄和完整性驗證
- **2025-12-26 15:50**: 增強日誌記錄，添加更多上下文信息
- **2025-12-26 15:43**: 改善實體名稱匹配邏輯，添加模糊匹配

