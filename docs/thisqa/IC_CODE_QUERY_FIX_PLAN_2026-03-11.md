# IC 欄位代碼 & 錯誤代碼查詢修正計畫

**更新時間：** 2026-03-11 10:05
**作者：** AI Assistant
**摘要：** 修正 VectorService 對 IC 欄位代碼（如 `[D12]`）與裸碼錯誤代碼（如 `AD61`）查詢的路由邏輯，確保正確取出對應 QA1 實體答案，而非 fallback 到 PDF 來源。

---

## 根本原因

### 案例 1：`[D12]` 欄位代碼查詢（含方括號但無「欄位」文字）

| 層次 | 問題 |
|------|------|
| `_try_get_ic_field_qa_source` | 有 `if not re.search(r"欄位\|欄位代碼", query): return None` 守衛，查詢含「資料」而非「欄位」時直接跳過，`doc_thisqa_ic_field_D12` 從未被查找 |
| `_try_get_ic_error_qa_source` | 偵測到 `[D12]` → 嘗試找 `doc_thisqa_ic_error_qa_D12`（不存在）→ `None` |
| keyword 索引 | `extract_ic_field_qa_from_txt` 只存了 `<D12>` 而未存 `[D12]`，keyword 搜尋無法命中 |

### 案例 2：`AD61` 錯誤代碼裸碼查詢（無方括號）

| 層次 | 問題 |
|------|------|
| `_try_get_ic_error_qa_source` | 正則 `\[\s*([A-Za-z0-9]+)\s*\]` 要求方括號，裸碼 `AD61` 完全不觸發，實體 `doc_thisqa_ic_error_qa_AD61`（答案：XCOVID 相關限制）從未被查找 |
| fallback | 兩個特殊查找皆 `None` → QA embedding 語意距離偏大 → 回傳 PDF 內容（錯誤） |

---

## 修改項目

### Fix 1：`app/services/vector_service.py` — `_try_get_ic_field_qa_source`

**移除**嚴格的「欄位」文字守衛，改為偵測欄位代碼格式本身：

修改前：
```python
if not re.search(r"欄位|欄位代碼", query):
    return None
m = re.search(r"\b([MDHV]\d{2})\b", query, flags=re.IGNORECASE)
```

修改後（支援 `[D12]`、`<D12>`、裸碼 `D12`）：
```python
# 支援 [D12] / <D12> / 裸碼 D12（欄位代碼首字為 M/D/H/V/E）
m = re.search(r"[<\[]\s*([MDHVE]\d{2})\s*[>\]]|\b([MDHVE]\d{2})\b", query, re.IGNORECASE)
if not m:
    return None
raw_code = (m.group(1) or m.group(2) or "").strip()
```

---

### Fix 2：`app/services/vector_service.py` — `_try_get_ic_error_qa_source` 欄位碼守衛

加入守衛：code 以 M/D/H/V/E + 2位數字（欄位代碼格式）時，跳過錯誤碼查找：

```python
# 欄位代碼（如 D12、M01）不屬於錯誤碼，交由 _try_get_ic_field_qa_source 處理
if re.match(r"^[MDHVE]\d{2}$", code, re.IGNORECASE):
    return None
```

插入於 `entity_id = f"{IC_ERROR_QA_ID_PREFIX}{code}"` 之前。

---

### Fix 3：`app/services/vector_service.py` — `_try_get_ic_error_qa_source` 裸碼偵測

**解決 AD61 案例**：括號偵測失敗後，若查詢含「錯誤代碼」上下文，嘗試偵測裸碼：

```python
code_match = re.search(r"\[\s*([A-Za-z0-9]+)\s*\]", query)
# 新增：裸碼偵測（如 AD61，適用於含「錯誤代碼/錯誤碼」上下文的查詢）
if not code_match and re.search(r"錯誤代碼|錯誤碼", query):
    code_match = re.search(r"\b([A-Za-z]{1,2}\d{2,4}|\d{1,4})\b", query, re.IGNORECASE)
```

搭配 Fix 2：即使裸碼偵測到 `D12`，Fix 2 也會攔截並交由欄位查找處理，兩個 fix 不衝突。

---

### Fix 4：`scripts/process_thisqa_to_graph.py` — `extract_ic_field_qa_from_txt` 關鍵字補齊

在 keywords 加入 `[{code}]` 格式與「資料」關鍵字：

```python
# 修改前
"keywords": [code, f"<{code}>", "IC 卡", "欄位", "欄位對照"],

# 修改後
"keywords": [code, f"<{code}>", f"[{code}]", "IC 卡", "欄位", "欄位對照", "資料"],
```

完成後需重新執行 `--file IC卡資料上傳錯誤對照.txt`（incremental，不 reset）讓新 keywords 寫入 graph.db。

---

## 驗證

```bash
# 欄位代碼（方括號，無「欄位」關鍵字）
python scripts/test_graph_llm_qa.py --query "IC 卡資料[D12] 代表什麼？"
# 預期回答含：委託或受託執行轉(代)

# 欄位代碼（標準格式，regression）
python scripts/test_graph_llm_qa.py --query "IC 卡欄位 M01 代表什麼？"
# 預期回答含：安全模組代碼

# 錯誤代碼（方括號格式，regression）
python scripts/test_graph_llm_qa.py --query "IC 卡資料上傳錯誤代碼 [01] 代表什麼？"
# 預期回答含：資料型態檢核錯誤

# 錯誤代碼（裸碼格式，新修正驗證）
python scripts/test_graph_llm_qa.py --query "IC 卡資料上傳錯誤代碼 AD61 代表什麼？"
# 預期回答含：XCOVID0001、XCOVID0002、XCOVID0004、XCOVID0005 相關限制
```

---

## 代碼類型識別邏輯總覽

| 格式 | 範例 | 對應 entity 前綴 | 處理方法 |
|------|------|-----------------|---------|
| `[01]` / `[C001]` / `[AD61]` | 方括號錯誤代碼 | `doc_thisqa_ic_error_qa_` | `_try_get_ic_error_qa_source`（現有） |
| 裸碼 + 「錯誤代碼」 | `AD61` | `doc_thisqa_ic_error_qa_` | `_try_get_ic_error_qa_source`（Fix 3 新增） |
| `[D12]` / `<D12>` / 裸碼 `D12` | 欄位代碼（MDHVE 前綴） | `doc_thisqa_ic_field_` | `_try_get_ic_field_qa_source`（Fix 1 放寬） |

---

## 修改檔案彙整

| 檔案 | 修改類型 | 對應 Fix |
|------|---------|---------|
| `app/services/vector_service.py` | 放寬欄位碼偵測 + 欄位碼守衛 + 裸碼偵測 | Fix 1 / 2 / 3 |
| `scripts/process_thisqa_to_graph.py` | keywords 補齊 [code] 與「資料」 | Fix 4 |
