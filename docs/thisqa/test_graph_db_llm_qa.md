# 使用 graph.db + LLM 做 QA 問答測試

**更新時間**：2026-03-06  
**摘要**：新增「雙重驗證（Double Test）」章節與通過條件；補充 Gemini 改為 `config=GenerateContentConfig` 後的快速/完整驗證步驟。  
**更新時間**：2026-03-10  
**摘要**：如何透過主線 GraphRAG API 以 `data/graph.db` 搭配 LLM 進行問答測試；**僅依 RAG 來源回答，無匹配時回「未找到」**。並含 Refactor 後完整測試檢查清單。

---

## Refactor 後完整測試（檢查清單與執行順序）

在 LLM / Embedding 改為新 SDK `google.genai` 後，可依下列順序執行完整測試並填寫結果。

| 步驟 | 指令（均在 care_rag_api 根目錄） | 預期結果 | 實測日期 | 結果 |
|------|--------------------------------|----------|----------|------|
| 1. Stub 檢查 | `python -m scripts.check_stub_status` | Embedding 與 LLM 皆為「真實 API」 |  |  |
| 2. Gemini LLM | `python -m scripts.test_gemini_llm` | 所有項目 [OK] 通過 |  |  |
| 3. 整合測試 | `python -m scripts.test_integration` | 四項皆通過 |  |  |
| 4. Pytest API | `pytest tests/test_api/ -v` | 全部 passed |  |  |
| 5. E2E（需先啟動 API） | 啟動 API 後執行 `python scripts/test_graph_llm_qa.py` | 見下方 E2E 三情境 |  |  |

**一鍵執行步驟 1～4（不含 E2E）**：

```bash
python -m scripts.run_full_test_after_refactor
```

**E2E 三情境建議**（API 已啟動後）：

| 情境 | 指令 | 預期 |
|------|------|------|
| 批價 QA | `python scripts/test_graph_llm_qa.py --query "批價作業如何搜尋病患資料？"` | 有 sources，answer 依手冊/QA 內容 |
| IC 錯誤碼 | `python scripts/test_graph_llm_qa.py --query "IC 卡資料上傳錯誤代碼 [01] 代表什麼？"` | 答案含「資料型態檢核錯誤」等對照內容 |
| 無匹配（負向） | `python scripts/test_graph_llm_qa.py --query "火星探測車如何在火星表面導航？"` | answer 為「未找到」，sources 為空 |

**本次完整測試結果**（可於每次跑完後填寫）：

- 實測日期：___________
- 步驟 1～4：□ 全通過  □ 部分失敗（說明：___________）
- E2E 批價 QA：□ Pass  □ Fail
- E2E IC 錯誤碼：□ Pass  □ Fail
- E2E 無匹配：□ Pass  □ Fail

**注意**：在 Windows 終端機（cp950）執行步驟 3 時，若出現 `UnicodeEncodeError`，可設定 `PYTHONIOENCODING=utf-8` 或於 `scripts/test_integration.py` 將 ✅/❌ 改為 ASCII。步驟 4 中 `test_sse_stream_empty_query` 若預期空 query 回 200，需與目前 API（空 query 回 422）行為一致後再調整測試。

---

## 雙重驗證（Double Test）— 確認 Gemini 真實 API 可用、無 Stub

在修改 `generation_config` 改為 `config=GenerateContentConfig` 後，可用以下方式**雙重驗證**是否為真實 API、行為正確。

### 快速雙重驗證（兩步）

在 **care_rag_api** 根目錄執行：

```bash
# 1) Stub 狀態：確認 Embedding / LLM 皆為「真實 API」
python -m scripts.check_stub_status

# 2) Gemini 單元：確認 generate / 串流皆呼叫成功（6/6 通過）
python -m scripts.test_gemini_llm
```

**通過條件**：Stub 檢查顯示 LLM 為真實 API；`test_gemini_llm` 輸出「總計: 6/6 測試通過」。

### 完整雙重驗證（含整合與 E2E）

```bash
# 步驟 1～4 一鍵（Stub + Gemini + 整合 + pytest）
python -m scripts.run_full_test_after_refactor
```

E2E（需先啟動 API，例如 `scripts\run_api.bat`）：

