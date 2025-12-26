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
- 🏥 **健康檢查** - 三層健康檢查（health/ready/live）
- 🐳 **Docker 支援** - 完整容器化部署（API + Redis）
- 🧪 **測試覆蓋** - 13 個測試案例（REST/SSE/WebSocket）

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

**注意**：預設端口為 8000（實際運行端口），而非配置文件的 8080。

3. **使用 Docker 啟動**
```bash
docker-compose up --build
```

### API 端點

**查詢端點：**
- `POST /api/v1/query` - REST 查詢端點
- `GET /api/v1/query/stream` - SSE 串流查詢端點
- `WebSocket /api/v1/ws/chat` - WebSocket 聊天端點
- `WebSocket /api/v1/ws/query` - WebSocket 查詢端點

**文件管理：**
- `POST /api/v1/documents` - 新增單一文件
- `POST /api/v1/documents/batch` - 批量新增文件
- `DELETE /api/v1/documents/{id}` - 刪除文件

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

**完整 API 查詢範例**：
- 📖 [API 查詢範例文檔](docs/api_query_examples.md) - 包含 12+ 個 REST API 範例、SSE 串流、WebSocket 查詢範例
- 📬 [Postman 集合](docs/postman/Care_RAG_API.postman_collection.json) - 可直接導入 Postman 使用的完整測試集合

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
│   └── reset_graph_db.py          # 重置資料庫腳本
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

更多詳細說明請參閱 [QA 文檔](docs/qa/README.md)

## 更新記錄

詳細的開發記錄請參閱 [dev_readme.md](dev_readme.md)

