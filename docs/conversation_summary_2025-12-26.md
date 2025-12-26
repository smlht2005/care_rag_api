# Care RAG API 對話總結 - 2025-12-26

**對話時間**：2025-12-26 15:50 - 16:36  
**主要議題**：JSON 解析問題修復、PDF 重複處理行為分析、資料庫重置功能

---

## 對話概述

本次對話主要解決了三個核心問題：
1. **JSON 解析失敗導致 LLM 實體/關係提取返回空**
2. **PDF 重複處理時的數據追加 vs 覆蓋行為**
3. **資料庫重置和清理功能**

---

## 主要成果

### 1. JSON 解析問題完整修復

**問題**：
- "LLM entity extraction returned empty, falling back to rule-based"
- "LLM relation extraction returned empty, falling back to rule-based"
- "cannot access local variable 'json' where it is not associated with a value"

**根本原因**：
1. **正則表達式使用非貪婪匹配**：`r'(\[[\s\S]*?\])'` 只匹配到第一個 `]`，導致 JSON 陣列被截斷
2. **變數作用域問題**：局部 `import json` 導致在 except 塊中無法訪問
3. **缺少完整性驗證**：沒有檢查 JSON 括號平衡

**修復方案**（`app/core/entity_extractor.py`）：

**修復 1：正則表達式改為貪婪匹配**
```python
# 修改前：
r'(\[[\s\S]*?\])',  # 非貪婪匹配 ❌

# 修改後：
r'(\[[\s\S]*\])',   # 貪婪匹配 ✅
```

**修復 2：統一 json 模組導入**
- 移除所有局部的 `import json`（5 處）
- 統一使用文件頂部導入的 json 模組

**修復 3：增強日誌記錄**
- 記錄 `json_str_preview`（前 1000 字元）
- 記錄 `matched_pattern`（匹配到的正則表達式模式）
- 記錄 `json_str_length`、`response_length`

**修復 4：添加 JSON 完整性驗證**
- 檢查 `[` 和 `]` 數量是否匹配
- 如果不匹配，記錄警告並返回空列表觸發降級

**影響範圍**：
- `_parse_entity_response` 方法
- `_parse_relation_response` 方法

**預期效果**：
- 減少 "LLM extraction returned empty" 的出現頻率
- 消除變數作用域錯誤
- 提升診斷能力

### 2. PDF 重複處理行為分析

**問題**：重複轉換 PDF 時，數據是追加還是覆蓋？

**核心發現**：

1. **資料庫使用 `INSERT OR REPLACE`**：
   - 如果 ID 相同會覆蓋
   - 但由於實體 ID 是隨機生成的 UUID，實際上不會覆蓋

2. **文件 ID 生成**：
   - 預設每次運行生成新的 UUID：`doc_{pdf_name}_{uuid[:8]}`
   - 如果指定 `--doc-id`，使用指定的 ID

3. **實體 ID 生成**：
   - 每次提取都使用 `uuid.uuid4()` 生成新的 UUID
   - 即使實體名稱相同，也會生成不同的 ID

4. **實際行為**：
   - **預設行為**：追加（因為所有 ID 都不同）
   - **問題**：會產生重複的實體（相同名稱但不同 ID）

**解決方案：添加 `--overwrite` 選項**

**實作**（`scripts/process_pdf_to_graph.py`）：
- 添加 `--overwrite` 命令行參數
- 在處理前檢查是否存在相同來源的 Document 實體
- 如果找到，刪除所有相關的 chunk 實體和主文件實體
- 級聯刪除會自動刪除 CONTAINS 關係

**使用方法**：
```bash
python scripts/process_pdf_to_graph.py "data/example/file.pdf" --overwrite
```

### 3. 資料庫重置功能

**問題**：如何清理所有數據重新開始？

**解決方案：創建重置腳本**

**新文件**：`scripts/reset_graph_db.py`

