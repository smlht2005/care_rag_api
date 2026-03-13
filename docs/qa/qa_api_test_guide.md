# QA API 測試指南

**更新時間**：2026-03-06  
**作者**：AI Assistant  
**修改摘要**：新增 QUERY_TYPE（sql / rag）說明與測試方式

**更新時間**：2026-01-13 15:20  
**作者**：AI Assistant  
**修改摘要**：更新標頭註解日期

**更新時間**：2025-12-30 11:30  
**目的**：說明如何使用 QA 查詢 API 和 Postman 測試

## QUERY_TYPE 查詢模式

QA 搜尋端點（POST/GET `/api/v1/qa/search`）的行為由環境變數 **QUERY_TYPE** 控制：

- **QUERY_TYPE=sql**（預設）：僅回傳檢索到的 QA 列表（`query`、`total`、`results`），不呼叫 LLM。`answer` 欄位為 `null`。
- **QUERY_TYPE=rag**：以檢索結果為 context 呼叫 LLM 產出單一回答，回傳 `answer` + `results`（sources）。若無檢索結果則 `answer` 為空字串。需設定 `GOOGLE_API_KEY`（或對應 LLM）方能使用。

**設定方式**：在專案根目錄的 `.env` 或 `.env.local` 中設定：
```
QUERY_TYPE=sql
# 或
QUERY_TYPE=rag
```
`.env.local` 若存在會覆寫 `.env` 的同名變數。

**建議驗證**：同一 query 分別設 `QUERY_TYPE=sql` 與 `QUERY_TYPE=rag` 各呼叫一次 `POST /api/v1/qa/search`，確認 sql 回傳僅 results（answer 為 null）、rag 回傳 answer + results。

## API 端點

### 1. 取得所有 QA 文件列表

**端點**：`GET /api/v1/qa/documents`

**說明**：取得所有已匯入的 QA 文件列表

**請求範例**：
```bash
curl http://localhost:8000/api/v1/qa/documents
```

**回應範例**：
```json
{
  "total": 2,
  "documents": [
    {
      "id": "掛號qa",
      "name": "掛號QA.md",
      "type": "qa_markdown",
      "qa_count": 20,
      "source": "C:\\...\\掛號QA.md"
    },
    {
      "id": "tamis_衛材與供應中心管理系統操作指南15qa",
      "name": "TAMIS 衛材與供應中心管理系統操作指南15qa.md",
      "type": "qa_markdown",
      "qa_count": 15,
      "source": "C:\\...\\TAMIS 衛材與供應中心管理系統操作指南15qa.md"
    }
  ]
}
```

### 2. 搜尋 QA（POST）

**端點**：`POST /api/v1/qa/search`

**說明**：搜尋問答對，支援關鍵詞匹配

**請求範例**：
```bash
curl -X POST http://localhost:8000/api/v1/qa/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "F1",
    "limit": 10
  }'
```

**請求參數**：
- `query` (string, required): 搜尋關鍵詞
- `limit` (int, optional): 返回結果數量（預設: 10，最大: 50）
- `doc_id` (string, optional): 限制搜尋特定文件 ID

**回應欄位**：
- `query`、`total`、`results`：與原本相同。
- `answer`（optional）：QUERY_TYPE=rag 時為 LLM 產出的單一回答；sql 或 LLM 失敗 fallback 時為 `null`。

**回應範例（QUERY_TYPE=sql）**：
```json
{
  "query": "F1",
  "total": 2,
  "results": [
    {
      "id": "掛號qa_qa_2",
      "qa_number": 2,
      "question": "第一次看病的病人要怎麼幫他掛號？",
      "answer": "使用 F1 功能鍵進行初診登錄...",
      "scenario": "當病患第一次來到醫院看診...",
      "keywords": ["初診", "F1", "IC卡", "建檔"],
      "steps": ["按下鍵盤「F1.初診」鍵...", "..."],
      "notes": "若不使用 IC 卡，可按 ESC 離開...",
      "metadata": {
        "product": "TAMIS 醫療資訊整合系統",
        "category": "門診掛號",
        "user_role": "櫃檯人員",
        "source": "05-0(GUI)掛號管理系統簡易操作手冊(102_07).pdf",
        "last_updated": "2025-12-02"
      }
    }
  ]
}
```

### 3. 搜尋 QA（GET）

**端點**：`GET /api/v1/qa/search`

**說明**：使用 GET 方法搜尋 QA（方便測試）

