---
name: API Query Examples Documentation
overview: 創建完整的 API 查詢範例文檔，包含 REST、SSE、WebSocket 三種方式的實際查詢範例，基於已創建的醫療照護資料庫
todos:
  - id: create_api_examples_doc
    content: 創建 docs/api_query_examples.md 文檔，包含完整的 API 查詢範例
    status: completed
  - id: add_rest_examples
    content: 添加 REST API 查詢範例（10+ 個基於醫療照護主題的實際查詢）
    status: completed
  - id: add_sse_examples
    content: 添加 SSE 串流查詢範例（3+ 個範例）
    status: completed
  - id: add_websocket_examples
    content: 添加 WebSocket 查詢範例（2+ 個範例）
    status: completed
  - id: add_error_handling
    content: 添加錯誤處理和故障排除範例
    status: completed
  - id: update_readme
    content: 更新 README.md，添加查詢範例文檔的連結
    status: completed
  - id: create_postman_collection
    content: 創建 Postman 集合文件（JSON 格式），包含所有 API 端點的測試請求，使用端口 8000
    status: completed
---

# API 查詢範例文檔計劃

## 目標

創建 `docs/api_query_examples.md` 文檔，提供完整的 API 查詢範例，基於已成功創建的 GraphDB（1273 實體、2227 關係）。

## 執行狀態

✅ **已完成** - 2025-12-26 17:35

所有計劃任務已完成：
- ✅ API 查詢範例文檔已創建（12+ REST 範例、3 SSE 範例、2 WebSocket 範例）
- ✅ Postman 集合已創建（包含所有 API 端點）
- ✅ Postman 環境變數文件已創建
- ✅ Postman 使用指南已創建
- ✅ README.md 已更新（添加連結並修正端口號）

## 文檔內容結構

### 1. 基礎資訊

- API 基礎 URL: `http://localhost:8000`（注意：實際運行端口為 8000，而非配置文件的 8080）
- 資料庫狀態：1273 實體、2227 關係
- 實體類型：Concept (887)、Organization (108)、Document (85)、Location (85)、Person (68)、Policy (40)

### 2. REST API 查詢範例

基於 `app/api/v1/endpoints/query.py` 的 `POST /api/v1/query` 端點

**範例查詢主題**（基於醫療照護 PDF）：
- 長期照護相關問題
- 組織和政策查詢
- 概念和實體關係查詢
- 地點和人員查詢

**請求格式**：

```json
{
  "query": "查詢問題",
  "top_k": 3,
  "provider": "gemini",
  "max_tokens": 2000,
  "temperature": 0.7
}
```

### 3. SSE 串流查詢範例

基於 `GET /api/v1/query/stream` 端點**使用場景**：
- 即時查詢結果串流
- 長時間查詢的進度顯示

### 4. WebSocket 查詢範例

基於 `WebSocket /api/v1/ws/chat` 和 `/api/v1/ws/query` 端點

**使用場景**：
- 即時對話
- 雙向通訊

### 5. 其他有用端點

- `GET /api/v1/health` - 健康檢查
- `GET /api/v1/admin/graph/stats` - 圖資料庫統計
- `GET /api/v1/admin/stats` - 系統統計

## 實作步驟

1. **創建文檔文件** `docs/api_query_examples.md`
   - 包含完整的 curl 命令範例
   - 包含 Python 請求範例
   - 包含 JavaScript/TypeScript 範例（可選）

2. **基於資料庫內容的實際查詢範例**：
   - 查詢 "長期照護" 相關內容
   - 查詢 "World Health Organization" 相關資訊
   - 查詢政策和組織關係
   - 查詢概念和實體關係

3. **包含錯誤處理範例**：
   - 無效查詢
   - 服務未啟動
   - 參數錯誤

4. **更新 README.md**：
   - 在 "API 端點" 章節添加連結到查詢範例文檔

5. **創建 Postman 集合** `docs/postman/Care_RAG_API.postman_collection.json`：
   - 包含所有 REST API 端點的請求
   - 包含環境變數設定（base_url: http://localhost:8000）
   - 包含範例請求體和參數
   - 包含健康檢查、查詢、文件管理、管理端點等所有端點
   - 使用 Postman Collection v2.1 格式
   - 包含請求範例和預設值

## 技術細節

- **重要**：所有範例中的 API 基礎 URL 使用 `http://localhost:8000`（實際運行端口），而非配置文件的 8080
- 使用 `curl` 命令展示 REST API
- 使用 Python `requests` 庫展示程式化查詢
- 使用 Python `websockets` 庫展示 WebSocket 查詢
- 所有範例都基於實際的資料庫內容
- **Postman 集合**：
  - 使用 Postman Collection v2.1 格式
  - 包含環境變數（base_url）
  - 每個請求包含範例請求體和參數
  - 組織成邏輯資料夾結構
  - 包含請求描述和範例回應

## 預期輸出

1. **API 查詢範例文檔** (`docs/api_query_examples.md`)：
   - 10+ 個 REST API 查詢範例
   - 3+ 個 SSE 串流查詢範例
   - 2+ 個 WebSocket 查詢範例
   - 錯誤處理範例

2. **Postman 集合** (`docs/postman/Care_RAG_API.postman_collection.json`)：
   - 完整的 Postman Collection v2.1 格式
   - 包含所有 API 端點的預設請求
   - 包含環境變數設定（base_url: http://localhost:8000）
   - 可直接導入 Postman 使用
   - 包含範例請求體和參數
   - 組織良好的資料夾結構（Query、Documents、Health、Admin 等）

