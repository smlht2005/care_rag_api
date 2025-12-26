# 正則表達式：貪婪匹配 vs 非貪婪匹配詳細說明

**更新時間：2025-12-26 16:00**  
**作者：AI Assistant**  
**修改摘要：詳細解釋貪婪匹配和非貪婪匹配的差異，以及它們如何影響 JSON 解析**

---

## 基本概念

### 貪婪匹配（Greedy Matching）

**符號**：`*`、`+`、`?`（預設行為）

**行為**：盡可能匹配**最多**的字元，直到無法繼續匹配為止。

**範例**：
```python
import re

text = "abc[123][456]def"
pattern_greedy = r'\[.*\]'  # 貪婪匹配

match = re.search(pattern_greedy, text)
print(match.group())  # 輸出: "[123][456]"
```

**匹配過程**：
1. 找到第一個 `[`
2. `.*` 開始匹配，**盡可能匹配更多字元**
3. 匹配到 `123][456`（跳過中間的 `]`）
4. 遇到最後一個 `]` 時停止
5. **結果**：`[123][456]`（匹配了兩個 JSON 陣列）

### 非貪婪匹配（Non-greedy / Lazy Matching）

**符號**：`*?`、`+?`、`??`

**行為**：盡可能匹配**最少**的字元，一旦滿足條件就停止。

**範例**：
```python
import re

text = "abc[123][456]def"
pattern_non_greedy = r'\[.*?\]'  # 非貪婪匹配

match = re.search(pattern_non_greedy, text)
print(match.group())  # 輸出: "[123]"
```

**匹配過程**：
1. 找到第一個 `[`
2. `.*?` 開始匹配，**盡可能匹配更少字元**
3. 遇到第一個 `]` 就立即停止
4. **結果**：`[123]`（只匹配了第一個 JSON 陣列）

---

## 在當前代碼中的問題

### 當前代碼（有問題）

**文件**：`app/core/entity_extractor.py:368`

```python
json_patterns = [
    r'```json\s*(\[.*?\])\s*```',  # markdown JSON 代碼塊（非貪婪）
    r'```\s*(\[.*?\])\s*```',      # 普通代碼塊（非貪婪）
    r'(\[[\s\S]*?\])',             # 直接 JSON 陣列（非貪婪）- ⚠️ 問題所在
]
```

### 問題場景

假設 LLM 返回以下回應：

```json
```json
[
  {"name": "張文瓊", "type": "Person", "properties": {}},
  {"name": "吳淑瓊", "type": "Person", "properties": {}},
  {"name": "社區發展季刊", "type": "Document", "properties": {}},
  {"name": "陳正芬", "type": "Person", "properties": {}}
]
```
```

### 非貪婪匹配的問題

**使用非貪婪匹配** `r'(\[[\s\S]*?\])'`：

1. **匹配過程**：
   - 找到第一個 `[`
   - `[\s\S]*?` 開始匹配
   - **遇到第一個 `]` 就停止**（可能在 JSON 陣列中間）
   - 結果：可能只匹配到 `[{"name": "張文瓊"}]` 或更短

2. **實際問題**：
   - 如果 JSON 陣列包含多個項目，非貪婪匹配可能只匹配到第一個項目的部分內容
   - 導致 JSON 不完整，解析失敗

### 貪婪匹配的解決方案

**使用貪婪匹配** `r'(\[[\s\S]*\])'`：

1. **匹配過程**：
   - 找到第一個 `[`
   - `[\s\S]*` 開始匹配，**盡可能匹配更多字元**
   - 匹配到最後一個 `]` 才停止
   - 結果：匹配完整的 JSON 陣列 `[{...}, {...}, {...}]`

2. **優點**：
   - 確保匹配完整的 JSON 陣列
   - 不會因為中間的 `]` 而提前停止

---

## 詳細對比範例

### 範例 1：簡單 JSON 陣列

**輸入文字**：
```
請返回以下 JSON：
[
  {"name": "實體1", "type": "Person"},
  {"name": "實體2", "type": "Organization"}
]
這是回應的結尾。
```