**功能**：
- 顯示當前資料庫統計信息
- 安全刪除現有資料庫文件
- 創建全新的乾淨資料庫
- 驗證新資料庫是否正確創建
- **自動檢查資料庫鎖定狀態**
- **改進的 Ctrl+C 處理**

**使用方法**：
```bash
# 帶確認提示
python scripts/reset_graph_db.py

# 自動確認
python scripts/reset_graph_db.py --confirm
```

**後續修復**（2025-12-26 16:45）：
- **資料庫鎖定問題**：添加 `check_db_lock()` 函數檢查資料庫是否被其他進程鎖定
- **錯誤處理**：添加重試機制（最多 3 次，指數退避：1秒、2秒、4秒）
- **Ctrl+C 問題**：改進信號處理，添加全局 `_interrupted` 標誌
- **錯誤提示**：添加詳細的錯誤信息和解決方案提示

---

## 創建/修改的文件

### 修改的文件

1. **`app/core/entity_extractor.py`**
   - 修復正則表達式（非貪婪→貪婪）
   - 統一 json 模組導入
   - 增強日誌記錄
   - 添加 JSON 完整性驗證

2. **`scripts/process_pdf_to_graph.py`**
   - 添加 `--overwrite` 選項
   - 實作數據清理邏輯

3. **`README.md`**
   - 添加 "PDF 處理和 GraphRAG 構建" 章節
   - 添加 "重置 GraphRAG 資料庫" 章節
   - 添加 "常見問題" 章節
   - 更新專案結構說明

### 新建的文件

1. **`scripts/reset_graph_db.py`**
   - 重置資料庫腳本

2. **`docs/qa/regex_greedy_vs_non_greedy_explanation.md`**
   - 正則表達式詳細說明文檔

3. **`docs/qa/json_parsing_fixes_summary.md`**
   - JSON 解析問題修復總結

4. **`docs/qa/pdf_repeat_processing_data_behavior.md`**
   - PDF 重複處理行為分析

5. **`docs/qa/reset_graph_db_guide.md`**
   - 重置資料庫使用指南

6. **`docs/conversation_summary_2025-12-26.md`**
   - 本次對話總結（本文件）

7. **`docs/qa/uvicorn_ctrl_c_shutdown_fix.md`** ⭐ 新增
   - Uvicorn Ctrl+C 無法停止服務問題的完整修復文檔

### 修改的文件（後續修復）

1. **`scripts/reset_graph_db.py`**
   - 修復資料庫鎖定錯誤處理
   - 添加資料庫鎖定檢查功能
   - 改進 Ctrl+C 信號處理
   - 添加重試機制（最多 3 次，指數退避）
   - 添加詳細的錯誤提示和解決方案

2. **`docs/qa/reset_graph_db_guide.md`**
   - 添加資料庫鎖定問題的解決方案
   - 添加 Ctrl+C 無法停止問題的解決方案
   - 添加常見問題（Q&A）章節

3. **`app/main.py`** ⭐ 新增
   - 修復 lifespan shutdown 階段的 `CancelledError` 處理
   - 添加超時保護（2秒）避免清理操作阻塞
   - 使用 `try-finally` 確保清理總會執行
   - 明確處理 `asyncio.CancelledError` 並重新拋出

4. **`app/core/graph_store.py`** ⭐ 新增
   - 改進 `close()` 方法的取消處理
   - 添加 `CancelledError` 處理和強制關閉邏輯
   - 確保連接引用被正確清理

---

## 技術要點

### 正則表達式：貪婪 vs 非貪婪

**關鍵差異**：
- **非貪婪 `*?`**：盡可能匹配更少，遇到第一個 `]` 就停止 → 可能截斷 JSON
- **貪婪 `*`**：盡可能匹配更多，匹配到最後一個 `]` 才停止 → 確保完整 JSON

**適用場景**：
- **非貪婪**：有明確邊界的場景（如 markdown 代碼塊）
- **貪婪**：沒有明確邊界的場景（如直接 JSON 陣列）

### 資料庫操作：INSERT OR REPLACE

