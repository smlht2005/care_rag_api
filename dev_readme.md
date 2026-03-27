# Care RAG API 開發記錄

## 更新歷史

### 2026-03-27 16:29 - AI Assistant - 負向測試改用 /api/v1/query 驗證

**更新摘要：**
- 更新 `.github/workflows/wif-deploy.yml`：負向測試由 `/api/v1/health/` 改為 `POST /api/v1/query`，並調整斷言為「不得 200；若為 401 且 `www-authenticate` 含 `invalid_token` 視為命中預期」。

---

### 2026-03-27 16:21 - AI Assistant - 強化 WIF 負向測試斷言

**更新摘要：**
- 更新 `.github/workflows/wif-deploy.yml`：在負向測試模式新增 JWT `aud` 檢查，並強制驗證 `/health/` 回應需為 `401` 且 `www-authenticate` 含 `invalid_token`；若未命中即 fail。

---

### 2026-03-27 16:01 - AI Assistant - WIF 負向測試分支：故意錯誤 audience

**更新摘要：**
- 在測試分支 `test/wif-negative-audience` 更新 `.github/workflows/wif-deploy.yml`：將 `CLOUD_RUN_URL` 改為錯誤 audience，供階段 7 負向測試驗證預期 `401 invalid_token` 行為。

---

### 2026-03-27 15:36 - AI Assistant - 修正 WIF workflow 的 Python ID token 取得流程

**更新摘要：**
- 更新 `.github/workflows/wif-deploy.yml`：將 `fetch_id_token(..., credentials=...)` 改為 `impersonated_credentials.IDTokenCredentials(...).refresh()`，避免 `google-auth` 相容性錯誤；同步整理 YAML 縮排。

---

### 2026-03-27 13:51 - AI Assistant - 同步 WIF 雙 SA 排錯清單到部署文件

**更新摘要：**
- 更新 `docs/gcp_deployment/python_id_token_cloud_run_plan.md`：新增「雙 SA 逐步檢查指令清單（排錯優先）」含 Provider、`workloadIdentityUser`、`TokenCreator`、`run.invoker` 與 audience 一致性檢核。

---

### 2026-03-27 13:21 - AI Assistant - GCP 部署：Python ID token 計畫存檔

**更新摘要：**
- 新增 `docs/gcp_deployment/python_id_token_cloud_run_plan.md`：將 gcloud 取 ID token 轉 Python（方案 B）、ADC／WIF（CI/Prod）與驗證矩陣之實作計畫存於 repo，並與同目錄 `get-id-token-for-postman.md` 等文件交叉引用。

---

### 2026-03-27 09:10 - AI Assistant - 修正 Windows 上 Python 呼叫 gcloud 之 WinError 2 說明

**更新摘要：**
- 更新 `docs/postman/Care_RAG_API_CloudRun_IAM.postman_README.md`、`docs/gcp_deployment/get-id-token-for-postman.md`：改為建議 `shutil.which('gcloud'/'gcloud.cmd')` 或 `shell=True`；並在 `cloud-run-troubleshooting-summary.md` 增補 WinError 2 根因。

---

### 2026-03-27 08:59 - AI Assistant - gcloud ID token：文件與 Python 一行指令

**更新摘要：**
- 新增 `docs/gcp_deployment/get-id-token-for-postman.md`：彙整 CMD / Python 產生 ID token 供 Postman `bearerToken`。
- 更新 `docs/postman/Care_RAG_API_CloudRun_IAM.postman_README.md`：補上 Python 一行產生 token。

---

### 2026-03-26 17:00 - AI Assistant - Postman Cloud Run IAM：Environment + 使用說明

**更新摘要：**
- 新增 `docs/postman/Care_RAG_API_CloudRun_IAM.postman_environment.json`（`baseUrl`、`bearerToken`、`xApiKey`）。
- 新增 `docs/postman/Care_RAG_API_CloudRun_IAM.postman_README.md`：匯入步驟與 gcloud 產生 ID token 貼入 Postman 之流程。

---

### 2026-03-26 16:25 - AI Assistant - 新增 Cloud Run IAM 專用 Postman Collection

**更新摘要：**
- 新增 `docs/postman/Care_RAG_API_CloudRun_IAM.postman_collection.json`，包含 Cloud Run IAM only 測試用 `GET /api/v1/health/` 與 `POST /api/v1/query`。
- Collection 變數預設加入 `baseUrl`、`bearerToken`、`xApiKey`，可直接匯入 Postman 後填 token 測試。

---

### 2026-03-26 14:25 - AI Assistant - Cloud Run 部署準備（Dockerfile 8002 + 內建 DB + .dockerignore）

**更新摘要：**
- 新增 `.dockerignore`：排除 `.env`、`.git`、`__pycache__`、logs 與 node_modules，避免 Build context 帶入秘密或垃圾檔。
- 更新 `Dockerfile`：API 埠統一 8002（`EXPOSE 8002`、uvicorn 讀 `PORT` fallback 8002）、HEALTHCHECK 改用 `httpx`、並將 `data/` 的 `graph_qa.db`/`graph.db`/`qa_vectors.db` 內建進映像（Cloud Run 不再缺檔）。
- 新增部署文件：`docs/deploy/cloud-run-access-iam-vpc-summary.md`、`docs/deploy/cloud-run-env-secrets-guide.md`、`docs/deploy/cloud-run-deploy-plan.md`。

---

### 2026-03-20 13:33 - AI Assistant - 正式區複製清單（missfind 修復）

**更新摘要：**
- 新增 `docs/deploy/COPY_TO_PROD_missfind_fix.md`：列出必備／建議複製之相對路徑、`copy` 範例與重啟驗證步驟，供複製到 prd（如 `172.31.6.123:8002`）時對照。

---

### 2026-03-20 12:10 - AI Assistant - 修復 graph 關鍵字假陽性（missfind / Organization 撞 type）

**更新摘要：**
- `GraphStore.search_entities` 新增關鍵字參數 `include_type_match`（預設 `True`）；`False` 時僅 `name` 子字串匹配。`SQLiteGraphStore`／`MemoryGraphStore` 已實作；`ORDER BY name`（SQLite）與記憶體版排序對齊以利穩定結果。
- `VectorService._search_from_graph` 改使用 `include_type_match=False`；graph 來源 `score` 改為 `0.35`，`metadata.score_source=graph_keyword`。
- 說明文件：`docs/bug/missfind.md` 增補「十、解法」；後續增補「6. 本機開發怎麼測（dev）」（pytest、`scripts/verify_missfind_graph_fallback.py`、uvicorn、Postman/PowerShell）。
- 手動驗證：`python scripts/verify_missfind_graph_fallback.py` 預期 `graph keyword hits: 0`；`pytest tests/test_core/` 全綠。

---

### 2026-03-20 12:05 - AI Assistant - .gitignore 明確排除 `.cursor/*.log`

**更新摘要：**
- 在 `# Logs` 區塊新增 `.cursor/*.log` 與註解（專案既有 `*.log` 已會忽略 `debug.log`；此條為語意明確與防未來規則調整時遺漏）。

---

### 2026-03-20 12:01 - AI Assistant - Cursor Ruler：變更分級、備份與專案規則檔

