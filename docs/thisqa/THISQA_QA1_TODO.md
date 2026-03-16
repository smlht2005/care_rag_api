# Thisqa / IC QA1 重構 TODO 清單

**更新時間：** 2026-03-10  
**適用：** Thisqa QA（批價/病歷與掛號/醫令 + IC 錯誤碼與欄位對照）

---

## 1. Phase 1：IC 錯誤碼 QA1（已完成程式實作，待文件補齊）

- [ ] 在 `test_graph_db_llm_qa.md` 補充說明：
  - 實體 ID 規則：`doc_thisqa_ic_error_qa_<CODE>`（例如：`01`、`C001`、`Y011`、`D086`）。
  - Properties：`code` / `question` / `answer` / `keywords` / `document_id` / `source_file`。
  - 實測案例與預期：
    - `IC 卡資料上傳錯誤代碼 [01] 代表什麼？` → 答案：**資料型態檢核錯誤**，來源數 1。
    - `IC 卡資料上傳錯誤代碼 [C001] 代表什麼？` → 答案：**資料重複：鍵值資料已存在**，來源數 1。
    - `IC 卡資料上傳錯誤代碼 [Y011]` / `[D086]` 等其它碼 → 皆對應 `IC卡資料上傳錯誤對照.txt`，來源數 1。

- [ ] 在 `REFACTOR_TEST_REPORT.md` 紀錄 Phase 1 測試項與結果：
  - 建圖：`python -m scripts.process_thisqa_to_graph --reset --file "IC卡資料上傳錯誤對照.txt"`。
  - 查詢腳本：`python scripts/test_graph_llm_qa.py --query "IC 卡資料上傳錯誤代碼 [XX] 代表什麼？"`。
  - `diagnose_not_found`：`python -m scripts.diagnose_not_found --query "<同一題>"`，expected id 應為 `doc_thisqa_ic_error_qa_<CODE>`。

---

## 2. Phase 2：IC 欄位 QA1（程式已實作，需文件 + 驗證）

- [ ] 說明欄位 QA1 ID 規則：
  - `doc_thisqa_ic_field_<CODE>`（例如：`doc_thisqa_ic_field_M01`、`doc_thisqa_ic_field_D01`、`doc_thisqa_ic_field_H00`）。

- [ ] 在 `test_graph_db_llm_qa.md` 新增「IC 欄位 QA1 測試」一節：
  - 範例查詢與預期：
    - `IC 卡欄位 M01 代表什麼？` → 答案包含：**安全模組代碼**，來源數 1。
    - 視需求再加一兩個 D/H 欄位測試（例如 `D01`、`H00`）。

- [ ] 在 `REFACTOR_TEST_REPORT.md` 補 Phase 2 測試項與結果：
  - 建圖：`python -m scripts.process_thisqa_to_graph --reset`（處理三個 .md + IC .txt）。
  - 查詢：
    - `python scripts/test_graph_llm_qa.py --query "IC 卡欄位 M01 代表什麼？"`。
    - 確認答案來源來自欄位 QA1（`doc_thisqa_ic_field_M01`），來源數 1。

---

## 3. 建圖與檢索行為（Graph / Vector / Callback）

- [ ] 在 `QA_GRAPH_BUILD_PLAN.md` 補充設計說明：
  - Thisqa `.md` → 產生 `Entity(type="QA")`，ID：`<doc_id>_qa_<idx>`。
  - `IC卡資料上傳錯誤對照.txt` → 產生 `Entity(type="QA1")` 兩類：
    - 欄位 QA1：`doc_thisqa_ic_field_<CODE>`，來源為檔案開頭「欄位與中文對照表」。
    - 錯誤碼 QA1：`doc_thisqa_ic_error_qa_<CODE>`，來源為「錯誤代碼:中文對照註釋」。
  - 兩類 QA1 都會寫入 `qa_vectors.db`，供 `VectorService` 做語意檢索。

- [ ] 在 `test_graph_db_llm_qa.md` 的診斷區補充：
  - `scripts.diagnose_not_found` 會根據查詢中的 `[CODE]` 檢查 `doc_thisqa_ic_error_qa_<CODE>` 是否在檢索結果中。
  - `scripts/debug_list_ic_error_entities.py` 可檢視單一錯誤碼 QA1（01 / C001）的 `type/code/question/answer`。

---

## 4. LLM / rule-based fallback 行為（建圖時的預期）

- [ ] 在 `EMBEDDING_TROUBLESHOOTING.md` 或新段落中說明：
  - 建圖時若 LLM 回傳的 JSON 不完整（`JSON string appears incomplete: ...`）或完全空白：
    - `EntityExtractor` 會先嘗試：
      - 去掉 ```json/``` code fence；
      - 以 `_extract_json_array_from_response` 找出 JSON 陣列；
      - 砍到最後一個 `}` 再補 `]` / `}]` 嘗試修復。
    - 修復成功 → console 會印 `Repaired incomplete JSON (entity/relation)`，並使用修復後的 LLM 結果。
    - 修復失敗或 LLM 回空 → console 會印：
      - `LLM entity extraction returned empty, falling back to rule-based`
      - `LLM relation extraction returned empty, falling back to rule-based...`
      → 代表該 chunk 由 rule-based 建圖，不影響 GraphRAG 與 QA 功能。

---

## 5. 指令彙總（方便重跑）

- [ ] 建圖（全部）：

  ```bash
  python -m scripts.process_thisqa_to_graph --reset
  ```

- [ ] 錯誤碼 QA1 測試：

  ```bash
  python scripts/test_graph_llm_qa.py --query "IC 卡資料上傳錯誤代碼 [01] 代表什麼？"
  python scripts/test_graph_llm_qa.py --query "IC 卡資料上傳錯誤代碼 [C001] 代表什麼？"
  ```

- [ ] 欄位 QA1 測試：

  ```bash
  python scripts/test_graph_llm_qa.py --query "IC 卡欄位 M01 代表什麼？"
  ```

- [ ] 診斷工具：

  ```bash
  python -m scripts.diagnose_not_found --query "IC 卡資料上傳錯誤代碼 [01] 代表什麼？"
  python -m scripts.diagnose_not_found --query "IC 卡資料上傳錯誤代碼 [C001] 代表什麼？"
  python -m scripts.debug_list_ic_error_entities   # 列出 01 / C001 QA1 實體內容
  ```
