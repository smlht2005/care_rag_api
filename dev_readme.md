# Care RAG API 開發記錄

## 更新歷史

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