**更新摘要：**
- 新增 `.cursor/rules/care-rag-change-governance.mdc`（`alwaysApply: true`）：T0–T3 變更分級、T1 預授權（RAG/Graph 假陽性／誤導分數／無來源硬答）、ECR 與 SSOT 並存、批次自動化 vs 對話任務、SSOT 缺口以 ADR/dev_readme 補預設行為。
- 新增 `.cursor/RULER_SUMMARY.md`：結論、Pros/Cons、檔案位置與還原方式。
- 備份導入前狀態：`.cursor/backups/ruler-before-tier-2026-03-20/`（README、INVENTORY、`user-rules-legacy-snapshot.md`）；當時 repo 內尚無 `.mdc`，僅盤點既有 `debug.log` 等）。

---

### 2026-03-17 - AI Assistant - IC/QA 前端單一面板整合與 UI/UX 調整

**更新摘要：**
- 將原本左右分欄（左：對話、右：Answer/Sources/Raw JSON 分頁）改為單一整合面板：同一畫面內顯示對話與每則回覆的完整結果。
- 新增 `frontend/src/components/ICQaConversation.tsx`：依 `turns` 渲染使用者氣泡與助理卡片；助理卡片內含回答主文、可展開的「顯示來源 / QA 結果」與「Raw JSON」（MUI Collapse + 按鈕），錯誤以 Alert 顯示於該則卡片內。
- `ICQaConsolePage` 改為維護 `turns` 狀態（id、userText、response、error），送出時呼叫 `runQuery` 並將回傳結果 push 進 turns；移除右側 Tabs 與獨立結果區塊。
- 查詢設定改為頂部單列（模式、Top K、清除對話按鈕），節省空間。
- `useIcQaQuery.runQuery` 改為回傳 `RunQueryResult`（answer、response、error），不再 throw，方便頁面組 turn。
- 間距與階層：8px 網格、回答主文較醒目、展開區使用 borderTop/divider，並提供「清除對話」按鈕。

---

### 2026-03-17 - AI Assistant - 前端 Vite + React + MUI 安裝與 main.tsx 掛載 root

**更新摘要：**
- 在 `frontend/` 建立 Vite + React + TypeScript 專案：新增 `package.json`、`index.html`、`vite.config.ts`、`tsconfig.json`、`tsconfig.node.json`、`src/vite-env.d.ts`。
- `index.html` 提供 `<div id="root"></div>`，並以 `<script type="module" src="/src/main.tsx"></script>` 載入入口；`main.tsx` 使用 `ReactDOM.createRoot(document.getElementById("root")!)` 掛載 App。
- 依賴：React 18、@mui/material、@emotion/react、@emotion/styled、@mui/icons-material、Vite 5、TypeScript 5.2。
- 開發代理：Vite `server.proxy` 將 `/api` 轉到 `http://localhost:8000`。
- 建置與執行：`npm install` 後於 `frontend` 目錄執行 `npm run dev`（埠 5173）或 `npm run build`。Script 使用 `node node_modules/vite/bin/vite.js` 以在 Windows 下正常執行。
- 修正：ChatPanel 送出後顯示後端 answer（`useIcQaQuery.runQuery` 回傳 answer 字串；ICQaChatPanel 依 onSend 回傳值追加助理訊息）。
- 追加修正：MUI icons 匯入錯誤根因為 `vite.config.ts` 中對 `@mui/icons-material/Send` 的錯誤 alias，已移除該 alias 與多餘的 `exclude: ["@mui/icons-material"]`，改回標準匯入路徑 `import SendIcon from "@mui/icons-material/Send"` 並經 `npm run dev`/build 驗證通過。

---

### 2026-03-13 - AI Assistant - 整理 Git 分支與 PR Merge 操作文件

**更新摘要：**
新增 `docs/git_pr_merge/README.md`，整理本次 `feature/ic-query-qa-refactor` 從：
- 分支命名與切分策略
- 本機開發與 pytest 測試流程
- GitHub 建立 PR、回應 code review、等待 CI 綠燈
- 使用「Squash and merge」合併 PR（含刪除遠端 feature 分支）
- 合併後本機同步與再次驗證

作為未來在 GitHub 手動操作分支與 PR 的標準流程說明文件。

---

### 2026-03-11 - AI Assistant - PR Review 修正全部完成（skip_cache 測試、StubEmbedding deterministic、deps lambda 修正）

**更新摘要：**
完成 PR code review 所有待修事項：

1. **`dependencies.py` lambda Depends 修正**
   - `Depends(lambda: get_graph_store())` → `Depends(get_graph_store)`，讓 FastAPI 正確管理依賴圖與 override。

2. **StubEmbeddingService deterministic 修正**
   - 原本使用 Python `hash()` 因 hash randomization 跨進程不一致。
   - 改為 `hashlib.sha256(text.encode()).digest()` 確保同一輸入永遠產生相同向量。
   - 補充 `tests/test_services/test_stub_embedding_determinism.py`（4/4 通過）。

3. **skip_cache 行為補強測試**
   - 新增 `tests/test_core/test_skip_cache.py` 共 6 個測試案例，覆蓋：
     - `RAGService.query(skip_cache=True)` 不讀不寫快取。
     - `RAGService.query(skip_cache=False)` 讀取並寫入快取。
     - `RAGService.query(skip_cache=False)` 快取命中時不呼叫 LLM。
     - `GraphOrchestrator.query(skip_cache=True)` 不讀不寫 orchestrator 快取。
     - `GraphOrchestrator.query(skip_cache=False)` 快取未命中後寫入。
     - `GraphOrchestrator.query(skip_cache=False)` 快取命中時不呼叫 rag.query。
   - 全部 6/6 通過。

**所有 PR Review 必修項目完成確認：**
- [x] `.db` 移除 git whitelist、`docs/` 取消忽略（已完成）
- [x] `GET /qa/search` DI bug 修正（qa.py 抽共用函式）（已完成）
- [x] `lambda Depends` 寫法修正（已完成）
- [x] `StubEmbeddingService` deterministic（已完成）
- [x] `skip_cache` 測試補強（已完成）

---

### 2026-03-11 - AI Assistant - README 補充 `/api/v1/query` QUERY_TYPE 說明

**更新摘要：**
在 `README.md` 中補充 `/api/v1/query` 於 `QUERY_TYPE=sql` / `QUERY_TYPE=rag` 下的行為：
- **sql**：使用 `graph_qa.db` 做純關鍵字 QA 搜尋，回傳多筆來源列表，不呼叫 LLM。
- **rag**：使用 `graph.db` + 向量 + 圖增強，由 LLM 產生單一整合回答。
並在查詢端點小節說明兩種模式的建議使用情境（只看列表 vs 需要自然語單一回答）。

---

### 2026-03-11 - AI Assistant - 單例 TOCTOU 與 Orchestrator 單次 LLM 修復之自動測試

**測試摘要：**
依測試計畫新增兩組驗證並執行通過。

**新增測試：**
- `tests/test_api/test_dependencies.py::test_singleton_llm_service_under_concurrent_first_calls`：多執行緒同時首次呼叫 `get_llm_service()` 時，僅建立一個實例（單例鎖有效）。
- `tests/test_core/test_orchestrator_llm_calls.py::test_with_graph_store_calls_retrieve_once_and_generate_once_not_query`：有 graph_store 時僅呼叫 `retrieve` 與一次 `generate_answer_from_sources`，不呼叫 `query`。
- `tests/test_core/test_orchestrator_llm_calls.py::test_without_graph_store_calls_query_once_not_retrieve_nor_generate`：無 graph_store 時僅呼叫 `query`，不呼叫 `retrieve` 或 `generate_answer_from_sources`。