**非貪婪匹配** `r'(\[[\s\S]*?\])'`：
- **匹配結果**：`[{"name": "實體1", "type": "Person"}]` ❌（不完整）
- **問題**：在第一個 `]` 處停止，漏掉了第二個實體

**貪婪匹配** `r'(\[[\s\S]*\])'`：
- **匹配結果**：`[{"name": "實體1", "type": "Person"}, {"name": "實體2", "type": "Organization"}]` ✅（完整）
- **優點**：匹配到最後一個 `]`，包含所有實體

### 範例 2：嵌套 JSON（更複雜的情況）

**輸入文字**：
```
```json
[
  {"name": "實體1", "properties": {"key": "value"}},
  {"name": "實體2", "properties": {"nested": {"deep": "value"}}}
]
```
```

**非貪婪匹配** `r'(\[[\s\S]*?\])'`：
- **可能匹配**：`[{"name": "實體1", "properties": {"key": "value"}}]` ❌
- **問題**：在嵌套對象的第一個 `]` 處停止

**貪婪匹配** `r'(\[[\s\S]*\])'`：
- **匹配結果**：完整的 JSON 陣列 ✅
- **優點**：正確處理嵌套結構

---

## 為什麼非貪婪匹配會導致解析失敗？

### 問題鏈

1. **非貪婪匹配截斷 JSON**：
   ```
   原始 JSON: [{"name": "A"}, {"name": "B"}]
   匹配結果: [{"name": "A"}]  ← 不完整
   ```

2. **JSON 解析失敗**：
   ```python
   json.loads('[{"name": "A"}]')  # 如果這是截斷的，可能缺少閉合括號
   # 可能導致 JSONDecodeError 或解析為不完整的數據
   ```

3. **實體列表為空**：
   ```python
   entities = []  # 解析失敗，返回空列表
   ```

4. **觸發降級**：
   ```python
   if not entities:
       # 降級到 rule-based 提取
   ```

---

## 解決方案對比

### 方案 1：使用貪婪匹配（推薦）

**優點**：
- ✅ 確保匹配完整的 JSON 陣列
- ✅ 處理嵌套結構
- ✅ 簡單直接

**缺點**：
- ⚠️ 如果回應中包含多個 JSON 陣列，可能匹配到最後一個（但這在我們的場景中不是問題）

**實作**：
```python
json_patterns = [
    r'```json\s*(\[.*?\])\s*```',  # markdown 代碼塊內使用非貪婪（代碼塊邊界已確定）
    r'```\s*(\[.*?\])\s*```',      # 普通代碼塊內使用非貪婪（代碼塊邊界已確定）
    r'(\[[\s\S]*\])',              # 直接 JSON 陣列使用貪婪匹配 ✅
]
```

### 方案 2：平衡括號匹配（更精確但複雜）

**優點**：
- ✅ 精確匹配平衡的括號
- ✅ 處理複雜嵌套

**缺點**：
- ⚠️ 實作複雜
- ⚠️ 性能較差

**實作**：
```python
def extract_balanced_json(text):
    """提取平衡的 JSON 陣列"""
    start = text.find('[')
    if start == -1:
        return None
    
    bracket_count = 0
    for i in range(start, len(text)):
        if text[i] == '[':
            bracket_count += 1
        elif text[i] == ']':
            bracket_count -= 1
            if bracket_count == 0:
                return text[start:i+1]
    return None
```

### 方案 3：組合方案（最佳實踐）

**實作**：
```python
json_patterns = [
    r'```json\s*(\[.*?\])\s*```',  # markdown JSON 代碼塊（代碼塊邊界已確定，非貪婪即可）
    r'```\s*(\[.*?\])\s*```',      # 普通代碼塊（代碼塊邊界已確定，非貪婪即可）
    r'(\[[\s\S]*\])',              # 直接 JSON 陣列（使用貪婪匹配）✅
]

# 如果匹配成功，驗證 JSON 完整性
if json_str:
    # 驗證括號平衡
    open_brackets = json_str.count('[')
    close_brackets = json_str.count(']')
    if open_brackets == close_brackets:
        # 嘗試解析
        data = json.loads(json_str)
    else:
        # JSON 不完整，記錄錯誤
        logger.warning(f"JSON appears incomplete: {open_brackets} opening, {close_brackets} closing")
```