```bash
# 確認查詢走真實 LLM、答案非 Stub
python scripts/test_graph_llm_qa.py --query "IC 卡資料上傳錯誤代碼 [01] 代表什麼？"
```

**通過條件**：回答內容為「資料型態檢核錯誤」等對照內容，且**不含** `[Gemini Stub]` 或整段 prompt 重複。

---

## 流程說明

- **graph.db** 由 `scripts/process_thisqa_to_graph.py`（或 `process_pdf_to_graph.py`）建出，內有實體與關係。
- 主線查詢 **`POST /api/v1/query`** 會：
  1. 用 **向量檢索**（RAG）取相關內容
  2. 用 **graph.db**（`GraphOrchestrator`）做圖增強（實體/關係查詢）
  3. **僅依檢索與圖合併後的來源** 當 context 送給 LLM 產出回答；**若無任何匹配來源，直接回「未找到」**，不讓 LLM 泛答

因此「用 graph.db + LLM 做 QA」＝ 啟動 API 後呼叫 `/api/v1/query`；回答一定來自 RAG 來源，無來源則固定為「未找到」。

---

## 測試計畫執行步驟（Step-by-step）

| 步驟 | 動作 | 驗證 |
|------|------|------|
| 1 | 檢查 port 8000：執行 `netstat -ano` 並篩選 `:8000` | 若有複數 PID，用 `taskkill /PID <PID> /F` 關閉多餘 process |
| 2 | 在 **care_rag_api** 目錄啟動 API：`scripts\run_api.bat` 或 `uvicorn app.main:app --host 0.0.0.0 --port 8000` | 瀏覽 http://localhost:8000/ 看到 `"Care RAG API is running!"` |
| 3 | 確認 `.env` 已設 `GOOGLE_API_KEY`（或所用 LLM 的 API key） | 有來源時才能產出回答 |
| 4 | 執行測試腳本：`python scripts/test_graph_llm_qa.py`（或加 `--query "單一問題"`） | 每題印出 `answer`、`來源數`；無來源時 answer 為「未找到」 |
| 5 | 對照結果：有 `sources` 的題目應有實質回答；無 `sources` 的題目 answer 必為「未找到」 | 符合「僅依 RAG 來源回答」行為 |

（若 graph.db 尚未建置，可先執行 `scripts/process_thisqa_to_graph.py --reset`，再跑 `scripts/check_db.py`、`scripts/verify_thisqa_graph.py` 確認內容。）

---

## 1. 確認 port 8000 無衝突後再啟動 API

若有多個 process 佔用 port 8000（例如舊的 uvicorn 或別專案），連到 **http://127.0.0.1:8000** 可能打到錯誤的 app 而回 **404**。請先檢查並釋放 8000，再啟動本 API。

**檢查誰佔用 8000**（PowerShell）：

```powershell
netstat -ano | findstr :8000
```

若有兩個 PID（例如一個聽 `0.0.0.0:8000`、一個聽 `127.0.0.1:8000`），關閉不需保留的那個：

```powershell
taskkill /PID <PID> /F
```

**啟動 API（務必從 care_rag_api 目錄啟動）**  