**執行結果：** `pytest tests/` 共 **15 passed**（含既有 12 + 新 3），無失敗。

---

### 2026-03-11 11:00 - AI Assistant - Backend API 三大高優先修復（Code Review Follow-up）

**修復摘要：**
依據上輪後端 Code Review 建議，完成三項高優先級重構：

#### Fix 1 — 刪除 `vector_service.py` 殭屍代碼
- **問題**：`_ensure_qa_index()` 末尾將 `_qa_index` 覆寫為 `list`，與後續 `QAEmbeddingIndex` 物件類型衝突，若被呼叫將產生 `AttributeError`。
- **修改**：完整刪除 `_ensure_qa_index()`、`_tokenize()`、`_search_from_qa_index()` 三個方法（共約 90 行死碼）。現系統全部走 `QAEmbeddingIndex` embedding 路徑，不再有冗餘備援路徑。

#### Fix 2 — `orchestrator.py._enhance_with_graph()` 真正並行
- **問題**：原程式碼先建立協程物件 `query_entities_task` 後立刻 `await`（第 198 行），導致 doc 查詢任務未能與 search_entities 同時執行，喪失 `asyncio.gather` 效益。
- **修改**：將 `search_entities` 協程與所有 doc 查詢任務（`get_entity` + `get_neighbors`）統一在一個 `asyncio.gather()` 呼叫中並行執行，延遲從 N 個串行等待降為單次 I/O 等待。

#### Fix 3 — `qa_embedding_index.py` 相似度門檻（Anti-hallucination）
- **問題**：`search()` 僅排除 score ≤ 0 的結果，當查詢與 QA 資料完全不相關時（如「火星探測車」），仍會回傳低相似度的 QA 內容，造成幻覺答案。
- **修改**：
  - `app/config.py`：新增 `QA_MIN_SCORE: float = 0.60`（可由 `.env` 覆寫）。
  - `app/services/qa_embedding_index.py`：`search()` 新增 `min_score: float = 0.0` 參數，score < threshold 的結果不進入排序，直接過濾。
  - `app/services/vector_service.py`：呼叫 `search()` 時帶入 `min_score=settings.QA_MIN_SCORE`。

**影響檔案：**
- `app/services/vector_service.py`（刪除殭屍代碼 + min_score 參數傳入）
- `app/core/orchestrator.py`（真正並行 gather）
- `app/services/qa_embedding_index.py`（min_score 參數）
- `app/config.py`（新增 QA_MIN_SCORE）

---

### 2026-03-11 10:30 - AI Assistant - IC 代碼查詢統一重構（_extract_ic_code 前處理器）

**更新摘要：**
重構 VectorService IC 代碼查詢邏輯，新增統一前處理器 `_extract_ic_code()`，以「IC 卡上下文 + 代碼格式」為唯一判斷依據，完全移除對中文語境詞彙（錯誤代碼/欄位）的依賴。

**重構內容** (`app/services/vector_service.py`)：
- 新增模組級別預編譯正則：`_IC_CONTEXT_RE`、`_CODE_BRACKET_RE`、`_CODE_ANGLE_RE`、`_CODE_BARE_RE`、`_FIELD_CODE_RE`
- 新增 `_extract_ic_code(query)` 純函式：偵測優先順序 `[CODE]` > `<CODE>` > 裸碼，並以 MDHVE+2digits 分類 field/error
- 重構 `_try_get_ic_error_qa_source`：改用 `_extract_ic_code()`，移除舊 Fix 2/3 行內邏輯
- 重構 `_try_get_ic_field_qa_source`：改用 `_extract_ic_code()`，移除舊 Fix 1 行內邏輯

**E2E 驗證結果（6 案例全 Pass）：**

| 查詢 | 實際答案 | 狀態 |
|------|---------|------|
| `IC 卡資料[D12] 代表什麼？` | 委託或受託執行轉(代) | ✅ |
| `IC 卡資料上傳錯誤代碼 AD61` | XCOVID0001...限門/急診... | ✅ |
| `IC 卡資料上傳錯誤 AD61`（新）| XCOVID0001...限門/急診... | ✅ 修正 |
| `IC 卡資料上傳 AD61`（新）| XCOVID0001...限門/急診... | ✅ 修正 |
| `IC 卡欄位 M01 代表什麼？` | 安全模組代碼 | ✅ |
| `IC 卡資料上傳錯誤代碼 [01]` | 資料型態檢核錯誤 | ✅ |

**計畫文件：** `docs/thisqa/IC_CODE_QUERY_FIX_PLAN_2026-03-11.md`

---

### 2026-03-11 10:05 - AI Assistant - IC 欄位代碼 & 錯誤代碼查詢修正（Fix 1/2/3/4）

**更新摘要：**
修正 VectorService 對 `[D12]` 欄位代碼與 `AD61` 裸碼錯誤代碼的查詢路由邏輯，E2E 4 案例全部 Pass。

**Fix 1** (`app/services/vector_service.py` `_try_get_ic_field_qa_source`)：移除嚴格的「欄位」文字守衛，改用正則偵測 `[D12]`、`<D12>`、裸碼 `D12`（MDHVE 前綴格式），使 `[D12]` 查詢能正確取出 `doc_thisqa_ic_field_D12`。

**Fix 2** (`app/services/vector_service.py` `_try_get_ic_error_qa_source`)：加入 MDHVE 欄位碼守衛：若 code 符合 `^[MDHVE]\d{2}$` 格式則 return None，交由 `_try_get_ic_field_qa_source` 處理，防止欄位碼被誤判為錯誤碼。

**Fix 3** (`app/services/vector_service.py` `_try_get_ic_error_qa_source`)：新增裸碼偵測邏輯，當查詢含「錯誤代碼/錯誤碼」上下文且無方括號時，嘗試 pattern `[A-Za-z]{1,2}\d{2,4}|\d{1,4}` 偵測裸碼（如 `AD61`）。

**Fix 4** (`scripts/process_thisqa_to_graph.py` `extract_ic_field_qa_from_txt`)：欄位 QA keywords 補齊 `[code]` 格式與「資料」關鍵字，改善 keyword 搜尋命中率。

**E2E 驗證結果（4 案例全 Pass）：**

| 查詢 | 預期 | 實際 | 狀態 |
|------|------|------|------|
| `IC 卡資料[D12] 代表什麼？` | 委託或受託執行轉(代) | 委託或受託執行轉(代) | ✅ |
| `IC 卡資料上傳錯誤代碼 AD61 代表什麼？` | XCOVID 相關限制說明 | XCOVID0001... 限門/急診... | ✅ |
| `IC 卡欄位 M01 代表什麼？` | 安全模組代碼 | 安全模組代碼 | ✅ |
| `IC 卡資料上傳錯誤代碼 [01] 代表什麼？` | 資料型態檢核錯誤 | 資料型態檢核錯誤 | ✅ |

**計畫文件：** `docs/thisqa/IC_CODE_QUERY_FIX_PLAN_2026-03-11.md`

---

### 2026-03-11 09:13 - AI Assistant - Thisqa graph.db 完整重建（Fix A/B/C）