---

## 實際案例分析

### 從 debug.log 看到的問題

**debug.log 行 2500**：
```json
{
  "response_preview": "```json\n[\n  {\"name\": \"張文瓊\", \"type\": \"Person\", \"properties\": {}},\n  {\"name\": \"吳淑瓊\", \"type\": \"Person\", \"properties\": {}},\n  {\"name\": \"社區發展季刊\", \"type\": \"Document\", \"properties\": {}},\n  {\"name\": \"陳正芬\", \"t"
}
```

**觀察**：
- LLM 返回了有效的 JSON（包含多個實體）
- response_preview 被截斷（只顯示前 200 字元），但實際回應應該更長
- 解析後返回空列表，表示 JSON 解析失敗

**可能的原因**：
1. **非貪婪匹配截斷**：正則表達式只匹配到部分 JSON
2. **JSON 不完整**：匹配到的 JSON 字符串缺少閉合括號
3. **解析錯誤**：JSON 格式正確但解析邏輯有問題

---

## 視覺化對比

### 非貪婪匹配流程

```
輸入: "文字 [項目1] [項目2] 更多文字"
      ↓
找到第一個 [
      ↓
.*? 開始匹配（非貪婪）
      ↓
遇到第一個 ] 立即停止
      ↓
結果: "[項目1]"  ← 不完整！
```

### 貪婪匹配流程

```
輸入: "文字 [項目1] [項目2] 更多文字"
      ↓
找到第一個 [
      ↓
.* 開始匹配（貪婪）
      ↓
匹配所有字元，直到最後一個 ]
      ↓
結果: "[項目1] [項目2]"  ← 完整！
```

---

## 建議的修復

### 修復 1：改為貪婪匹配

```python
# 修改前：
r'(\[[\s\S]*?\])',  # 非貪婪匹配 ❌

# 修改後：
r'(\[[\s\S]*\])',   # 貪婪匹配 ✅
```

### 修復 2：添加 JSON 完整性驗證

```python
if json_str:
    json_str = json_str.strip()
    
    # 驗證括號平衡
    open_brackets = json_str.count('[')
    close_brackets = json_str.count(']')
    
    if open_brackets != close_brackets:
        self.logger.warning(
            f"JSON string appears incomplete: "
            f"{open_brackets} opening brackets, {close_brackets} closing brackets"
        )
        # 記錄到 debug.log
        # ...
        return []  # 返回空列表，觸發降級
    
    # 嘗試解析
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        # 記錄詳細錯誤
        # ...
```

### 修復 3：增強日誌記錄

記錄以下信息以便診斷：
- 提取到的 json_str（完整內容）
- JSON 字符串長度
- 括號數量（開閉）
- 解析錯誤詳情

---

## 總結

### 關鍵差異

| 特性 | 貪婪匹配 (`*`) | 非貪婪匹配 (`*?`) |
|------|---------------|------------------|
| **匹配行為** | 盡可能匹配更多 | 盡可能匹配更少 |
| **停止條件** | 無法繼續匹配 | 滿足最小條件即停止 |
| **適用場景** | 匹配完整結構（如完整 JSON） | 匹配單個項目（如單個標籤） |
| **當前問題** | ✅ 正確匹配完整 JSON | ❌ 可能截斷 JSON |

### 當前代碼的問題

1. **非貪婪匹配導致截斷**：`r'(\[[\s\S]*?\])'` 可能只匹配到部分 JSON
2. **缺少完整性驗證**：沒有檢查 JSON 是否完整
3. **日誌不足**：無法診斷具體的解析失敗原因

### 建議的修復

1. **改為貪婪匹配**：`r'(\[[\s\S]*\])'` 確保匹配完整 JSON
2. **添加完整性驗證**：檢查括號平衡
3. **增強日誌記錄**：記錄詳細的解析過程

---

## 相關文檔

- [LLM 關係提取返回空結果分析](./llm_relation_extraction_empty_analysis.md)
- [正則表達式參考](https://docs.python.org/3/library/re.html)