若從錯誤目錄執行 uvicorn，會載入別的 app，導致 **GET /** 與 **POST /api/v1/query** 都回 404。請任選其一，且**一定要在 care_rag_api 目錄下**執行：

**方式 A（建議）**：用腳本強制從 care_rag_api 目錄啟動，避免開錯專案：

```batch
cd C:\Development\langChain\source\care_rag\care_rag_api
scripts\run_api.bat
```

**方式 B**：手動在 care_rag_api 目錄執行：

```bash
cd C:\Development\langChain\source\care_rag\care_rag_api
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

啟動後，在瀏覽器開 **http://localhost:8000/** 應看到 `"message": "Care RAG API is running!"`。若看到 `{"detail": "Not Found"}` 或別的字樣，代表目前 8000 不是本 API，請關閉該服務後用上述方式重新啟動。

確保 `.env` 已設定 **GOOGLE_API_KEY**（或你使用的 LLM provider 的 API key），否則 LLM 無法產出回答。

---

## 2. 用 curl 測試一筆問答

先確認 API 是否為本專案：瀏覽 **http://localhost:8000/** 應看到 `"message": "Care RAG API is running!"`。再開 **http://localhost:8000/docs**，在 Swagger 裡可看到 `POST /api/v1/query`，可直接在頁面試送請求。

**Windows（PowerShell）** 建議用單行、或把 JSON 寫進檔案避免跳脫問題：

```powershell
# 單行（JSON 用單引號包、內部雙引號照寫）
curl -X POST "http://localhost:8000/api/v1/query" -H "Content-Type: application/json" -H "X-API-Key: test-api-key" -d '{\"query\": \"批價作業如何搜尋病患資料？\", \"top_k\": 5}'
```

**若一直重複回「未找到」**：可能是先前結果被快取。請任選其一：(1) 重啟 API 清空快取後再問一次；(2) 呼叫時帶上 `skip_cache: true`（本專案 `scripts/test_graph_llm_qa.py` 已預設帶上，會略過快取取得新結果）。

若仍回 **404 Not Found**：
- 確認啟動的是本專案：在 `care_rag_api` 目錄執行 `uvicorn app.main:app --host 0.0.0.0 --port 8000`。
- 或改用 **Swagger**：打開 http://localhost:8000/docs，找到 **POST /api/v1/query**，點 Try it out 輸入 `query`、`top_k` 後執行。
- 或改用腳本：`python scripts/test_graph_llm_qa.py --query "批價作業如何搜尋病患資料？"`。

（Linux/macOS 用 `\` 換行，單引號包 JSON；Windows 用 `^` 換行，雙引號內用 `\"`。）

回應會包含：
- `answer`：**僅依** graph + 向量檢索合併後的 **sources** 產出的回答；若無匹配來源則為 **「未找到」**
- `sources`：引用來源（空則 answer 必為「未找到」）
- `query`：你的問題

---

## 3. 用腳本連續問多題（推薦）

專案內提供腳本，可一次送多個問題並印出回答：

```bash
python scripts/test_graph_llm_qa.py
```

或指定單一問題：

```bash
python scripts/test_graph_llm_qa.py --query "日樺加沙颱風天災就醫識別碼怎麼上傳？"
```

詳見腳本內說明與 `--help`。

---

## 4. 其他呼叫方式

- **SSE 串流**：`GET /api/v1/query/stream?query=你的問題`（回答會以串流回傳）
- **WebSocket**：連到 `ws://localhost:8000/api/v1/ws/query`，送 `{"query": "你的問題"}` 可做即時問答
- **知識庫查詢（含圖）**：`POST /api/v1/knowledge/query`，可帶 `include_graph: true` 取得圖實體/關係，見 [README](README.md) 與 [API 範例](../api_query_examples.md)

---

## 5. 預期行為與驗證

- **有匹配來源**：`answer` 僅根據 `sources` 內容產出，不會出現與來源無關的泛答。
- **無匹配來源**：`answer` 固定為 **「未找到」**，`sources` 為空陣列。
- 驗證方式：跑 `python scripts/test_graph_llm_qa.py`，對照 `sources` 數量與 `answer` 是否一致（有來源才有實質回答，無來源必為「未找到」）。
- 若想直接檢查「Thisqa QA 是否被 Graph + 向量檢索召回」，可執行：

  ```bash
  python scripts/verify_thisqa_qa_vector.py --query "批價作業如何搜尋病患資料？"
  ```

  預期會看到最前面的結果為文件 `衛生所門診批價管理系統操作指引.md` 中那題「如何搜尋病患的批價資料？」的 QA Entity。

## 6. 注意事項

- **graph.db** 需已建好（例如已跑過 `process_thisqa_to_graph.py --reset`），否則圖增強無資料，僅以向量來源回答。
- 若只回「未找到」或與預期不符，可先跑 `python scripts/check_db.py`、`python scripts/verify_thisqa_graph.py` 確認 graph.db 內容是否正確。
- 確保 **GOOGLE_API_KEY**（或所用 LLM 的 API key）已在 `.env` 設定，否則無法產出有來源時的回答。

## 7. 診斷「未找到」根因（先確認是哪一環）

**先釐清**：回「未找到」是因為「檢索沒帶出該筆」還是「有帶出但 LLM 仍回未找到」？

執行診斷腳本（與 API 相同環境、同一 graph/vector）：

```bash
python -m scripts.diagnose_not_found --query "IC 卡資料上傳錯誤代碼 [01] 代表什麼？"
```

腳本會列出：
- 檢索到的筆數與每筆的 `id`、`score`、content 預覽
- 若查詢含 `[01]` 等錯誤代碼，會檢查預期實體 `doc_thisqa_ic_error_qa_1` 是否在結果中

解讀：
- **該實體不在檢索結果中** → 根因是 **檢索**：qa_vectors.db 未含該筆、或 embedding 排序讓其他 QA 排在前面。需從建索引（process_thisqa_to_graph）、或檢索邏輯/參數著手。
- **該實體在檢索結果中** → 根因是 **LLM**：送給模型的 context 已有答案，但模型仍回「未找到」。需檢查是否為 Stub、或調整 prompt/模型行為。

API 日誌也會在「有來源但 LLM 回未找到」時打出 `source_ids=`，可對照檢索到的 id 列表。

---

## 8. 排查：有來源數卻回「未找到」（依日誌追蹤）

若測試顯示 **來源數: 5** 但 **A: 未找到**，請看 **API 終端機** 的日誌：

1. **`GraphRAG query completed: 5 sources, graph_enhanced=False`**  
   表示 5 筆來自 **向量檢索**，圖未增強（或圖無匹配）。

2. **`RAG context: 5 sources, ... first_source_preview='...'`**  
   若 `first_source_preview` 為 **`'相關文件內容 1'`**（或 2、3…），代表目前 **VectorService 為 stub**，回傳的是假資料，不是真實文件。LLM 依「僅依參考資料」規則會正確回「未找到」。  
   **處理**：要得到真實回答，需接上真實向量庫（或依賴圖增強：確保 graph.db 有資料且查詢能命中實體，使 `graph_enhanced=True` 並用圖來源生成答案）。

3. 若 `first_source_preview` 已是真實手冊/QA 內文，但 LLM 仍回「未找到」，可能是參考內容與問題不相關（檢索或切塊需調整）。

---

## 9. 本次實測結果摘要（2026-03-10）

- **雙重驗證（Double Test）**  
  - 2026-03-06 執行：`check_stub_status` → Embedding / LLM 皆為真實 API；`test_gemini_llm` → 6/6 通過。Gemini 已改用 `config=GenerateContentConfig`，真實 API 正常、無 Stub。

- **Thisqa 批價 QA 問題**  
  - 指令：`python scripts/test_graph_llm_qa.py --query "批價作業如何搜尋病患資料？"`  
  - 結果：  
    - `answer`：成功依 `衛生所門診批價管理系統操作指引.md` 中對應 QA，說明如何在批價系統中輸入病患資料、使用搜尋功能查詢批價紀錄（含 4 個步驟）。  
    - `sources`：5 筆（來自 Thisqa 資料，含對應 QA）。  
  - 判定：**Pass**（GraphRAG + QA embedding 已能正確回答此關鍵問題）。

- **IC 錯誤碼問句（[01]）**  
  - 指令：`python scripts/test_graph_llm_qa.py --query "IC 卡資料上傳錯誤代碼 [01] 代表什麼？"`  
  - 結果：  
    - `answer`：回覆「資料型態檢核錯誤」等說明，內容對應 `IC卡資料上傳錯誤對照.txt` 中 `[01]: 資料型態檢核錯誤` 的中文註釋  
    - `sources`：目前 5 筆（包含 Thisqa 相關 QA 與文件）；未來可進一步優化，只保留最相關的 IC 對照來源  
  - 判定：**Pass**（IC 錯誤碼 [01] 已能由 GraphRAG + QA/圖來源回答，且答案來自對照表內容）。

- **無關問題（負向測試）**  
  - 指令：`python scripts/test_graph_llm_qa.py --query "火星探測車如何在火星表面導航？"`  
  - 結果：  
    - `answer`：`未找到`  
    - `sources`：0  
  - 判定：**Pass**（對於與醫療/Thisqa 無關的問題，系統不會憑空編造答案，符合「僅依 RAG 來源回答」設計）。