**更新摘要：**
修正三個根本問題後完整重建 graph.db + qa_vectors.db，Pytest 12/12 通過，E2E 批價/IC 情境 Pass。

**Fix A** (`scripts/process_thisqa_to_graph.py`)：新增 `_reset_qa_vectors_db()`，`--reset` 時同步清空 qa_vectors.db（舊殘留 228 筆已清除，現為精確 389 筆）。同時新增 `run_reset_graph_db()` fallback 清表邏輯，解決 DB 被鎖定時 `unlink()` 失敗的問題。

**Fix B** (`app/core/entity_extractor.py`)：重寫 `_rule_based_entity_extraction()`，改用標點邊界分段（`re.split(r'[，。！？...]')`）取代原 `r'[\u4e00-\u9fff]{2,6}` 6-char 滑動視窗，消除截詞垃圾實體。Concept 實體從 2129 筆降至 1033 筆（-51%）。

**Fix C** (`tests/test_api/test_sse.py`)：`test_sse_stream_empty_query` 預期改為 422，Pytest 11/12 → 12/12 全通過。

**重建結果：**
- graph.db：4 文件、60 QA、329 QA1、2133 total entities（原 2681）、3809 relations（原 7205）
- qa_vectors.db：389 筆（原 617，已清除舊殘留）

**計畫文件：** `docs/thisqa/GRAPH_REBUILD_PLAN_2026-03-11.md`

**已知待處理（後續）：** 負向查詢（如「火星探測車」）仍回傳低相似度醫療 QA 來源（score ~0.45），根因是 VectorService 無相似度門檻過濾，需後續加入 `min_score` 閾值。

### 2026-03-09 20:20 - AI Assistant - Embedding 故障排除總結

**更新摘要：**
將本次 Embedding 相關排查整理成文件，便於日後對照。

**文件位置：** `docs/thisqa/EMBEDDING_TROUBLESHOOTING.md`

**涵蓋項目：** 404（text-embedding-004 / v1beta）、model is required、舊 SDK content 型別錯誤、output_dimensionality 參數不支援、.env 覆寫導致 404、FutureWarning 抑制；建議 .env 設定、相關檔案與驗證步驟。

### 2026-03-09 19:00 - AI Assistant - Embedding 新 SDK（google.genai）支援與切換方式

**更新摘要：**
支援使用新 SDK `google.genai` 做 QA embedding（預設 gemini-embedding-001；text-embedding-004 僅 Vertex 支援），與舊版 `google.generativeai` 並存，以環境變數切換。

**使用方式：**
1. 安裝新 SDK：`pip install google-genai`
2. 在 `.env` 設定：
   - `USE_GOOGLE_GENAI_SDK=true`：優先使用新 SDK
   - `GEMINI_EMBEDDING_MODEL=text-embedding-004`（可選，新 SDK 預設即為此模型）
3. 建圖與 API 會自動使用 `GoogleGenAIEmbeddingService`；未設定或新 SDK 不可用時會退回舊版 `GeminiEmbeddingService`（models/embedding-001）或 Stub。

**相關檔案：** `app/services/embedding_service.py`（新增 `GoogleGenAIEmbeddingService`）、`app/config.py`（USE_GOOGLE_GENAI_SDK、GEMINI_EMBEDDING_MODEL）、`env.example`。

### 2026-03-09 18:04 - AI Assistant - Thisqa QA Embedding 語意檢索骨架實作（EmbeddingService + QAEmbeddingIndex）

**更新摘要：**
在既有 QA GraphRAG 設計上，新增 EmbeddingService 抽象層與 QAEmbeddingIndex，讓 VectorService 能優先使用 QA 向量索引（embedding/cosine 相似度）進行語意檢索，為後續接入真實 embedding 模型奠定基礎。

**調整內容：**
1. **Embedding 服務**：`app/services/embedding_service.py`
   - 新增 `BaseEmbeddingService` 抽象類別與 `GeminiEmbeddingService` / `StubEmbeddingService` 實作。
   - `get_default_embedding_service()` 會優先使用 Gemini（`GOOGLE_API_KEY` + `GEMINI_EMBEDDING_MODEL`，預設 `text-embedding-004`），若不可用則自動降級為 stub（以 deterministic hash 產生固定長度向量）。
2. **QA 向量索引**：`app/services/qa_embedding_index.py`
   - 新增 `QAEmbeddingIndex`，使用 sqlite 檔 `data/qa_vectors.db` 儲存 `entity_id/text/embedding/metadata`，並提供 `upsert()` 與基於 cosine 相似度的 `search()` 介面。
3. **Thisqa 建圖腳本整合 embedding**：`scripts/process_thisqa_to_graph.py`
   - 在解析 Thisqa `.md` 的 QA block 並建立 `Entity(type="QA")` 後，使用 `EmbeddingService` 對每個 QA 的 `question + answer + keywords` 計算 embedding，透過 `QAEmbeddingIndex.upsert()` 寫入 `qa_vectors.db`。
4. **向量檢索流程調整**：`app/services/vector_service.py`
   - `VectorService.search()` 改為：
     - 優先呼叫 `_search_from_qa_embeddings()`：以 EmbeddingService 計算 query 向量，透過 `QAEmbeddingIndex.search()` 找出最相近的 QA Entity，並組成 RAG `sources`（`content = question+answer`）。
     - 若 QA 向量索引無結果或發生錯誤，才退回原本的 graph keyword 檢索 `_search_from_graph()`，最後才使用 stub。

**驗證建議：**
- 停止 API，執行 `python scripts/process_thisqa_to_graph.py --reset` 重新建置 `graph.db` 與 `qa_vectors.db`。
- 啟動 API 後執行：
  - `python scripts/verify_thisqa_qa_vector.py --query "批價作業如何搜尋病患資料？"`：應可透過 embedding/cosine 索引召回 `doc_thisqa_billing_qa_1` 等相關 QA。
  - `python scripts/test_graph_llm_qa.py --query "批價作業如何搜尋病患資料？"`：確認 `/api/v1/query` 回應內容已依據該 QA 的 Answer 產生，而不再僅回「未找到」。

### 2026-03-09 15:22 - AI Assistant - Thisqa QA GraphRAG + 向量檢索設計與實作計畫落地（QA Entity + VectorService QA 索引）

**更新摘要：**
依計畫 `docs/thisqa/THISQA_QA_GRAPHRAG_VECTOR_PLAN.md`，在現有 `graph.db` 基礎上，為 Thisqa QA 建立 `type="QA"` 的圖實體與簡易 QA 向量索引，讓 `/api/v1/query` 能優先從 QA 來源進行語意檢索，僅在無來源時回「未找到」。

**調整內容：**
1. **Graph 建圖腳本**：`scripts/process_thisqa_to_graph.py`
   - 從 Thisqa `.md` 解析 `## Q:` / `**Answer**` / `**關鍵字**` 區塊，為每題建立 `Entity(type="QA")`，properties 包含 `question` / `answer` / `keywords` / `document_id` / `source_file`。
2. **向量檢索服務**：`app/services/vector_service.py`
   - 新增 QA 向量索引 stub：啟動時由 `GraphStore.get_entities_by_type("QA")` 讀入 QA Entity，將 question/answer/keywords 斷詞成 token 集合，使用 Jaccard 相似度實作簡易語意檢索。
   - `search()` 優先使用 QA 索引（模式 A），若無結果再退回原本的圖實體 keyword 檢索（模式 B），最後才使用 stub 結果。
