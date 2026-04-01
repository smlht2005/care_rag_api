更新時間：2026-04-01 15:20
作者：AI Assistant
修改摘要：補充 LINE@（Service A：care-rag-line-proxy）整合說明與文件入口（SOP + Trouble Shooting），並摘要 S2S/Reply/QA_MIN_SCORE 相關新增功能
（Windows cmd 時間戳參考）2026/04/01 15:20:15.44

---

更新時間：2026-04-01 15:16
作者：AI Assistant
修改摘要：新增 Windows Server robocopy 部署（SOP + 一鍵 .bat）文件入口
（Windows cmd 時間戳參考）2026/04/01 15:16:55.01

---

更新時間：2026-03-11
作者：AI Assistant
修改摘要：補充 `/api/v1/query` 在 QUERY_TYPE=sql/rag 下的行為說明，說明與 QA Graph 端點的關係

# Care RAG API

企業級 RAG (Retrieval-Augmented Generation) API - 支援 REST、SSE 和 WebSocket 協定

## 專案簡介

Care RAG API 是一個基於 FastAPI 的企業級 RAG 系統，提供 GraphRAG 查詢功能，支援多種 API 協定和即時串流回應。

## 功能特色

- 🚀 **多協定支援** - REST API、Server-Sent Events (SSE)、WebSocket
- 🤖 **多 LLM Provider** - 支援 Gemini、OpenAI、Deepseek 動態切換
- 🔍 **GraphRAG Orchestrator** - 完整的 RAG 查詢編排流程
- 💾 **快取策略** - Redis 快取支援（stub），提升查詢效能
- 🔎 **向量檢索** - 向量服務 stub，支援文件管理和檢索
- 📊 **Prometheus 指標** - 完整的監控指標（請求/查詢/快取/WebSocket）
- 🔐 **API Key 驗證** - 安全認證機制
- 📄 **文件管理** - 文件新增、刪除、批量處理 API
- 📚 **知識庫管理** - 知識攝取、查詢、來源管理
- 🏥 **健康檢查** - 三層健康檢查（health/ready/live）
- 🔧 **管理端點** - 系統統計、圖資料庫統計、快取管理
- 🐳 **Docker 支援** - 完整容器化部署（API + Redis）
- 🪟 **Windows Server 部署** - 以 robocopy 同步原始碼（SOP + 一鍵 `.bat`）
- 🧪 **測試覆蓋** - 13 個測試案例（REST/SSE/WebSocket）
- 💬 **LINE@ 整合（Cloud Run 雙服務）** - Service A（`care-rag-line-proxy`）接 Webhook、轉呼叫 Service B（`care-rag-api`）並可回覆 LINE Reply API

## 快速開始

### 前置需求

- Python 3.11+
- pip
- Docker (選用)

### 安裝步驟

1. **安裝依賴**
```bash
pip install -r requirements.txt
```

2. **啟動開發伺服器**
```bash
uvicorn app.main:app --reload --port 8000
```

**注意**：預設端口為 8000，配置文件中的 `PORT` 也設定為 8000，保持一致。

3. **使用 Docker 啟動**
```bash
docker-compose up --build
```

### Windows Server 部署（robocopy 同步原始碼）

- SOP：`docs/deploy/robocopy-to-win-server-sop.md`
- 一鍵部署腳本：`docs/deploy/cmd/deploy_to_172.31.6.123.bat`

### LINE@（Cloud Run Service A/B）整合與疑難排解

- 架構：LINE Webhook → **Service A** `care-rag-line-proxy` → **Service B** `care-rag-api` → LINE Reply API
- 重點能力：
  - **Webhook 簽章驗證**：`X-Line-Signature` + `LINE_CHANNEL_SECRET`
  - **Service A → B S2S**：Cloud Run **OIDC ID token**（`CloudRunAuthService`，含快取）+ `X-API-Key`
  - **LINE Reply API**：用 `replyToken` 回覆到聊天室（`LINE_CHANNEL_ACCESS_TOKEN`；程式會 `.strip()` 避免 Secret 尾端換行造成 header 非法）
  - **QA_MIN_SCORE 一致化**：在 Orchestrator 最終合併 sources 後統一套用門檻，避免 graph 路徑低分來源繞過門檻進 LLM
- 文件：
  - SOP：`docs/lineAt/lineAt-cloudrun-sop.md`
  - Trouble Shooting：`docs/lineAt/lineAt-line-settings-cloud-troubleshooting.md`

### API 端點

