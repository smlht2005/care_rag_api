# JSON 解析錯誤問答

## Q: 為什麼會出現 "Failed to parse relation response" 錯誤？

**A:** 這個錯誤出現的原因是：

### 根本原因

1. **LLM 服務是 Stub**
   - `LLMService.generate()` 返回的是簡單文字，不是 JSON
   - 例如：`"[Gemini] 回答: {prompt}\n\n這是模擬回答..."`

2. **EntityExtractor 期望 JSON**
   - 期望 LLM 返回 JSON 格式的實體和關係列表
   - 例如：`[{"name": "張三", "type": "Person"}, ...]`

3. **正則表達式匹配錯誤**
   - 原始正則 `r'\[.*\]'` 會匹配任何包含 `[` 和 `]` 的文字
   - 如果回應中有 `[Gemini]`，也會被匹配
   - 但 `"[Gemini]"` 不是有效的 JSON，導致解析失敗

---

## Q: 這個錯誤會影響系統運行嗎？

**A:** **不會**，這是預期的行為：

### 為什麼不會影響？

1. **有降級機制**
   - 當 JSON 解析失敗時，系統會使用規則基礎的實體提取
   - 不會中斷處理流程

2. **錯誤處理完善**
   - 使用 `try-except` 捕獲錯誤
   - 記錄警告但不中斷執行

3. **系統仍能運作**
   - 雖然提取的實體和關係可能不準確
   - 但基本的圖構建功能仍能運作

---

## Q: 如何修復這個錯誤？

**A:** 已經修復，包含以下改進：

### 1. 改進 JSON 提取邏輯

**改進前**：
```python
json_match = re.search(r'\[.*\]', response, re.DOTALL)
```

**改進後**：
```python
# 使用多種模式
json_patterns = [
    r'```json\s*(\[.*?\])\s*```',  # markdown JSON
    r'```\s*(\[.*?\])\s*```',      # 普通代碼塊
    r'(\[[\s\S]*?\])',             # 直接 JSON（非貪婪）
]
```

### 2. 改進錯誤處理

**改進前**：
```python
except Exception as e:
    self.logger.warning(f"Failed to parse: {str(e)}")
```

**改進後**：
```python
except json.JSONDecodeError as e:
    self.logger.debug(f"Failed to parse as JSON: {str(e)}")  # debug 級別
    self.logger.debug(f"Response preview: {response[:200]}")
except Exception as e:
    self.logger.warning(f"Failed to parse: {str(e)}")
```

### 3. 添加數據驗證

```python
if isinstance(data, list):
    for item in data:
        if isinstance(item, dict) and "name" in item:
            # 驗證通過，建立實體
```

---

## Q: 為什麼將錯誤級別從 warning 改為 debug？

**A:** 因為這是**預期的行為**：

### 原因

1. **Stub 實作是預期的**
   - LLM 服務是 Stub，返回非 JSON 是正常的
   - 這不是真正的錯誤，而是預期的行為

2. **避免誤導**
   - `warning` 級別會讓開發者以為有問題
   - 實際上系統運作正常

3. **減少噪音**
   - 大量警告訊息會掩蓋真正的問題
   - 使用 `debug` 級別，只在需要時查看

---

## Q: 如何完全消除這個錯誤？

**A:** 有兩個選項：

### 選項 1: 實作真正的 LLM 整合（推薦）

```python
# 實作真實的 LLM API 呼叫
async def generate(self, prompt: str) -> str:
    # 確保返回 JSON 格式
    response = await real_llm_api(prompt)
    return response  # 應該是 JSON 格式
```

**優點**：
- 真正的 AI 功能
- 可以提取真實的實體和關係

**缺點**：
- 需要 API Key
- 需要網路連線
- 可能產生費用

### 選項 2: 改進 Stub 返回 JSON

```python
# 讓 Stub 也返回 JSON 格式
async def generate(self, prompt: str) -> str:
    return json.dumps([
        {"name": "測試實體", "type": "Concept", "properties": {}}
    ])
```

**優點**：
- 不需要真實 API
- 可以測試 JSON 解析邏輯

**缺點**：
- 仍然是模擬數據
- 不是真正的 AI 回答

---

## Q: 錯誤訊息 "Expecting value: line 1 column 2 (char 1)" 是什麼意思？

**A:** 這是 JSON 解析錯誤的詳細訊息：

### 解釋

- **"Expecting value"**: JSON 解析器期望找到一個值
- **"line 1 column 2"**: 在第 1 行第 2 個字元位置
- **"char 1"**: 字串中的第 1 個字元（從 0 開始）

### 例子

```python
# 嘗試解析無效的 JSON
json.loads("[Gemini]")  # 錯誤：Expecting value: line 1 column 2 (char 1)
#                      ^
#                      位置 1（第 2 個字元）
```

**原因**：
- `[` 是有效的 JSON 陣列開始
- 但 `G` 不是有效的 JSON 值開始
- 所以解析器在位置 1 報告錯誤

---

## Q: 如何調試 JSON 解析錯誤？

**A:** 使用以下方法：

### 1. 查看回應內容

```python
# 在解析前記錄回應
self.logger.debug(f"LLM Response: {response}")
self.logger.debug(f"Response length: {len(response)}")
```

### 2. 測試 JSON 有效性

```python
import json

try:
    data = json.loads(json_str)
    print("✅ Valid JSON")
except json.JSONDecodeError as e:
    print(f"❌ Invalid JSON: {e}")
    print(f"Error at position: {e.pos}")
    print(f"Text around error: {json_str[max(0, e.pos-20):e.pos+20]}")
```

### 3. 使用 JSON 驗證工具

```python
# 使用 json.tool 驗證
import json
import sys

try:
    json.loads(json_str)
    print("Valid JSON")
except json.JSONDecodeError as e:
    print(f"Invalid JSON: {e}", file=sys.stderr)
```

---

## Q: 為什麼有些區塊能成功，有些失敗？

**A:** 取決於文字內容：

### 成功的情況

- 文字中包含有效的 JSON 格式
- 或者正則表達式匹配到有效的 JSON

### 失敗的情況

- 文字中只包含 `[Gemini]` 這樣的標籤
- 或者沒有包含任何 JSON 格式的內容

### 例子

**成功**：
```python
response = "[{\"name\": \"測試\", \"type\": \"Concept\"}]"
# 可以成功解析
```

**失敗**：
```python
response = "[Gemini] 回答: 這是測試文字"
# 正則匹配到 "[Gemini]"，但不是有效 JSON
```

---

## 相關檔案

- `app/core/entity_extractor.py` - 實體提取器（已修復）
- `app/services/llm_service.py` - LLM 服務（Stub）
- `docs/json_parse_error_fix.md` - 詳細修復說明


