## Thisqa QA Graph 重建計畫

- **最後更新時間**：2026-03-06 17:56
- **負責人**：AI Assistant

### 目標

- **清空並重建 `data/graph_qa.db`**，只保留來自 `data/Thisqa` 目錄的 QA 與 IC 卡錯誤規格資料。
- 資料來源：
  - `data/Thisqa/衛生所醫令系統操作指南與常見問題彙編.md`
  - `data/Thisqa/衛生所病歷與掛號系統操作指南.md`
  - `data/Thisqa/衛生所門診批價管理系統操作指引.md`
  - `data/Thisqa/IC卡資料上傳錯誤對照.txt`

### 最終圖結構設計

- **QA 文件與問答**
  - `Document(type="qa_markdown")`：對應每一個 Thisqa Markdown 檔。
  - `QA` 實體：
    - `properties`：`question`、`answer`、`scenario`、`keywords`、`steps`、`notes`、`qa_number`、`qa_title`、`metadata`、`source="qa_markdown"`。
  - 關係：
    - `CONTAINS_QA`：`Document -> QA`，並記錄 `qa_number` / `qa_index`。

- **IC 卡欄位與錯誤規格**
  - `Document(type="ic_error_spec")`：對應 `IC卡資料上傳錯誤對照.txt`。
  - `IC_Field`：欄位代碼（`Mxx`、`Dxx`、`Exx` 等）。
    - `properties`：`field_id`、`section`、`description`、`raw_line`、`source`。
  - `IC_Error`：錯誤代碼（`01`、`AD69`、`Y016` 等）。
    - `properties`：`code`、`message`、`category`、`related_field_ids`、`raw_line`、`source`。
  - 關係：
    - `CONTAINS_FIELD`：`Document -> IC_Field`
    - `CONTAINS_ERROR`：`Document -> IC_Error`
    - `ERROR_ON_FIELD`：`IC_Error -> IC_Field`（由錯誤說明文字中出現的欄位代碼推得）。

### 腳本一：重置 QA 圖資料庫

- 檔案：`scripts/reset_graph_qa_db.py`
- 功能：
  - 針對 `./data/graph_qa.db` 進行安全重置（**不刪檔，只清空表格**）：
    - 若檔案存在：列出統計資訊、確認沒有鎖定後，使用 SQLite 直接 `DELETE FROM relations; DELETE FROM entities;` 清空兩張表。
    - 若檔案不存在：自動建立空的 SQLite 檔並初始化 `entities` / `relations` 表。
  - 支援選項：
    - `--confirm`：略過互動式確認直接重置。
- 使用方式：
  ```bash
  # 建議在關閉 API 服務後執行
  python scripts/reset_graph_qa_db.py --confirm
  ```

### 腳本二：匯入 Thisqa Markdown QA

- 檔案：`scripts/import_thisqa_markdown_batch.py`
- 依賴：`scripts/parse_qa_markdown_to_graph.py`
- 策略：
  - Thisqa 的 3 個 Markdown 檔是嚴格 Q&A 模板（Q / Scenario / Keywords / Question / Answer / Steps / Notes / Metadata），
    直接沿用既有的 `parse_qa_markdown()` + `process_qa_markdown_to_graph()` 而非長文抽問答。
  - `parse_qa_markdown()` 已調整支援兩種標題格式：
    - 舊格式：`## **1. Q: 標題**`（以 `---` 分隔各題）。
    - Thisqa 格式：`## Q: 標題`（以 `## Q:` 切分區塊，依出現順序自動編號）。
- 行為：
  - 掃描 `data/Thisqa` 目錄下的所有 `.md` 檔（不包含 IC 卡錯誤 `.txt` 檔）。
  - 對每個 `.md` 檔呼叫：
    - `process_qa_markdown_to_graph(md_path, document_id=前綴+檔名, db_path="./data/graph_qa.db")`
  - 建議使用固定的 Document ID 前綴，例如：
    - `thisqa_衛生所病歷與掛號系統操作指南`
    - `thisqa_衛生所醫令系統操作指南與常見問題彙編`
    - `thisqa_衛生所門診批價管理系統操作指引`
  - 為每個檔案在 `graph_qa.db` 中建立一個 `Document(type="qa_markdown")` 及其對應的 `QA` / `CONTAINS_QA`（目前每本 20 題，總計 60 題）。
- 使用方式：
  ```bash
  python scripts/import_thisqa_markdown_batch.py \
    --qa-dir "data/Thisqa" \
    --db-path "./data/graph_qa.db" \
    --doc-id-prefix "thisqa_"
  ```

### 腳本三：匯入 Thisqa 版 IC 卡錯誤對照

- 檔案：`scripts/import_ic_error_spec_to_qa_graph.py`
- 調整重點：
  - 預設 `--spec-file` 指向 `data/Thisqa/IC卡資料上傳錯誤對照.txt`。
  - 建議固定 `--doc-id ic_error_spec_main`，並搭配 `--overwrite-doc`，確保永遠只有一套最新 IC 規格資料。
- 使用方式：
  ```bash
  python scripts/import_ic_error_spec_to_qa_graph.py ^
    --spec-file "data/Thisqa/IC卡資料上傳錯誤對照.txt" ^
    --db-path "./data/graph_qa.db" ^
    --doc-id "ic_error_spec_main" ^
    --overwrite-doc
  ```

### 建庫完整流程（一次重建）

1. **重置 QA 資料庫**
   ```bash
   python scripts/reset_graph_qa_db.py --confirm
   ```

2. **匯入 3 本 Thisqa 操作指引的 QA**
   ```bash
   python scripts/import_thisqa_markdown_batch.py \
     --qa-dir "data/Thisqa" \
     --db-path "./data/graph_qa.db" \
     --doc-id-prefix "thisqa_"
   ```

3. **匯入 Thisqa 版 IC 卡錯誤對照**
   ```bash
   python scripts/import_ic_error_spec_to_qa_graph.py ^
     --spec-file "data/Thisqa/IC卡資料上傳錯誤對照.txt" ^
     --db-path "./data/graph_qa.db" ^
     --doc-id "ic_error_spec_main" ^
     --overwrite-doc
   ```

4. **驗證結果**
   ```bash
   python scripts/query_qa_graph.py
   ```

- 期望結果：
  - 文件列表只包含 3 個 Thisqa QA 文件 + 1 個 `ic_error_spec_main`：
    - `thisqa_衛生所病歷與掛號系統操作指南`
    - `thisqa_衛生所醫令系統操作指南與常見問題彙編`
    - `thisqa_衛生所門診批價管理系統操作指引`
    - `ic_error_spec_main`
  - `CONTAINS_QA` 僅來自 3 本操作指引，總數約為 60（每本 20 題）。
  - `CONTAINS_FIELD`、`CONTAINS_ERROR`、`ERROR_ON_FIELD` 只來自 Thisqa 的 IC 卡錯誤對照檔（目前為 89 個欄位、240 個錯誤碼及其關聯）。