**查詢端點：**
- `POST /api/v1/query` - REST 查詢端點  
  - 行為由環境變數 `QUERY_TYPE` 控制：
    - `QUERY_TYPE=sql`：執行 **關鍵字 QA 搜尋**（使用 `graph_qa.db`），回傳多筆來源列表（`sources`），`answer` 為簡單摘要或第一筆結果，**不呼叫 LLM**。
    - `QUERY_TYPE=rag`：執行 **GraphRAG + LLM**（使用 `graph.db` + 向量 + 圖增強），在 `sources` 基礎上由 LLM 產生單一整合回答。
  - 建議用法：
    - 只需要「找出哪幾筆 QA 匹配關鍵字」時用 `sql`。
    - 需要「自然語問答 + 單一回答」時用 `rag`。
- `GET /api/v1/query/stream` - SSE 串流查詢端點
- `WebSocket /api/v1/ws/chat` - WebSocket 聊天端點
- `WebSocket /api/v1/ws/query` - WebSocket 查詢端點

**文件管理：**
- `POST /api/v1/documents` - 新增單一文件
- `POST /api/v1/documents/batch` - 批量新增文件
- `DELETE /api/v1/documents/{id}` - 刪除文件

**知識庫：**
- `POST /api/v1/knowledge/query` - 知識庫查詢（包含圖結構資訊）
- `GET /api/v1/knowledge/sources` - 取得知識來源列表
- `POST /api/v1/knowledge/ingest` - 知識庫攝取

**管理端點（需要 API Key）：**
- `GET /api/v1/admin/stats` - 系統統計資訊
- `GET /api/v1/admin/graph/stats` - 圖資料庫統計資訊
- `POST /api/v1/admin/cache/clear` - 清除快取

**健康檢查：**
- `GET /` - 根端點
- `GET /api/v1/health` - 健康檢查
- `GET /api/v1/health/ready` - 就緒檢查
- `GET /api/v1/health/live` - 存活檢查

### 範例請求

**REST 查詢：**
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -d '{"query": "你的問題", "top_k": 3}'
```

**SSE 串流查詢：**
```bash
curl -N "http://localhost:8000/api/v1/query/stream?query=你的問題" \
  -H "X-API-Key: test-api-key"
```

**WebSocket 查詢：**
```python
import websockets
import json

async def websocket_query():
    uri = "ws://localhost:8000/api/v1/ws/query"
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({"query": "你的問題"}))
        response = await websocket.recv()
        print(json.loads(response))
```

**指定 LLM Provider：**
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -d '{"query": "你的問題", "provider": "openai", "top_k": 5}'
```

**知識庫查詢（包含圖結構）：**
```bash
curl -X POST "http://localhost:8000/api/v1/knowledge/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "什麼是長期照護2.0？",
    "top_k": 3,
    "include_graph": true
  }'
```

**取得知識來源列表：**
```bash
curl -X GET "http://localhost:8000/api/v1/knowledge/sources"
```

**知識庫攝取：**
```bash
curl -X POST "http://localhost:8000/api/v1/knowledge/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "這是知識內容...",
    "source": "api",
    "metadata": {"title": "知識範例"}
  }'
```

**系統統計（需要 API Key）：**
```bash
curl -X GET "http://localhost:8000/api/v1/admin/stats" \
  -H "X-API-Key: test-api-key"
```

**完整 API 查詢範例**：
- 📖 [API 查詢範例文檔](docs/api_query_examples.md) - 包含 12+ 個 REST API 範例、SSE 串流、WebSocket 查詢範例
- 📬 [Postman 集合](docs/postman/README.md) - Postman 使用指南和完整測試集合

## 專案結構

```
care_rag_api/
├── app/
│   ├── main.py                    # FastAPI 主應用
│   ├── config.py                  # 應用程式配置
│   ├── core/                      # 核心業務邏輯
│   │   ├── orchestrator.py       # GraphRAG 編排器
│   │   ├── security.py            # API Key 驗證
│   │   ├── exceptions.py         # 自訂例外類別
│   │   └── logging.py             # 日誌設定
│   ├── services/                  # 服務層
│   │   ├── rag_service.py         # RAG 查詢服務
│   │   ├── vector_service.py      # 向量檢索服務
│   │   ├── cache_service.py       # Redis 快取服務
│   │   ├── llm_service.py         # LLM 服務（多 Provider）
│   │   └── background_tasks.py   # 背景任務服務
│   ├── api/v1/                    # API v1
│   │   ├── router.py              # 路由配置
│   │   ├── endpoints/             # API 端點
│   │   │   ├── query.py           # 查詢端點（REST/SSE/WS）
│   │   │   ├── documents.py       # 文件管理
│   │   │   ├── health.py          # 健康檢查
│   │   │   ├── knowledge.py       # 知識庫端點
│   │   │   ├── admin.py           # 管理端點
│   │   │   ├── webhook.py         # Webhook 端點
│   │   │   └── websocket.py       # WebSocket 端點
│   │   └── schemas/               # 結構定義
│   │       ├── query.py           # 查詢結構
│   │       ├── document.py        # 文件結構
│   │       └── common.py          # 通用結構
│   └── utils/                     # 工具函數
│       ├── metrics.py             # Prometheus 指標
│       └── formatters.py          # 格式化工具
├── scripts/                       # 腳本檔案
│   ├── init_graph_db.py           # GraphRAG 資料庫初始化
│   ├── load_documents.py          # 文件載入腳本
│   ├── process_pdf_to_graph.py   # PDF 處理和圖構建腳本
│   ├── reset_graph_db.py          # 重置資料庫腳本
│   ├── check_db.py                # 資料庫檢查腳本
│   ├── test_health_api.ps1        # 健康檢查 API 測試腳本（PowerShell）
│   └── test_health_api.sh         # 健康檢查 API 測試腳本（Bash）
├── tests/                         # 測試檔案
│   └── test_api/                  # API 測試
│       ├── test_query.py          # REST API 測試
│       ├── test_sse.py            # SSE 測試
│       └── test_ws.py             # WebSocket 測試
├── Dockerfile                     # Docker 配置
├── docker-compose.yml             # Docker Compose 配置
└── requirements.txt               # Python 依賴
```

