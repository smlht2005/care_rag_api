# LINE@ 設定與 Cloud Run 疑難排解（對照表）

更新時間：2026-04-01 11:31  
作者：AI Assistant  
修改摘要：彙整 LINE 官方帳號／Developers 設定、雙 Cloud Run 服務與常見故障現象、根因與處置，供實測與維運對照

---

## 文件用途

本文件與 [lineAt-cloudrun-sop.md](./lineAt-cloudrun-sop.md) 搭配使用：SOP 描述「正確架構與部署步驟」，本文件聚焦 **症狀 → 可能根因 → 檢查與修復**，涵蓋對話中實際踩過的坑。

---

## 1. 架構速覽（兩個 Cloud Run 服務）

| 角色 | 服務名稱 | 對外用途 | 認證 |
|------|----------|----------|------|
| Service A | `care-rag-line-proxy` | LINE Webhook 入口、`LINE Reply API` 出口 | Webhook 可設為不需登入；內部呼叫 B 用 OIDC + API Key |
| Service B | `care-rag-api` | `POST /api/v1/query`（RAG 主 API） | 需已驗證身分（例如 Cloud Run invoker）+ `X-API-Key` |

資料流：`LINE → Service A → Service B → Service A → LINE Reply API → 使用者`

---

## 2. LINE 端設定（必查）

### 2.1 LINE Developers（Messaging API）

| 項目 | 建議值 | 若設錯會怎樣 |
|------|--------|----------------|
| Webhook URL | `https://<care-rag-line-proxy 主機>/api/v1/webhook/line/query` | Verify 失敗 → LINE 不送事件或顯示錯誤 |
| Use webhook | **Enabled** | 關閉則後端收不到訊息 |
| Channel secret | 與 Cloud Secret `LINE_CHANNEL_SECRET`、本機 `.env` **一致** | 簽章驗證失敗 → 401 / `Invalid LINE signature` |

### 2.2 LINE Official Account Manager（官方帳號後台）

| 項目 | 建議值 | 若設錯會怎樣 |
|------|--------|----------------|
| **Auto-reply messages** | **Disabled** | 使用者看到固定罐頭回覆，誤以為 RAG 沒跑或被我們的 Reply 蓋掉 |
| **Greeting messages** | **Disabled** | 重開聊天室或特定情境仍出現官方招呼文，**干擾判斷**我們的 Reply 是否成功 |

實務上：兩者都應關閉，才能用聊天室內容單純驗證 **Webhook → A → B → Reply** 路徑。

### 2.3 Channel access token（long-lived）

- 來源：Messaging API 頁面的 **Channel access token (long-lived)**。
- 在 Console **Reissue** 後，**舊 token 立即失效**，必須同步：
  - 本機 `.env` 的 `LINE_CHANNEL_ACCESS_TOKEN`
  - Secret Manager 新版本
  - Service A 仍掛載該 secret 的 `:latest`（或指定版本）

---

## 3. Google Cloud 端（必查）

### 3.1 專案與帳號

- 部署與查 log 時 **`gcloud config set project`** 必須與實際資源一致（本專案實務為 **`gen-lang-client-0567547134`**）。
- 若 `--project` 指到無權限或錯誤專案，會出現 `PERMISSION_DENIED` / `CONSUMER_INVALID`，**不是程式 bug**。

### 3.2 Service A（`care-rag-line-proxy`）執行身分與 Secret

Runtime Service Account（例：`441535054378-compute@developer.gserviceaccount.com`）至少需要：

- `roles/secretmanager.secretAccessor`（針對掛載的每個 secret，或專案層級）
- 能對 Service B 發起已驗證呼叫（Service B 端需將該 SA 設為 `roles/run.invoker` 或等效政策）

常見錯誤：