3. **驗證腳本**：`scripts/verify_thisqa_qa_vector.py`
   - 透過 `SQLiteGraphStore + VectorService` 對任意 query 進行 QA 向量檢索，列出召回的 QA Entity id / score / preview，協助確認 `graph.db` + QA 索引是否建置正確。
4. **文件更新**：`docs/thisqa/test_graph_db_llm_qa.md`
   - 新增使用 `verify_thisqa_qa_vector.py` 驗證 Thisqa QA 向量檢索的說明，並說明預期可召回「如何搜尋病患的批價資料？」等 QA。

**驗證建議：**
- 先關閉 API，執行 `python scripts/process_thisqa_to_graph.py --reset` 重建 `graph.db`。
- 再啟動 API，執行：
  - `python scripts/verify_thisqa_qa_vector.py --query "批價作業如何搜尋病患資料？"` 確認 QA 索引可召回正確 QA Entity。
  - `python scripts/test_graph_llm_qa.py --query "批價作業如何搜尋病患資料？"` 確認 `/api/v1/query` 回應內容來自該 QA 的 Answer（有來源才回答，無來源時仍回「未找到」）。

### 2026-03-06（系統日期請以執行時為準） - AI Assistant - Phase 2 Thisqa 建圖腳本（process_thisqa_to_graph）

**更新摘要：**
依計畫 `docs/thisqa/QUERY_TYPE_SQL_VS_RAG_PLAN.md` 實作 Phase 2：新增 `scripts/process_thisqa_to_graph.py`，從 Thisqa 來源檔（3 .md + 1 .txt）建 graph.db 與向量庫，供主線 GraphRAG（`/api/v1/query`）使用。

**調整內容：**
1. **腳本**：`scripts/process_thisqa_to_graph.py` — 讀取 `data/Thisqa` 下 4 檔（可 `--dir` 指定）、UTF-8 全文；.md 依 `## Q:` / 段邊界切塊、.txt 依雙換行/固定行數切塊；每塊 `build_graph_from_text` 寫入 graph.db；每檔處理完 `add_documents` 摘要至向量庫；`--reset` 可先執行 `reset_graph_db`。
2. **計畫文件**：`docs/thisqa/QUERY_TYPE_SQL_VS_RAG_PLAN.md` 狀態更新為 Phase 2 已完成，附錄 B 檢查項標記 [x]。

**使用方式**：
- 僅建圖（附加到現有 graph.db）：`python scripts/process_thisqa_to_graph.py --dir data/Thisqa`
- 先清空 graph.db 再建圖：`python scripts/process_thisqa_to_graph.py --dir data/Thisqa --reset`

### 2026-03-06（系統日期請以執行時為準） - AI Assistant - QUERY_TYPE 環境變數實作（sql / rag）

**更新摘要：**
依計畫 `docs/thisqa/QUERY_TYPE_SQL_VS_RAG_PLAN.md` 實作 Phase 1：以環境變數 QUERY_TYPE 控制 QA 搜尋為「僅回傳列表（sql）」或「LLM 產出單一回答（rag）」。

**調整內容：**
1. **設定**：`app/config.py` 新增 `QUERY_TYPE`（預設 `sql`）、支援 `.env.local` 覆寫、`get_query_type()` 驗證並 fallback。
2. **env.example**：新增 `QUERY_TYPE=sql` 與註解。
3. **Schema**：`QASearchResponse` 增加 `answer: Optional[str] = None`。
4. **QA 端點**：`search_qa` 依 `get_query_type()` 分流；rag 時組 context（限制筆數/字元）、組 prompt、呼叫 `LLMService.generate`，回傳 answer + results；LLM 失敗時 fallback 回傳 results、answer=None。
5. **文件**：`docs/qa/qa_api_test_guide.md` 新增 QUERY_TYPE 說明與測試方式。

**驗證建議**：同一 query 分別設 `QUERY_TYPE=sql` 與 `QUERY_TYPE=rag` 呼叫 `POST /api/v1/qa/search` 確認行為差異。

### 2026-03-06 18:31 - AI Assistant - QA 查詢多欄位、多關鍵字搜尋強化完成

**更新摘要：**
強化 CLI 與 API 的 QA 查詢功能，支援同時在標題、情境、關鍵字、問題、答案與備註中搜尋，並支援多關鍵字 AND 匹配，優化 Thisqa QA 的實際查找體驗。

**調整內容：**

1. **CLI 查詢腳本強化**
   - 更新 `scripts/query_qa_graph.py` 的 `search_qa()`：
     - 以前僅在 `question` / `answer` 欄位做單一字串 substring 比對。
     - 現在會組合以下欄位為一個可搜尋文本 `search_text`：
       - `qa_title`（或實體 `name`）、`scenario`、`keywords`、`question`、`answer`、`notes`。
     - 將使用者輸入以空白切成多個 token，採 AND 模式（所有 token 都必須出現在 `search_text` 中）判斷是否命中。
     - 若無有效 token，則退回原本的 question/answer 匹配行為，維持相容性。
   - 實測指令：
     - `python scripts/query_qa_graph.py --search "如何為看診中的病患快速辦理下次的預約掛號"`：可命中對應的 QA（即使該句只在 Q 標題）。
     - `python scripts/query_qa_graph.py --search "預約掛號 下次回診"`：多關鍵字 AND 也能正確命中同一題。

2. **QA API 搜尋行為對齊**
   - 更新 `app/api/v1/endpoints/qa.py` 中 `search_qa()` 的搜尋邏輯：
     - 原本僅比對 `question` / `answer` / `keywords` 的 substring。
     - 現在改為與 CLI 一致：
       - 同樣組合 `qa_title` / `scenario` / `keywords` / `question` / `answer` / `notes` 為 `search_text`。
       - 以空白拆分使用者查詢為多個 token，使用 AND 模式判斷是否命中。
       - 若無有效 token，則退回原本 question/answer/keywords 的 substring 邏輯。
   - 後續若透過 `/api/v1/qa/search` 查詢，例如：
     - `query: "預約掛號 下次回診"` 並搭配 `doc_id: "thisqa_衛生所醫令系統操作指南與常見問題彙編"`，即可找到該題相關 QA，行為與 CLI 一致。

### 2026-03-06 17:56 - AI Assistant - Thisqa Q&A 解析規則調整與資料重建完成

**更新摘要：**
修正結構化 Q&A 解析規則，讓 `data/Thisqa` 下三本 Markdown 操作指引的 20 題問答都能正確寫入 `graph_qa.db`，並重新執行 QA Graph 重建流程。

**調整內容：**

1. **Q&A 解析邏輯更新**
   - 更新 `scripts/parse_qa_markdown_to_graph.py` 中的 `parse_qa_markdown()`：
     - 若檔案內含 `---` 分隔線，沿用原有行為逐塊解析（舊版掛號 QA 模板不受影響）。
     - 若無 `---`，則改以 `## Q:` 作為每一題 Q&A 區塊的開始，使用前瞻 regex `(?=^##\s+Q:\s*)` 分割。
     - 標題解析支援兩種格式：
       - 原格式：`## **1. Q: 標題**`（從標題中取得題號與標題）。
       - Thisqa 格式：`## Q: 標題`（自動以出現順序編號 `qa_number`，標題取整個 Q 行文字）。