## PDF 處理和 GraphRAG 構建

### 處理 PDF 文件並構建圖結構

**基本使用**：
```bash
# 處理預設 PDF 文件
python scripts/process_pdf_to_graph.py

# 處理指定 PDF 文件
python scripts/process_pdf_to_graph.py "data/example/your_file.pdf"

# 指定文件 ID
python scripts/process_pdf_to_graph.py "data/example/your_file.pdf" --doc-id "my_document_id"

# 使用覆蓋模式（清理相同來源的現有數據）
python scripts/process_pdf_to_graph.py "data/example/your_file.pdf" --overwrite
```

**選項說明**：
- `pdf_path`: PDF 文件路徑（預設: `data/example/1051219長期照護2.0核定本.pdf`）
- `--doc-id`: 指定文件 ID（預設: 自動生成）
- `--chunk-size`: 文字分塊大小，單位字元（預設: 2000）
- `--overwrite`: 如果檢測到相同來源的 PDF，先刪除現有數據再處理（避免重複數據）

### 重置 GraphRAG 資料庫

當資料庫中有重複或髒數據時，可以使用重置腳本清理所有數據：

```bash
# 帶確認提示（推薦第一次使用）
python scripts/reset_graph_db.py

# 自動確認（跳過提示）
python scripts/reset_graph_db.py --confirm
```

**重置後重新導入 PDF**：
```bash
# 1. 重置資料庫
python scripts/reset_graph_db.py --confirm

# 2. 重新導入 PDF
python scripts/process_pdf_to_graph.py "data/example/your_file.pdf"

# 3. 驗證數據（可選）
python scripts/check_db.py
```

**注意事項**：
- 重置會刪除所有現有數據，建議先備份 `data/graph.db`
- 確保沒有其他進程正在使用資料庫
- 重置只清理圖資料庫，向量資料庫需要單獨處理

## QA Graph（graph_qa.db）與 IC 卡錯誤規格整合

- **單一 DB，多子圖**：`graph_qa.db` 使用與 `graph.db` 相同的 `entities` / `relations` schema，內部可以同時存放多種知識子圖：
  - 一般 QA 知識庫：`Document(type=\"qa_markdown\")` + `QA` + `CONTAINS_QA`
  - 診所操作手冊等 QA/知識點（由 PDF 解析腳本建立）
- **IC 卡錯誤規格子圖**（本專案擴充設計）：
  - 新增一個 `Document(type=\"ic_error_spec\")`，代表 `data/hisqa/IC卡資料上傳錯誤對照.txt`
  - 新增兩種實體型別：
    - `IC_Field`：欄位代碼（例如 `M07`、`D06`），保存欄位中文說明與區段資訊
    - `IC_Error`：錯誤代碼（例如 `01`、`AD69`、`Y016`），保存完整中文錯誤訊息
  - 新增關係型別：
    - `CONTAINS_FIELD`：`Document -> IC_Field`，表示文件中定義了哪些欄位
    - `CONTAINS_ERROR`：`Document -> IC_Error`，表示文件中定義了哪些錯誤代碼
    - `ERROR_ON_FIELD`：`IC_Error -> IC_Field`，表示某錯誤代碼與哪些欄位有邏輯關聯（由錯誤說明文字中提到的 `Mxx` / `Dxx` 等欄位解析而來）
- **與現有 QA API 的關係**：
  - 現有 `/api/v1/qa/*` 端點仍只針對 `Document(type=\"qa_markdown\")` 與 `QA` 兩種實體做查詢，不會受到 IC 卡錯誤規格子圖影響。
  - IC 卡錯誤規格資料與其他 QA 資料共用同一顆 `data/graph_qa.db`，透過 `SQLiteGraphStore` 存取；未來如需對 IC 錯誤提供專用 API，可在 `app/api/v1/endpoints/qa.py` 新增額外端點，針對 `IC_Error` / `IC_Field` 以及 `ERROR_ON_FIELD` 關係進行查詢。