**行為**：
- 如果 ID 存在：覆蓋（REPLACE）
- 如果 ID 不存在：插入（INSERT）

**實際影響**：
- 由於實體 ID 是隨機生成的 UUID，實際上不會覆蓋
- 需要使用 `--overwrite` 選項來清理重複數據

### 數據清理策略

**`--overwrite` 選項的清理邏輯**：
1. 查找所有 Document 類型的實體
2. 檢查 `properties.source` 是否匹配 PDF 路徑
3. 先刪除所有相關的 chunk 實體
4. 再刪除主文件實體（級聯刪除 CONTAINS 關係）

**注意**：
- 只刪除 Document 類型的實體
- 其他實體（Person、Organization 等）不會被刪除（可能被多個文件共享）

---

## 相關文檔

- [正則表達式詳細說明](qa/regex_greedy_vs_non_greedy_explanation.md)
- [JSON 解析問題修復總結](qa/json_parsing_fixes_summary.md)
- [PDF 重複處理行為分析](qa/pdf_repeat_processing_data_behavior.md)
- [重置資料庫指南](qa/reset_graph_db_guide.md)
- [QA 文檔索引](qa/README.md)

---

## 給未來 Agent 的重要提醒

### 1. JSON 解析相關

- **正則表達式**：直接 JSON 陣列必須使用貪婪匹配 `*`，不要使用非貪婪 `*?`
- **json 導入**：統一在文件頂部導入，不要在方法內局部導入
- **完整性驗證**：解析前檢查括號平衡，避免解析不完整的 JSON

### 2. PDF 處理相關

- **重複處理**：預設行為是追加，會產生重複實體
- **清理數據**：使用 `--overwrite` 選項清理相同來源的數據
- **重置資料庫**：使用 `scripts/reset_graph_db.py` 完全重置

### 3. 資料庫操作

- **INSERT OR REPLACE**：如果 ID 相同會覆蓋，但實體 ID 是隨機生成的，實際上不會覆蓋
- **級聯刪除**：刪除實體會自動刪除相關的關係（CONTAINS）
- **數據清理**：需要手動查找和刪除，無法依賴 ID 匹配

### 4. 日誌記錄

- **debug.log**：重要診斷信息記錄到 `.cursor/debug.log`
- **日誌格式**：使用 JSON 格式，包含 sessionId、runId、hypothesisId、location、message、data、timestamp
- **日誌內容**：記錄 json_str_preview、matched_pattern、response_length 等關鍵信息

---

## 測試建議

### 驗證 JSON 解析修復

```bash
# 運行 PDF 處理腳本
python scripts/process_pdf_to_graph.py "data/example/file.pdf"

# 檢查 debug.log
# 查看是否有 "JSON string appears incomplete" 警告
# 查看 matched_pattern 字段
# 查看 json_str_preview 是否完整
```

### 驗證 --overwrite 選項

```bash
# 第一次處理
python scripts/process_pdf_to_graph.py "data/example/file.pdf"

# 第二次處理（應該清理舊數據）
python scripts/process_pdf_to_graph.py "data/example/file.pdf" --overwrite
```

### 驗證重置功能

```bash
# 重置資料庫
python scripts/reset_graph_db.py --confirm

# 重新導入 PDF
python scripts/process_pdf_to_graph.py "data/example/file.pdf"

# 驗證數據
python scripts/check_db.py
```

---

## 更新歷史

- **2025-12-26 16:50**: 修復 uvicorn 服務 Ctrl+C 無法停止的根本原因
- **2025-12-26 16:45**: 修復重置腳本的資料庫鎖定和 Ctrl+C 問題
- **2025-12-26 16:36**: 創建對話總結文檔
- **2025-12-26 16:27**: 實作 `--overwrite` 選項
- **2025-12-26 16:20**: PDF 重複處理行為分析
- **2025-12-26 16:15**: JSON 解析問題完整修復
- **2025-12-26 16:00**: 正則表達式詳細說明