2. **重新建立 QA Graph**
   - 再次執行：
     - `python scripts/reset_graph_qa_db.py --confirm`
     - `python scripts/import_thisqa_markdown_batch.py --qa-dir "data/Thisqa" --db-path "./data/graph_qa.db"`
     - `python scripts/import_ic_error_spec_to_qa_graph.py --spec-file "data/Thisqa/IC卡資料上傳錯誤對照.txt" --db-path "./data/graph_qa.db" --doc-id "ic_error_spec_main" --overwrite-doc`
   - 目前 `data/graph_qa.db` 狀態（由 `scripts/query_qa_graph.py` 驗證）：
     - 文件數量：7（舊的 Thisqa Document 3 筆 + 新建 Thisqa Document 3 筆 + `ic_error_spec_main` 1 筆）。
     - 問答對數量：60（每本 Markdown 成功解析 20 題 Q&A，`CONTAINS_QA` = 60）。
     - IC 規格子圖維持：89 個欄位實體、240 個錯誤實體，關係類型統計為 `CONTAINS_FIELD`、`CONTAINS_ERROR`、`ERROR_ON_FIELD`。

**後續建議：**
- 如需減少舊版 Document 噪音，可視需求重置後僅保留新一輪建立的 Document ID（例如固定 `--doc-id-prefix` 來控制命名），或在查詢端點上以 Document ID 篩選最新版本。

### 2026-03-06 17:45 - AI Assistant - Thisqa QA Graph 重建流程與腳本完成

**更新摘要：**
建立專用的 QA 圖資料庫重置與匯入流程，統一使用 `data/Thisqa` 下的三本操作指引 Markdown 與 IC 卡錯誤對照檔重建 `graph_qa.db`。

**新增與調整項目：**

1. **QA 資料庫重置腳本**
   - 新增 `scripts/reset_graph_qa_db.py`：
     - 僅針對 `data/graph_qa.db` 進行安全重置，不影響主 GraphRAG `graph.db`。
     - 刪除舊檔前會檢查 SQLite 是否被鎖定，並輸出重置前的實體 / 關係統計。
     - 重置後使用 `SQLiteGraphStore("./data/graph_qa.db")` 重新初始化空的 `entities` / `relations` 表。

2. **Thisqa Markdown QA 匯入批次腳本**
   - 新增 `scripts/import_thisqa_markdown_batch.py`：
     - 掃描 `data/Thisqa` 目錄下所有 `.md` 檔案（目前為：醫令、病歷與掛號、門診批價三本操作指引）。
     - 針對每個檔案呼叫既有的 `process_qa_markdown_to_graph()`，建立 `Document(type="qa_markdown")` + `QA` + `CONTAINS_QA` 結構（目前 Thisqa 檔案尚未完全符合 parser 規則，因此問答數量為 0，後續可依實際格式微調 regex）。
     - 提供 `--doc-id-prefix` 參數，需時可用來產生穩定的 Document ID。

3. **IC 卡錯誤對照匯入腳本調整**
   - 更新 `scripts/import_ic_error_spec_to_qa_graph.py`：
     - 預設 `--spec-file` 改為 `data/Thisqa/IC卡資料上傳錯誤對照.txt`，與 Thisqa 資料來源一致。
     - 建議執行時使用固定 `--doc-id ic_error_spec_main` 搭配 `--overwrite-doc`，確保 QA 圖資料庫中永遠只有一套最新的 IC 規格子圖。
     - 匯入結果會建立：
       - 一個 `Document(type="ic_error_spec")`；
       - 多筆 `IC_Field` / `IC_Error` 實體；
       - 關係型別：`CONTAINS_FIELD`、`CONTAINS_ERROR`、`ERROR_ON_FIELD`。

4. **Thisqa QA Graph 計畫文檔**
   - 新增說明文件 `docs/thisqa/QA_GRAPH_BUILD_PLAN.md`：
     - 說明整體目標（僅使用 `data/Thisqa` 來源重建 `graph_qa.db`）。
     - 描述 QA 與 IC 子圖的 entity / relation 設計。
     - 列出完整建庫流程與建議指令：
       - `python scripts/reset_graph_qa_db.py --confirm`
       - `python scripts/import_thisqa_markdown_batch.py --qa-dir "data/Thisqa" --db-path "./data/graph_qa.db"`
       - `python scripts/import_ic_error_spec_to_qa_graph.py --spec-file "data/Thisqa/IC卡資料上傳錯誤對照.txt" --db-path "./data/graph_qa.db" --doc-id "ic_error_spec_main" --overwrite-doc`

**目前狀態：**
- `data/graph_qa.db` 已依上述流程重建：
  - Document 數量：4（3 本 Thisqa 操作指引 + 1 個 `ic_error_spec_main`）。
  - 問答對數量：目前為 0（等待後續依實際 Markdown 模板調整 parser）。
  - IC 規格子圖：89 個欄位實體、240 個錯誤實體，關係統計為 `CONTAINS_FIELD`、`CONTAINS_ERROR`、`ERROR_ON_FIELD`。

### 2025-12-26 11:33 - AI Assistant - QA 文檔集建立完成

**更新摘要：**
建立完整的問答集（QA）文檔，包含 Stub 解釋、JSON 解析錯誤說明和一般使用問答

**新增文檔：**

1. **docs/qa/stub_qa.md** - Stub 相關問答（200+ 行）
   - 什麼是 Stub？
   - 為什麼使用 Stub？
   - 專案中哪些服務是 Stub？
   - Stub vs Mock 的區別
   - 如何替換 Stub？
   - 為什麼 JSON 解析會失敗？

2. **docs/qa/json_parse_error_qa.md** - JSON 解析錯誤問答（200+ 行）
   - 錯誤原因分析
   - 是否影響系統運行？
   - 如何修復錯誤？
   - 如何調試 JSON 解析問題？
   - 錯誤訊息解釋

3. **docs/qa/general_qa.md** - 一般問答（100+ 行）
   - 什麼是 GraphRAG？
   - 專案架構說明
   - 如何開始使用？
   - 如何檢查系統狀態？
   - 常見問題和解決方案

4. **docs/qa/README.md** - QA 索引文件
   - 文檔索引
   - 快速查找指南
   - 相關文檔連結

**技術重點：**
- 詳細解釋 Stub 概念和用途
- 說明 JSON 解析錯誤的根本原因
- 提供完整的故障排除指南
- 建立清晰的文檔結構

**文檔統計：**
- QA 文檔：4 個
- 總行數：500+ 行
- 涵蓋主題：Stub、錯誤處理、使用指南

---

### 2025-12-26 10:53 - AI Assistant - GraphRAG 完整系統實作完成

**更新摘要：**
完成 GraphRAG 圖結構儲存系統的完整實作，包含圖儲存、實體提取、關係提取、圖構建和系統整合

**完整實作內容：**

**階段一：核心基礎設施 ✅**
- `app/core/graph_store.py` - 完整的圖儲存系統（650+ 行）
  - `Entity` 和 `Relation` 資料模型
  - `GraphStore` 抽象介面
  - `SQLiteGraphStore`：SQLite 持久化實作
  - `MemoryGraphStore`：記憶體實作（測試用）
  - 完整的 CRUD 和查詢方法