- **建庫腳本規劃**：
  - `scripts/parse_qa_markdown_to_graph.py`：匯入 Markdown QA 到 `graph_qa.db`
  - `scripts/import_qa_markdown_batch.py`：批次匯入多個 QA Markdown 檔案
  - `scripts/parse_clinic_manual_pdfs_to_qa_graph.py`：從 PDF 抽取 QA 與知識點匯入 `graph_qa.db`
  - `scripts/import_ic_error_spec_to_qa_graph.py`：從 `data/hisqa/IC卡資料上傳錯誤對照.txt` 匯入 IC 卡欄位與錯誤代碼，建立上述實體與關係（本計畫新增）

## 開發

### 執行測試

```bash
pytest tests/
```

### 監控指標

Prometheus 指標服務預設運行於 `http://localhost:8001/metrics`

**可用指標：**
- `care_rag_requests_total` - 總請求數（按方法/端點/狀態）
- `care_rag_request_latency_seconds` - 請求延遲（按方法/端點）
- `care_rag_queries_total` - 總查詢數（按 Provider/狀態）
- `care_rag_query_latency_seconds` - 查詢延遲（按 Provider）
- `care_rag_cache_hits_total` - 快取命中數
- `care_rag_cache_misses_total` - 快取未命中數
- `care_rag_websocket_connections` - WebSocket 連線數
- `care_rag_documents_total` - 文件總數

### 環境變數配置

建立 `.env` 檔案（選用）：
```env
DEBUG=false
LLM_PROVIDER=gemini
REDIS_HOST=localhost
REDIS_PORT=6379
METRICS_PORT=8001
API_KEY=your-api-key-here
```

## 授權

本專案遵循企業內部授權規範。

## API Key 設置

### 快速設置

**預設值**：`test-api-key`

**設置方法：**

1. **環境變數（推薦）**：
   ```bash
   # Windows PowerShell
   $env:API_KEY="your-api-key-here"
   
   # Linux/Mac
   export API_KEY="your-api-key-here"
   ```

2. **`.env` 文件**：
   ```env
   API_KEY=your-api-key-here
   ```

3. **Postman 集合變數**：
   - 打開 Postman 集合
   - 編輯 `api_key` 變數
   - 設置為你的 API Key

### 哪些端點需要 API Key？

**需要 API Key：**
- `GET /api/v1/admin/stats` - 系統統計
- `GET /api/v1/admin/graph/stats` - 圖資料庫統計
- `POST /api/v1/admin/cache/clear` - 清除快取

**不需要 API Key：**
- 所有查詢端點（`/api/v1/query`）
- 所有知識庫端點（`/api/v1/knowledge`）
- 所有文件管理端點（`/api/v1/documents`）
- 所有健康檢查端點（`/api/v1/health`）

**詳細指南**：請參考 [API Key 設置指南](docs/api_key_setup_guide.md)

## 常見問題

### PDF 處理相關

**Q: 重複處理相同 PDF 會產生重複數據嗎？**

A: 預設情況下會追加數據（因為每次生成新的 UUID）。使用 `--overwrite` 選項可以自動清理相同來源的現有數據。

**Q: 如何清理所有數據重新開始？**

A: 使用重置腳本：`python scripts/reset_graph_db.py --confirm`，然後重新導入 PDF。

### API Key 相關

**Q: 如何設置 API Key？**

A: 請參考 [API Key 設置指南](docs/api_key_setup_guide.md) 獲取完整的設置說明。

**Q: 哪些端點需要 API Key？**

A: 只有管理端點（Admin）需要 API Key，查詢和文件管理端點不需要。詳見 [API Key 設置指南](docs/api_key_setup_guide.md)。

**Q: 資料庫文件在哪裡？**

A: 預設位置為 `./data/graph.db`，可在 `app/config.py` 中修改 `GRAPH_DB_PATH`。

**Q: 為什麼 `/api/v1/knowledge/sources` 返回空列表？**

A: 這表示還沒有處理任何 PDF 文件或攝取知識。請先使用 `scripts/process_pdf_to_graph.py` 處理 PDF 文件，或使用 `/api/v1/knowledge/ingest` 端點攝取知識內容。

**Q: 如何查看已處理的文件來源？**

A: 使用 `GET /api/v1/knowledge/sources` 端點，它會從 GraphStore 中獲取所有 Document 類型的實體作為知識來源。

更多詳細說明請參閱 [QA 文檔](docs/qa/README.md)

## 更新記錄

詳細的開發記錄請參閱 [dev_readme.md](dev_readme.md)

