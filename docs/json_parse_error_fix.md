# JSON 解析錯誤修復說明

## 錯誤訊息

```
Failed to parse relation response: Expecting value: line 1 column 2 (char 1)
Failed to parse entity response: Expecting value: line 1 column 2 (char 1)
```

## 根本原因

### 問題 1: LLM 回應格式不匹配

**當前狀況**：
- `LLMService` 目前是 stub 實作，返回的是簡單文字，不是 JSON 格式
- 例如：`"[Gemini] 回答: {prompt}\n\n這是一個基於 Gemini 模型的回答..."`

**問題**：
- `EntityExtractor` 期望 LLM 返回 JSON 格式的實體和關係列表
- 正則表達式 `r'\[.*\]'` 可能匹配到非 JSON 的文字（例如包含 `[` 和 `]` 的普通文字）
- 當嘗試 `json.loads()` 時，如果匹配到的不是有效的 JSON，就會拋出 `JSONDecodeError`

### 問題 2: 正則表達式過於寬鬆

**原始代碼**：
```python
json_match = re.search(r'\[.*\]', response, re.DOTALL)
```

**問題**：
- 這個正則表達式會匹配任何包含 `[` 和 `]` 的文字
- 如果 LLM 回應中包含 `[Gemini]` 或 `[OpenAI]` 這樣的文字，也會被匹配
- 但這些不是有效的 JSON，導致解析失敗

## 修復方案

### 1. 改進 JSON 提取邏輯

**新的實現**：
- 使用多種模式嘗試提取 JSON：
  1. Markdown JSON 代碼塊：` ```json [...] ``` `
  2. 普通代碼塊：` ``` [...] ``` `
  3. 直接 JSON 陣列：`[...]`
- 使用非貪婪匹配（`.*?`）避免匹配過多內容
- 添加更嚴格的驗證

### 2. 改進錯誤處理

**改進前**：
```python
except Exception as e:
    self.logger.warning(f"Failed to parse relation response: {str(e)}")
```

**改進後**：
```python
except json.JSONDecodeError as e:
    self.logger.debug(f"Failed to parse relation response as JSON: {str(e)}")
    self.logger.debug(f"Response preview: {response[:200]}")
except Exception as e:
    self.logger.warning(f"Failed to parse relation response: {str(e)}")
```

**優點**：
- 區分 JSON 解析錯誤和其他錯誤
- 使用 `debug` 級別記錄 JSON 錯誤（因為這是預期的，當 LLM 返回非 JSON 時）
- 記錄回應預覽，方便調試

### 3. 添加數據驗證

**改進**：
- 檢查解析後的數據類型（確保是 list）
- 檢查每個項目是否為 dict
- 驗證必要欄位存在（如 `name`、`source`、`target`）

## 為什麼會出現這個警告？

### 當前情況

1. **LLM 服務是 stub**：
   - `LLMService.generate()` 返回的是簡單文字，不是 JSON
   - 這是預期的行為（因為是 stub 實作）

2. **降級機制**：
   - 當 JSON 解析失敗時，系統會：
     - 記錄警告（現在改為 debug 級別）
     - 使用規則基礎的實體提取作為降級方案
     - 繼續處理，不會中斷流程

3. **不影響功能**：
   - 雖然有警告，但系統仍能正常運作
   - 會使用降級方案提取實體和關係

## 解決方案選項

### 選項 1: 改進 LLM 服務（推薦，長期）

實作真正的 LLM 整合，讓 LLM 返回正確的 JSON 格式：

```python
# 在 LLMService 中實作真正的 API 呼叫
# 並確保返回 JSON 格式的實體和關係
```

### 選項 2: 改進解析邏輯（已完成）

- ✅ 使用更嚴格的正則表達式
- ✅ 添加多種 JSON 提取模式
- ✅ 改進錯誤處理
- ✅ 添加數據驗證

### 選項 3: 調整日誌級別（已完成）

- ✅ 將 JSON 解析錯誤從 `warning` 改為 `debug`
- ✅ 因為這是預期的行為（當 LLM 返回非 JSON 時）

## 當前狀態

### 已修復

1. ✅ 改進 JSON 提取邏輯
2. ✅ 添加多種提取模式
3. ✅ 改進錯誤處理
4. ✅ 調整日誌級別

### 預期行為

- 當 LLM 返回非 JSON 格式時，會記錄 debug 訊息（不會顯示警告）
- 系統會使用降級方案繼續處理
- 不會中斷處理流程

## 測試建議

### 測試 JSON 解析

```python
# 測試各種回應格式
test_responses = [
    '[{"name": "測試", "type": "Concept"}]',  # 直接 JSON
    '```json\n[{"name": "測試"}]\n```',      # Markdown JSON
    '[Gemini] 回答: ...',                     # 非 JSON（應該優雅處理）
]

for response in test_responses:
    entities = extractor._parse_entity_response(response, "")
    print(f"提取到 {len(entities)} 個實體")
```

## 相關檔案

- `app/core/entity_extractor.py` - 實體提取器（已修復）
- `app/services/llm_service.py` - LLM 服務（stub 實作）