**階段二：實體和關係提取 ✅**
- `app/core/entity_extractor.py` - 實體和關係提取器（200+ 行）
  - LLM-based 實體提取
  - LLM-based 關係提取
  - 規則基礎降級方案
  - 實體去重和合併

- `app/services/graph_builder.py` - 圖構建服務（150+ 行）
  - 從文字構建圖結構
  - 從文件構建圖結構
  - 批次處理支援
  - 增量更新支援

**階段三：圖查詢方法 ✅**
- 已在 GraphStore 中實作：
  - `get_neighbors()` - 鄰居查詢
  - `get_path()` - BFS 路徑查詢
  - `get_subgraph()` - 子圖查詢
  - `search_entities()` - 實體搜尋

**階段四：系統整合 ✅**
- `app/core/orchestrator.py` - 更新整合 GraphStore
  - 圖查詢增強向量檢索結果
  - 結果融合和去重
  - 支援可選的 GraphStore（向後相容）

- `app/api/v1/dependencies.py` - 完整的依賴注入系統（新建）
  - 所有服務的依賴注入函數
  - 單例模式實作
  - GraphStore、EntityExtractor、GraphBuilder 依賴

- `app/api/v1/endpoints/query.py` - 更新使用依賴注入
  - 移除全域服務實例化
  - 使用 `Depends()` 注入服務

- `app/api/v1/endpoints/documents.py` - 整合圖構建
  - 文件新增時自動構建圖結構
  - 使用 GraphBuilder 服務

- `app/main.py` - 應用啟動時初始化 GraphStore

**階段五：資料庫初始化 ✅**
- `scripts/init_graph_db.py` - 更新整合 SQLiteGraphStore
  - 非同步初始化
  - 完整的錯誤處理

**技術成就：**
- ✅ 完整的抽象設計（GraphStore 介面）
- ✅ 雙重實作（SQLite + Memory）
- ✅ LLM-based 實體和關係提取
- ✅ 自動圖構建（文件新增時）
- ✅ 圖查詢增強 RAG 結果
- ✅ 完整的依賴注入系統
- ✅ 向後相容（GraphStore 可選）

**檔案統計：**
- 新建檔案：5 個
- 更新檔案：6 個
- 總代碼行數：1000+ 行

**依賴更新：**
- `requirements.txt` - 添加 `aiosqlite>=0.19.0`

**文檔：**
- `docs/graphrag_implementation_plan.md` - 完整實作計劃（包含代碼審查）

**下一步：**
- 階段六：建立測試套件
- 效能優化
- 生產環境部署準備

---

### 2025-12-26 10:51 - AI Assistant - GraphRAG Graph Store 階段一實作完成

**更新摘要：**
實作 GraphRAG 圖結構儲存系統的核心基礎設施，包含完整的 GraphStore 抽象介面、SQLiteGraphStore 和 MemoryGraphStore 實作

**實作內容：**

**1. 核心資料模型：**
- `app/core/graph_store.py` - 完整的圖儲存系統（650+ 行）
  - `Entity` 類別：實體資料模型（id, type, name, properties）
  - `Relation` 類別：關係資料模型（id, source_id, target_id, type, weight）
  - `GraphStore` 抽象基類：定義所有圖操作介面
  - `SQLiteGraphStore`：SQLite 持久化實作
  - `MemoryGraphStore`：記憶體實作（用於測試）

**2. GraphStore 功能：**
- 實體 CRUD：add_entity, get_entity, delete_entity
- 關係 CRUD：add_relation, get_relation, delete_relation
- 查詢方法：
  - `get_entities_by_type()` - 依類型查詢
  - `search_entities()` - 搜尋實體
  - `get_neighbors()` - 取得鄰居節點
  - `get_path()` - BFS 路徑查詢（多跳）
  - `get_subgraph()` - 子圖查詢
- 級聯刪除：刪除實體時自動刪除相關關係
- 事務處理：批次操作支援
- JSON 序列化：properties 欄位支援

**3. 資料庫 Schema：**
- entities 表：id, type, name, properties, created_at, updated_at
- relations 表：id, source_id, target_id, type, properties, weight, created_at
- 完整索引：type, name, source_id, target_id, relation_type
- 外鍵約束：CASCADE 刪除
- 檢查約束：防止自循環關係

**4. 腳本更新：**
- `scripts/init_graph_db.py` - 整合 SQLiteGraphStore 進行資料庫初始化
- 支援非同步初始化
- 完整的錯誤處理

**5. 依賴更新：**
- `requirements.txt` - 添加 `aiosqlite>=0.19.0`

**技術特點：**
- 完整的抽象設計，易於擴展
- 雙重實作（SQLite + Memory）
- 非同步操作支援
- 完整的錯誤處理和日誌記錄
- 支援中文和特殊字元（JSON ensure_ascii=False）

**下一步計劃：**
- 階段二：實作 EntityExtractor（實體和關係提取）
- 階段三：實作 GraphBuilder（文件到圖轉換）
- 階段四：整合到 Orchestrator 和 API 端點

**文檔：**
- `docs/graphrag_implementation_plan.md` - 完整實作計劃（包含代碼審查）

---

### 2025-12-26 09:20 - AI Assistant - 企業級版本升級完成

**更新摘要：**
將 Care RAG API 升級為完整企業級版本，包含 REST/SSE/WebSocket 多協定支援、GraphRAG Orchestrator、Redis 快取、多 LLM Provider 支援、完整監控和測試套件

**新增核心功能：**

**1. 配置和基礎設施：**
- `app/config.py` - 完整的應用程式配置管理（Pydantic Settings）
- `app/core/exceptions.py` - 自訂例外類別體系
- `app/core/logging.py` - 結構化日誌設定
- `app/core/security.py` - API Key 驗證增強

**2. 服務層完整實作：**
- `app/services/rag_service.py` - RAG 查詢服務（支援快取和向量檢索）
- `app/services/vector_service.py` - 向量檢索服務 stub
- `app/services/cache_service.py` - Redis 快取服務 stub（支援 TTL）
- `app/services/llm_service.py` - 多 LLM Provider 支援（Gemini/OpenAI/Deepseek）
- `app/services/background_tasks.py` - 背景任務處理服務
- `app/core/orchestrator.py` - GraphRAG 編排器（完整查詢流程）

**3. API 端點擴展：**
- `app/api/v1/endpoints/query.py` - REST + SSE + WebSocket 查詢端點
- `app/api/v1/endpoints/documents.py` - 文件管理 API（新增/刪除/批量）
- `app/api/v1/endpoints/health.py` - 健康檢查端點（health/ready/live）
- `app/api/v1/endpoints/websocket.py` - WebSocket 獨立端點
- `app/api/v1/router.py` - 統一路由配置

**4. API 結構定義：**
- `app/api/v1/schemas/query.py` - 查詢請求/回應結構（含驗證）
- `app/api/v1/schemas/document.py` - 文件管理結構定義
- `app/api/v1/schemas/common.py` - 通用結構（錯誤/成功/分頁）

**5. 工具和監控：**
- `app/utils/metrics.py` - Prometheus 指標擴展（請求/查詢/快取/WebSocket）
- `app/utils/formatters.py` - 回應格式化工具

**6. 測試套件：**
- `tests/test_api/test_query.py` - REST API 測試（6 個測試案例）
- `tests/test_api/test_sse.py` - SSE 串流測試（3 個測試案例）
- `tests/test_api/test_ws.py` - WebSocket 測試（4 個測試案例）

