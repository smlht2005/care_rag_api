---
name: Cloud Run 部署 Care RAG API
source: c:\Users\hungtao.liu\.cursor\plans\cloud_run_部署_care_rag_api_5de4bd2e.plan.md
saved_at: 2026-03-26 00:00
---

# Google Cloud Run 部署 Care RAG API 計畫（存檔版）

## 現況摘要（程式庫已具備）

- **應用入口**：`uvicorn app.main:app --host 0.0.0.0`。
- **既有容器**：`Dockerfile` 已存在；本計畫 **API 埠統一 8002**。部署時 Cloud Run 設定 `--port 8002`，uvicorn 監聽 `PORT`（fallback `8002`）。
- **設定載入**：`app/config.py` 使用 `load_dotenv()` + `BaseSettings`；正式環境以 Cloud Run 注入的環境變數/Secret 為主（不依賴映像內 `.env`）。
- **健康檢查**：`/api/v1/health`。
- **資料（你已決定）**：映像內需包含 3 個 DB：`./data/graph_qa.db`、`./data/graph.db`、`./data/qa_vectors.db`。

## 建議執行步驟（摘要版）

### 1) GCP 專案與 API

- 專案：`gen-lang-client-0567547134`
- 區域：`asia-east1`
- 啟用：Cloud Run / Artifact Registry / Cloud Build / Secret Manager
- 你已決定：**GEMINI/LLM 金鑰使用 Secret Manager**

### 2) Artifact Registry

- 在 `asia-east1` 建 Docker repository（例如 `care-rag-api`）

### 3) Build & Push

- 用 Cloud Build 將映像 push 到 Artifact Registry
- 你已決定：新增 `.dockerignore` 排除 `.env`、`.git`、`__pycache__`

### 4) Dockerfile（你已決定採用策略 A）

- 在 Dockerfile 加入：
  - `COPY ./data/graph_qa.db ./data/graph.db ./data/qa_vectors.db /app/data/`
- API 埠：`EXPOSE 8002`，uvicorn 用 `--port ${PORT:-8002}`

### 5) Cloud Run 環境變數 / Secret

- 非敏感設定：用 `--set-env-vars`
- 敏感金鑰：用 Secret Manager + `--update-secrets`

### 6) Cloud Run 部署（你已決定：IAM only，不開放匿名）

- `gcloud run deploy ... --port 8002`
- 不使用 `--allow-unauthenticated`
- 授權呼叫端 `roles/run.invoker`

### 7) 驗收

- `GET https://<service-url>/api/v1/health/`（注意尾斜線；本專案在 Cloud Run 上實測此路徑可避免 307 redirect）
- IAM only（不開放匿名）：呼叫需帶 `Authorization: Bearer <ID_TOKEN>`（且呼叫身分需具備 `roles/run.invoker`）
- 進一步用實際查詢端點驗證（含 Graph/LLM 路徑）
- `POST https://<service-url>/api/v1/query`
  - Header：`X-API-Key: test-api-key`

```json
{
  "query": "門診批價作業中，如何查詢某病患當日掛號紀錄？",
  "top_k": 5,
  "skip_cache": true
}
```