**請求範例**：
```bash
curl "http://localhost:8000/api/v1/qa/search?query=F1&limit=5"
```

**查詢參數**：
- `query` (string, required): 搜尋關鍵詞
- `limit` (int, optional): 返回結果數量（預設: 10，最大: 50）
- `doc_id` (string, optional): 限制搜尋特定文件 ID

### 4. 根據文件 ID 取得所有 QA

**端點**：`POST /api/v1/qa/by-document`

**說明**：取得指定文件的所有 QA

**請求範例**：
```bash
curl -X POST http://localhost:8000/api/v1/qa/by-document \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "掛號qa",
    "limit": 20
  }'
```

**請求參數**：
- `doc_id` (string, required): 文件 ID
- `limit` (int, optional): 返回結果數量（預設: 100，最大: 200）

## Postman 測試

### 匯入 Postman 集合

1. 開啟 Postman
2. 點選 "Import"
3. 選擇 `docs/postman/Care_RAG_API.postman_collection.json`
4. 選擇 `docs/postman/Care_RAG_API.postman_environment.json`（可選）

### 設定環境變數

在 Postman 環境中設定：
- `base_url`: `http://localhost:8000`
- `api_key`: `test-api-key`（如果需要）

### 測試步驟

1. **測試健康檢查**
   - 執行 `Health Check > Health Check`
   - 應該返回 `{"success": true, ...}`

2. **取得 QA 文件列表**
   - 執行 `QA > Get QA Documents`
   - 應該返回所有 QA 文件列表

3. **搜尋 QA**
   - 執行 `QA > Search QA - GET` 或 `QA > Search QA - POST`
   - 修改 `query` 參數測試不同關鍵詞
   - 例如：`F1`, `掛號`, `衛材`, `初診`

4. **根據文件取得 QA**
   - 先從 "Get QA Documents" 取得文件 ID
   - 執行 `QA > Get QA by Document`
   - 設定 `doc_id` 參數

## 啟動 API

### 方法 1：使用 uvicorn（開發模式）

```bash
py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 方法 2：使用 Python 腳本

```bash
python -m app.main
```

### 方法 3：使用 Docker

```bash
docker-compose up
```

## 測試範例

### PowerShell 測試

```powershell
# 1. 取得文件列表
Invoke-WebRequest -Uri http://localhost:8000/api/v1/qa/documents -UseBasicParsing

# 2. 搜尋 QA
$body = @{query='F1';limit=3} | ConvertTo-Json
Invoke-WebRequest -Uri http://localhost:8000/api/v1/qa/search -Method POST -Body $body -ContentType 'application/json' -UseBasicParsing

# 3. 根據文件取得 QA
$body = @{doc_id='掛號qa';limit=20} | ConvertTo-Json
Invoke-WebRequest -Uri http://localhost:8000/api/v1/qa/by-document -Method POST -Body $body -ContentType 'application/json' -UseBasicParsing
```

### curl 測試

```bash
# 1. 取得文件列表
curl http://localhost:8000/api/v1/qa/documents

# 2. 搜尋 QA
curl -X POST http://localhost:8000/api/v1/qa/search \
  -H "Content-Type: application/json" \
  -d '{"query":"F1","limit":3}'

# 3. GET 方法搜尋
curl "http://localhost:8000/api/v1/qa/search?query=F1&limit=3"
```

## 常見問題

### Q: API 返回 404 錯誤

**A:** 檢查：
1. API 是否已啟動（檢查 `http://localhost:8000/api/v1/health`）
2. 路徑是否正確（應該是 `/api/v1/qa/...`）
3. QA 資料庫是否存在（`data/graph_qa.db`）

### Q: 找不到 QA 資料

**A:** 確認：
1. 已執行匯入腳本：`py scripts/import_qa_markdown_batch.py`
2. 資料庫中有 QA 資料：`py scripts/test_qa_import.py --list-docs`

### Q: 搜尋結果為空

**A:** 可能原因：
1. 關鍵詞不匹配（嘗試使用英文關鍵詞，如 "F1", "IC"）
2. 關鍵詞不在問題、答案或關鍵字中
3. 嘗試使用部分匹配（例如 "掛" 而不是 "掛號"）

## API 文檔

啟動 API 後，可以訪問：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 相關文件

- `scripts/import_qa_markdown_batch.py` - QA 匯入腳本
- `scripts/test_qa_import.py` - QA 測試腳本
- `docs/qa/qa_import_test_guide.md` - QA 匯入測試指南