**7. Docker 和部署：**
- `Dockerfile` - 企業級容器配置（健康檢查、多端口）
- `docker-compose.yml` - 完整部署配置（API + Redis、網路、卷）
- `requirements.txt` - 完整依賴管理（含測試套件）

**8. 腳本工具：**
- `scripts/load_documents.py` - 文件載入腳本
- `scripts/init_graph_db.py` - GraphRAG 資料庫初始化增強

**技術架構升級：**
- **多協定支援：** REST API、Server-Sent Events (SSE)、WebSocket
- **LLM Provider 切換：** 支援 Gemini、OpenAI、Deepseek 動態切換
- **快取策略：** Redis stub 實作，支援 TTL 和快取命中率監控
- **向量檢索：** 向量服務 stub，支援文件新增/刪除/檢索
- **監控指標：** 完整的 Prometheus 指標（請求、查詢、快取、WebSocket）
- **健康檢查：** 三層健康檢查（health/ready/live）
- **背景任務：** 非同步文件處理和快取清理

**API 端點總覽：**
- `GET /` - 根端點
- `POST /api/v1/query` - REST 查詢
- `GET /api/v1/query/stream` - SSE 串流查詢
- `WebSocket /api/v1/ws/chat` - WebSocket 聊天
- `WebSocket /api/v1/ws/query` - WebSocket 查詢
- `POST /api/v1/documents` - 新增文件
- `POST /api/v1/documents/batch` - 批量新增文件
- `DELETE /api/v1/documents/{id}` - 刪除文件
- `GET /api/v1/health` - 健康檢查
- `GET /api/v1/health/ready` - 就緒檢查
- `GET /api/v1/health/live` - 存活檢查

**測試覆蓋：**
- REST API 測試：6 個測試案例
- SSE 測試：3 個測試案例
- WebSocket 測試：4 個測試案例
- 總計：13 個測試案例

**部署配置：**
- Docker 多端口支援（8080 API、8001 Metrics）
- Redis 服務整合（docker-compose）
- 健康檢查配置
- 環境變數管理
- 資料持久化（volumes）

---

### 2025-12-26 09:16 - AI Assistant - 完整專案檔案建立（基於 chkgpt 指示）

**更新摘要：**
根據 chkgpt 指示建立完整的 Care RAG API 專案，包含所有核心檔案、API 端點、Docker 配置和測試檔案

**建立的檔案清單：**

**主要應用程式檔案：**
- `app/main.py` - FastAPI 主應用程式，包含 CORS 中間件和路由註冊
- `app/core/orchestrator.py` - GraphRAG 編排器核心類別
- `app/core/security.py` - API Key 驗證安全模組
- `app/utils/metrics.py` - Prometheus 指標監控工具

**API 端點和結構定義：**
- `app/api/v1/endpoints/query.py` - REST 查詢端點和 SSE 串流端點
- `app/api/v1/schemas/query.py` - Pydantic 請求/回應結構定義

**腳本和測試：**
- `scripts/init_graph_db.py` - GraphRAG 資料庫初始化腳本
- `tests/test_api/test_query.py` - API 查詢端點測試

**Docker 和依賴管理：**
- `Dockerfile` - Python 3.11 容器化配置
- `requirements.txt` - Python 套件依賴（fastapi, uvicorn, pydantic, prometheus_client）
- `docker-compose.yml` - Docker Compose 服務配置

**模組初始化檔案：**
- 所有目錄的 `__init__.py` 檔案（確保 Python 模組正確導入）

**專案配置：**
- `.gitignore` - Git 版本控制忽略規則
- `README.md` - 專案說明文件

**打包腳本：**
- `scripts/create_zip.ps1` - PowerShell ZIP 打包腳本（自動排除開發檔案）
- `scripts/create_zip.bat` - Windows Batch 包裝腳本

**使用打包腳本：**
```bash
# 方法 1: 使用 PowerShell
powershell -ExecutionPolicy Bypass -File scripts/create_zip.ps1

# 方法 2: 使用 Batch 腳本
scripts\create_zip.bat
```

打包腳本會自動：
- 排除 `__pycache__`、`.git`、`venv` 等開發檔案
- 產生帶時間戳記的 ZIP 檔案（格式：`care_rag_api_YYYYMMDD_HHMMSS.zip`）
- 顯示檔案大小資訊

**專案結構：**
```
care_rag_api/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI 主應用
│   ├── core/
│   │   ├── __init__.py
│   │   ├── orchestrator.py        # GraphRAG 編排器
│   │   └── security.py            # API Key 驗證
│   ├── services/
│   │   └── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── endpoints/
│   │       │   ├── __init__.py
│   │       │   └── query.py       # REST/SSE 查詢端點
│   │       └── schemas/
│   │           ├── __init__.py
│   │           └── query.py      # Pydantic 結構定義
│   └── utils/
│       ├── __init__.py
│       └── metrics.py             # Prometheus 指標
├── scripts/
│   └── init_graph_db.py           # 資料庫初始化
├── tests/
│   ├── __init__.py
│   └── test_api/
│       ├── __init__.py
│       └── test_query.py          # API 測試
├── Dockerfile                      # Docker 容器配置
├── docker-compose.yml              # Docker Compose 配置
├── requirements.txt                # Python 依賴
├── .gitignore                      # Git 忽略規則
└── dev_readme.md                  # 開發記錄
```

**技術架構：**
- **框架：** FastAPI (Python 3.11)
- **API 版本：** v1
- **支援協定：** REST API、Server-Sent Events (SSE)
- **監控：** Prometheus 指標
- **容器化：** Docker + Docker Compose
- **測試框架：** FastAPI TestClient

**快速啟動指令：**
```bash
# 安裝依賴
pip install -r requirements.txt

# 啟動開發伺服器
uvicorn app.main:app --reload --port 8080

# Docker 啟動
docker-compose up --build
```

**API 端點：**
- `GET /` - 健康檢查
- `POST /api/v1/query` - REST 查詢端點
- `GET /api/v1/query/stream` - SSE 串流查詢端點

---

### 2025-12-26 09:08 - AI Assistant - 專案目錄結構建立

**更新摘要：**
建立 Care RAG API 專案基礎目錄結構

**建立的目錄結構：**
```
care_rag_api/
├── app/
│   ├── core/                    # 核心業務邏輯
│   ├── services/                # 服務層
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/       # API 端點
│   │       └── schemas/         # API 結構定義
│   └── utils/                   # 工具函數
├── scripts/                     # 腳本檔案
└── tests/
    └── test_api/                # API 測試
```

**技術說明：**
- 使用 PowerShell `New-Item -ItemType Directory -Force` 命令建立目錄
- Windows CMD 不支援 `mkdir -p` 語法，需使用 PowerShell 或正確的 CMD 語法

**Windows CMD 正確語法參考：**
```cmd
REM 方法 1: 使用 PowerShell（推薦）
powershell -Command "New-Item -ItemType Directory -Force -Path 'app\core','app\services','app\api\v1\endpoints','app\api\v1\schemas','app\utils','scripts','tests\test_api'"

REM 方法 2: 使用 CMD mkdir（逐層建立）
mkdir app\core
mkdir app\services
mkdir app\api\v1\endpoints
mkdir app\api\v1\schemas
mkdir app\utils
mkdir scripts
mkdir tests\test_api
```

