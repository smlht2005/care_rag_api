# Code Review 待修項目清單

**更新時間：** 2026-03-11  
**摘要：** 後端 API（`app/`）Code Review 後尚未修復的項目；高優先三項（殭屍代碼、假並行、QA_MIN_SCORE）已完成。

---

## 已修復（本輪）

| 項目 | 檔案 | 狀態 |
|------|------|------|
| 殭屍代碼 _ensure_qa_index / _tokenize / _search_from_qa_index | `app/services/vector_service.py` | ✅ 已刪除 |
| _enhance_with_graph 假並行 | `app/core/orchestrator.py` | ✅ 改為 asyncio.gather 真正並行 |
| QA 相似度無門檻導致負向查詢誤報 | `app/services/qa_embedding_index.py` + `app/config.py` | ✅ 新增 QA_MIN_SCORE |
| 單例 TOCTOU 競態 | `app/api/v1/dependencies.py` | ✅ 加 threading.Lock double-checked locking |
| 圖增強後重複呼叫 LLM | `app/core/orchestrator.py` + `app/services/rag_service.py` | ✅ 有圖時改 retrieve + 合併後只呼叫一次 LLM |

---

## 待修項目（依優先級）

### 中優先（安全／穩定性）

#### 1. CORS 預設允許所有來源（Production 不安全）

| 項目 | 內容 |
|------|------|
| **檔案** | `app/config.py` |
| **位置** | 約第 59 行 `CORS_ORIGINS: list = ["*"]` |
| **問題** | Production 環境下 `["*"]` 允許任意網域，有 CSRF／資訊洩漏風險。 |
| **建議** | 預設改為空列表或單一開發用 origin（如 `["http://localhost:3000"]`），Production 由 `.env` 設定實際前端網域，例如：`CORS_ORIGINS=["https://your-frontend.com"]`。 |
| **使用處** | `app/main.py` 約第 88 行：`allow_origins=settings.CORS_ORIGINS` |

---

#### 2. API_KEY 預設硬編碼

| 項目 | 內容 |
|------|------|
| **檔案** | `app/config.py` |
| **位置** | 約第 66 行 `API_KEY: Optional[str] = "test-api-key"` |
| **問題** | 未設定環境變數時使用固定值，若部署時忘記改會造成安全缺口。 |
| **建議** | 改為 `API_KEY: Optional[str] = None`，並在 `app/core/security.py` 驗證：若 `settings.API_KEY` 為 None 或空，則一律拒絕（或僅在 DEBUG 時允許無 key）。 |
| **使用處** | `app/core/security.py` 約第 19、26 行與 `settings.API_KEY` 比對。 |

---

#### 3. 依賴注入單例建立無鎖（多執行緒競態）✅ 已修復 2026-03-11

| 項目 | 內容 |
|------|------|
| **檔案** | `app/api/v1/dependencies.py` |
| **修復** | 新增 `_init_lock = threading.Lock()`，各 `get_*` 內改為 double-checked locking：`if _xxx is None: with _init_lock: if _xxx is None: _xxx = ...`，消除 TOCTOU 競態。 |

---

#### 4. LLM 呼叫無逾時保護

| 項目 | 內容 |
|------|------|
| **檔案** | `app/services/rag_service.py`、`app/services/llm_service.py` |
| **位置** | `rag_service.py` 約第 155、188 行 `await self.llm.generate(prompt, max_tokens=2000)` |
| **問題** | 外部 API 延遲或掛起時，請求會一直等，導致 worker 卡住、無法釋放。 |
| **建議** | 在 `config.py` 新增 `LLM_REQUEST_TIMEOUT: float = 30.0`，在 `rag_service.py` 以 `asyncio.wait_for(self.llm.generate(...), timeout=settings.LLM_REQUEST_TIMEOUT)` 包裝；若 LLM 底層支援 timeout 參數，可改在 `llm_service.py` 傳入。 |

---

### 低優先（文件／一致性）

#### 5. Docker 與 config 端口不一致

| 項目 | 內容 |
|------|------|
| **檔案** | `docker-compose.yml`、`app/config.py` |
| **說明** | `config.py` 預設 `PORT: int = 8000`，Docker 對外為 `8080:8080`，若容器內未設 `PORT=8080`，健康檢查會打錯端口。 |
| **建議** | 在 `docker-compose.yml` 的 `api` 服務 `environment` 中明確加上 `PORT=8080`，與 `ports: "8080:8080"` 一致；或統一改為 8000。 |
| **備註** | Prometheus `8001` 已在 compose 中暴露，無需再改。 |

---

#### 6. 錯誤響應格式不統一（code_review_2nd.md）

| 項目 | 內容 |
|------|------|
| **說明** | 不同端點回傳錯誤時格式可能不一致（有的純字串，有的 JSON）。 |
| **建議** | 使用 FastAPI 的 `exception_handler` 或統一依賴 `HTTPException` + 同一 Pydantic schema，讓所有 4xx/5xx 回傳同一結構（如 `{ "detail": "...", "code": "..." }`）。 |

---

#### 7. 缺少請求 ID（可選）

| 項目 | 內容 |
|------|------|
| **說明** | 日誌中難以追蹤「同一請求」的整條呼叫鏈。 |
| **建議** | 在中間件為每個請求產生 `X-Request-ID`（或使用 `uuid.uuid4()`），寫入 response header 並在 logger 的 extra 中傳遞，方便排查。 |

---

## 參考

- **已落實的 Code Review 修復**：`dev_readme.md` —「Backend API 三大高優先修復」
- **第二次代碼審查（多數已修）**：`docs/code_review_2nd.md` — Phase 1/2 已標為完成

若要依此清單逐項實作，可從 **1（CORS）、2（API_KEY）** 開始，再處理 **3（鎖）、4（LLM timeout）**。