| 現象 | 可能根因 | 處置 |
|------|----------|------|
| Revision **not ready**；日誌提到 `Permission denied on secret ... LINE_CHANNEL_ACCESS_TOKEN` | SA 對該 secret 無 `secretAccessor` | 對該 secret 綁定 SA + `roles/secretmanager.secretAccessor` |
| Reply 仍失敗但 revision 已就緒 | Token 錯誤、Reissue 未同步、或見下節「換行」 | 更新 secret、確認環境變數 |

### 3.3 `gcloud run deploy --update-env-vars`（PowerShell）

- 多個 `KEY=VAL` 必須 **整段放在同一個引號內**（例如單引號包住整串逗號分隔），否則可能被解析成 **單一錯誤變數**，導致 `LINE_PROXY_QUERY_ENDPOINT` / `LINE_PROXY_TARGET_AUDIENCE` **在執行時缺失** → 500 或無法轉呼 B。

### 3.4 Secret Manager 內容尾端換行

- 若 `LINE_CHANNEL_ACCESS_TOKEN` 從檔案或管線寫入時帶入 `\r\n`，HTTP 標頭可能變成非法值（例如 `Illegal header value` / `LocalProtocolError`）。
- **程式已對 token 做 `.strip()`**；仍建議建立 secret 時盡量用不含尾端換行的輸入。

### 3.5 Service B（`care-rag-api`）流量與環境變數

| 現象 | 可能根因 | 處置 |
|------|----------|------|
| 已 `update` 環境變數（如 `QA_MIN_SCORE`）但行為不變 | 新 revision **0% 流量**，舊 revision 仍全量 | `gcloud run services update-traffic care-rag-api --to-latest`（或手動把流量切到新 revision） |
| 本機／舊 UI「未找到」，LINE 卻有答案 | 除流量外，曾存在 **僅 QA embedding 路徑套用 `QA_MIN_SCORE`**，graph 旁路低分仍進 LLM；已在 Orchestrator 合併後 **統一過濾**（見程式變更與 `dev_readme.md`） | 部署含該修正的映像後再驗 |

---

## 4. 端到端檢查清單（建議順序）

1. **LINE**：Developers Webhook Verify 成功；Official Account 關閉 Auto-reply 與 Greeting。
2. **Secret**：`LINE_CHANNEL_SECRET`、`LINE_PROXY_X_API_KEY`、`LINE_CHANNEL_ACCESS_TOKEN` 與後台一致；SA 有 accessor。
3. **Service A 環境**：`LINE_PROXY_QUERY_ENDPOINT`、`LINE_PROXY_TARGET_AUDIENCE`、`LINE_REPLY_ENABLED` 正確；無因錯誤 `update-env-vars` 語法造成變數遺失。
4. **Service B**：`API_KEY` / `X-API-Key` 與 A 一致；需要時檢查 **流量是否在新 revision**。
5. **Log**：`gcloud run services logs read care-rag-line-proxy --region asia-east1 --limit 80`  
   搜尋 `LINE webhook processed`、`query_status`、`reply_token_present`、`reply_status`、`reply_detail`。

---

## 5. 與 Postman 測試 Service B 的差異

- Postman 手動貼的 **ID token** 會過期，需自行重簽。
- **正式 LINE 流量**：Service A 每次呼叫 B 前由 `CloudRunAuthService` **重新簽發 ID token**，不需人工輪換（見 SOP 第 5 節）。

---

## 6. 相關檔案

| 檔案 | 說明 |
|------|------|
| `app/api/v1/endpoints/webhook.py` | Webhook、簽章、轉呼 B、LINE Reply |
| `app/services/cloud_run_auth_service.py` | Service A → B 的 ID token |
| `app/config.py` | `LINE_*`、`QA_MIN_SCORE` 等 |
| [lineAt-cloudrun-sop.md](./lineAt-cloudrun-sop.md) | 完整 SOP、Token 說明、驗證指令 |

---

本文件依實際整合與除錯經驗整理；若 LINE 或 GCP 介面改版，請以官方文件為準並同步更新本頁。
