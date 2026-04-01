### Care RAG LINE@ 後端整合與 Cloud Run SOP

更新時間：2026-04-01 11:31  
作者：AI Assistant  
修改摘要：於文件開頭增加與疑難排解文件的交叉連結

更新時間：2026-03-31 15:00  
作者：AI Assistant  
修改摘要：首次整理 LINE@ → Service A（care-rag-line-proxy）→ Service B（care-rag-api）完整實作與部署/驗證流程

**相關文件**：[LINE@ 設定與 Cloud Run 疑難排解](./lineAt-line-settings-cloud-troubleshooting.md)（症狀／根因／檢查清單）

---

### 1. 架構總覽

- **Service B：`care-rag-api`（既有）**
  - 仍為主 API，不變更對外行為。
  - 提供 `POST /api/v1/query`，回傳 `QueryResponse{ answer, sources, query, provider }`。
- **Service A：`care-rag-line-proxy`（新建）**
  - Image 與 `care-rag-api` 相同，但以獨立 Cloud Run 服務部署。
  - 入口：`POST /api/v1/webhook/line/query`，允許 LINE Webhook 無認證呼叫。
  - 負責：
    - 驗證 LINE 簽章（`X-Line-Signature` + `LINE_CHANNEL_SECRET`）。
    - 從 LINE webhook 事件抽出第一則文字訊息與 `replyToken`。
    - 以 **OIDC ID Token + X-API-Key** 呼叫 Service B `/api/v1/query`。
    - 依查詢結果（`answer`）呼叫 **LINE Reply API** 回覆到聊天室。

資料流：  
`LINE 使用者 → (Webhook) LINE → Service A (care-rag-line-proxy) → Service B (care-rag-api) → Service A → LINE Reply API → 使用者`

---

### 2. 程式實作重點

#### 2.1 設定（`app/config.py`）

- 新增 LINE Webhook/Reply 設定：
  - `LINE_CHANNEL_SECRET`：LINE Developers「Messaging API」頁面中的 Channel secret。
  - `LINE_WEBHOOK_REQUIRE_SIGNATURE`：預設 `True`，強制驗簽。
  - `LINE_PROXY_QUERY_ENDPOINT`：Service B `/api/v1/query` URL。
  - `LINE_PROXY_TARGET_AUDIENCE`：Service B Cloud Run URL（做 ID token audience）。
  - `LINE_PROXY_INVOKER_SERVICE_ACCOUNT`：Runtime SA（此案為 `441535054378-compute@developer.gserviceaccount.com`）。
  - `LINE_PROXY_X_API_KEY`：轉呼叫 B 時附加的 `X-API-Key`（若空則回退 `API_KEY`）。
  - `LINE_PROXY_TOP_K` / `LINE_PROXY_TIMEOUT_SEC`：查詢筆數與 timeout。
  - `LINE_REPLY_ENABLED`：是否啟用 LINE Reply API。
  - `LINE_CHANNEL_ACCESS_TOKEN`：Channel access token（long-lived）。
  - `LINE_WEBHOOK_TEST_BASE_URL`：僅本機測試腳本使用。

#### 2.2 Cloud Run ID Token 工具（`app/services/cloud_run_auth_service.py`）

- `CloudRunAuthService.get_id_token(target_audience, invoker_service_account=None)`：
  - 若有 `invoker_service_account`：使用 `impersonated_credentials` 以來源 ADC 身份模擬，再簽發 ID token。
  - 否則直接依當前 ADC/metadata 取得 ID token。
  - 用於 Service A → Service B 呼叫時的 `Authorization: Bearer <id_token>`。

#### 2.3 Webhook Schema（`app/api/v1/schemas/webhook.py`）

- `LineWebhookMessage`：`{ type, id?, text? }`
- `LineWebhookEvent`：`{ type, replyToken?, message?, source?, timestamp? }`
- `LineWebhookRequest`：`{ events: List[LineWebhookEvent] }`
- `LineWebhookProxyResponse`：
  - `status, event_id, forwarded, query_status, query, answer, detail`
  - `reply_status, reply_detail`：記錄 Reply API 呼叫結果。

#### 2.4 Webhook 端點（`app/api/v1/endpoints/webhook.py`）

- `_verify_line_signature(raw_body, channel_secret, line_signature)`：
  - 使用 `HMAC-SHA256` + base64 比對 `X-Line-Signature`。
- `_extract_first_text_query(LineWebhookRequest)`：
  - 遍歷 events，找第一個 `type=="message"` 且 `message.type=="text"`，回傳 `(text, replyToken)`。
- `_line_reply(reply_token, text)`：
  - 若 `LINE_REPLY_ENABLED` 為 False、或缺 `LINE_CHANNEL_ACCESS_TOKEN` / `replyToken`，則直接回 `(None, reason)`。
  - 對 token `.strip()` 後組出：
    - `Authorization: Bearer <access_token>`
    - `POST https://api.line.me/v2/bot/message/reply`  
      body：`{ "replyToken": ..., "messages":[{"type":"text","text":...}] }`
  - 成功回 `(status_code, None)`，失敗回 `(status_code, response_text)`；例外回 `(0, "reply exception: ...")`。
- `POST /api/v1/webhook/line/query`：
  1. 產生 `event_id`，讀 raw body 並以 Pydantic 驗證 JSON。
  2. 若啟用簽章驗證：檢查 `LINE_CHANNEL_SECRET` 是否存在；失敗回 401 `Invalid LINE signature`。
  3. 透過 `_extract_first_text_query` 取得 `(query_text, reply_token)`；若無文字則 200 + `forwarded=False`。
  4. 檢查 `LINE_PROXY_QUERY_ENDPOINT` / `LINE_PROXY_TARGET_AUDIENCE` 是否存在，缺一則回 500。
  5. 使用 `CloudRunAuthService` 取得 ID token，並帶上 `X-API-Key` 呼叫 Service B `/api/v1/query`：
     - 請求 body：`{"query": query_text, "top_k": LINE_PROXY_TOP_K}`。
     - 若 200：讀取 `answer = resp.json().get("answer")`。
  6. 以 INFO log 記錄：
     - `event_id, query_status, reply_enabled, reply_token_present, answer_present`。
  7. 若 `query_status == 200`：
     - 若 `answer` 为空：改用 fallback 文案。
     - 呼叫 `_line_reply(reply_token or "", reply_text)`。
  8. 統一回 200，附上 `forwarded` / `query_status` / `answer` / `reply_status` / `reply_detail`。

#### 2.5 測試（`tests/test_api/test_line_reply_webhook.py`）

- 自動注入測試預設設定（monkeypatch）：
  - 假的 `LINE_CHANNEL_SECRET`、`LINE_PROXY_*`、`LINE_REPLY_ENABLED=true`、`LINE_CHANNEL_ACCESS_TOKEN` 等。
- 兩個關鍵情境：
  - 簽章正確 + 上游 200：會同時呼叫 Service B `/api/v1/query` 與 LINE Reply API，並回 200，`forwarded=True`、`query_status=200`、`reply_status=200`。
  - Reply 失敗（模擬 500）：Webhook 仍回 200，`forwarded=True`、`reply_status=500`，只在 `reply_detail` 記錄錯誤。

---

### 3. Cloud Run / Secret Manager 設定

#### 3.1 Service Account

- Runtime SA：`441535054378-compute@developer.gserviceaccount.com`
  - 需具備：
    - `roles/run.invoker`（呼叫 B 時視設計，通常由 B 端 policy 控制）。
    - `roles/secretmanager.secretAccessor`：
      - `GOOGLE_API_KEY`
      - `LINE_CHANNEL_SECRET`
      - `LINE_PROXY_X_API_KEY`
      - `LINE_CHANNEL_ACCESS_TOKEN`

#### 3.2 Secret Manager Secrets

- `GOOGLE_API_KEY`：既有，用於 Gemini。
- `LINE_CHANNEL_SECRET`：
  - 值為 LINE Developers「Messaging API → Channel secret」。
- `LINE_PROXY_X_API_KEY`：
  - 與 Service B 的 `API_KEY` 一致（或專用 key），用於保護 `/api/v1/query`。
- `LINE_CHANNEL_ACCESS_TOKEN`：
  - 值為 Messaging API 的「Channel access token (long-lived)」。
  - 推薦透過：
    - 本機 `.env` 設 `LINE_CHANNEL_ACCESS_TOKEN=...`。
    - 以 `gcloud secrets create` + `versions add --data-file=-` 建立，但要避免尾端換行問題。

#### 3.3 Cloud Run Service A（care-rag-line-proxy）主要設定

- **Image**：
  - 由 Cloud Build 產出的 `care-rag-line-proxy:reply-YYYYMMDD-HHmm`。
- **Env（plain）**：
  - `LINE_REPLY_ENABLED=true`
  - `LINE_PROXY_QUERY_ENDPOINT=https://care-rag-api-<hash>.a.run.app/api/v1/query`
  - `LINE_PROXY_TARGET_AUDIENCE=https://care-rag-api-<hash>.a.run.app`
  - `LINE_WEBHOOK_REQUIRE_SIGNATURE=true`
- **Env（from Secret）**：
  - `GOOGLE_API_KEY=GOOGLE_API_KEY:latest`
  - `LINE_CHANNEL_SECRET=LINE_CHANNEL_SECRET:latest`
  - `LINE_PROXY_X_API_KEY=LINE_PROXY_X_API_KEY:latest`
  - `LINE_CHANNEL_ACCESS_TOKEN=LINE_CHANNEL_ACCESS_TOKEN:latest`

---

### 4. 部署步驟（SOP）

#### 4.1 先決條件

1. 本機 `gcloud` 已登入並選擇正確專案：
   - `gcloud auth login`
   - `gcloud config set project gen-lang-client-0567547134`
2. 本機 `.env`（不 commit）已填：
   - `LINE_CHANNEL_SECRET=...`
   - `LINE_PROXY_X_API_KEY=...`（或 `API_KEY`）
   - `LINE_CHANNEL_ACCESS_TOKEN=...`

#### 4.2 建立/更新 Secrets

（範例，以有本機 `.env` 為前提）

```powershell
# 建立 LINE_CHANNEL_ACCESS_TOKEN（若尚未存在）
$token = (Get-Content .env | Select-String '^LINE_CHANNEL_ACCESS_TOKEN=' | ForEach-Object { $_.Line.Split('=',2)[1] }).Trim()
echo $token | gcloud secrets create LINE_CHANNEL_ACCESS_TOKEN `
  --project gen-lang-client-0567547134 `
  --replication-policy=automatic `
  --data-file=-

# 若 secret 已存在，新增新版本：
echo $token | gcloud secrets versions add LINE_CHANNEL_ACCESS_TOKEN `
  --project gen-lang-client-0567547134 `
  --data-file=-

# 授權 runtime SA
gcloud secrets add-iam-policy-binding LINE_CHANNEL_ACCESS_TOKEN `
  --project gen-lang-client-0567547134 `
  --member="serviceAccount:441535054378-compute@developer.gserviceaccount.com" `
  --role="roles/secretmanager.secretAccessor"
```

其他 secrets（`LINE_CHANNEL_SECRET`、`LINE_PROXY_X_API_KEY`）流程相同。

#### 4.3 建置與部署 Service A

1. 使用 Cloud Build 建置 image：

```powershell
$ts  = (Get-Date).ToString('yyyyMMdd-HHmm')
$img = "asia-east1-docker.pkg.dev/gen-lang-client-0567547134/care-rag/care-rag-line-proxy:reply-$ts"
gcloud builds submit --project gen-lang-client-0567547134 --tag $img .
```

2. 部署到 Cloud Run：

```powershell
gcloud run deploy care-rag-line-proxy `
  --project gen-lang-client-0567547134 `
  --region asia-east1 `
  --image $img `
  --service-account 441535054378-compute@developer.gserviceaccount.com `
  --update-secrets `
    GOOGLE_API_KEY=GOOGLE_API_KEY:latest,`
    LINE_CHANNEL_SECRET=LINE_CHANNEL_SECRET:latest,`
    LINE_PROXY_X_API_KEY=LINE_PROXY_X_API_KEY:latest,`
    LINE_CHANNEL_ACCESS_TOKEN=LINE_CHANNEL_ACCESS_TOKEN:latest `
  --update-env-vars `
    LINE_REPLY_ENABLED=true,`
    LINE_PROXY_QUERY_ENDPOINT=https://care-rag-api-<hash>.a.run.app/api/v1/query,`
    LINE_PROXY_TARGET_AUDIENCE=https://care-rag-api-<hash>.a.run.app,`
    LINE_WEBHOOK_REQUIRE_SIGNATURE=true
```

> 注意：在 PowerShell 中，`--update-env-vars` 的多個 `key=value` 需要放在同一個參數字串中，避免被解析成錯誤的值。

---

### 5. Token 流程與過期處理（重要觀念）

#### 5.1 LINE Channel access token（`LINE_CHANNEL_ACCESS_TOKEN`）

- 來源：LINE Developers「Messaging API → Channel access token (long-lived)」。
- 用途：Service A 呼叫 **LINE Reply API** 時帶在 HTTP header：
  - `Authorization: Bearer <LINE_CHANNEL_ACCESS_TOKEN>`
- 特性：
  - 由 LINE 官方管理效期，屬長效 token，正常情況不需每次重新取得。
  - 每次在 Console 按 **Reissue** 之後，**舊 token 立即失效**，必須同步：
    - 更新本機 `.env` 中的 `LINE_CHANNEL_ACCESS_TOKEN`。
    - 重新寫入 Secret Manager 的 `LINE_CHANNEL_ACCESS_TOKEN` 新版本。
    - 確認 Cloud Run Service A 繼續掛載 `:latest` 版本。
- 實作細節：
  - 由於 Secret Manager 版本常會包含尾端換行，程式在 `_line_reply()` 中會先對 token 執行 `.strip()`，避免 `Authorization` header 因 `\r\n` 變成非法值。

#### 5.2 Service A → Service B 的 ID Token（Postman 與正式環境差異）

- **Postman 測試模式**（僅供人工測試 Service B）：
  - 開發者手動執行 `gcloud auth print-identity-token` 等指令，取得一顆 **短效 ID token**。
  - 再把這顆 token 貼到 Postman `Authorization: Bearer <token>` 裡呼叫 `https://care-rag-api-.../api/v1/query`。
  - 這種方式需要開發者自行注意 token 過期時間。

- **正式 LINE 流量下的模式（推薦，也是目前已實作的方式）**：
  - 不再使用「人工先簽一顆 ID token 再貼 header」的流程。
  - 由 Service A 程式碼在每次 webhook 進來、準備呼叫 Service B 之前自動產生 ID token：

```python
auth = CloudRunAuthService()
token = auth.get_id_token(
    target_audience=settings.LINE_PROXY_TARGET_AUDIENCE,
    invoker_service_account=settings.LINE_PROXY_INVOKER_SERVICE_ACCOUNT,
)
```

  - `CloudRunAuthService` 會根據當前執行身份（Cloud Run SA / ADC）透過 `google-auth` 每次現場簽發 **新的短效 ID token**。
  - Service A 呼叫 Service B 時 header：
    - `Authorization: Bearer <id_token>`
    - `X-API-Key: <LINE_PROXY_X_API_KEY 或 API_KEY>`

- 效果與風險控管：
  - ID token 的「過期時間」完全由程式與 `google-auth` 管理，不需要人工輪換。
  - 即使 Cloud Run 長時間運行，因為每次呼叫前都會重新 mint token，不會出現「使用已過期的 Postman token」的問題。

#### 5.3 要注意與維護的只有兩種 token

1. **LINE 端的 Channel access token**
   - 何時會失效：在 LINE Console 上 Reissue 時。
   - 處理方式：同步更新 `.env` + Secret Manager，重新部署或至少重新掛載 secrets。
2. **Service B 的 X-API-Key / API_KEY**
   - 儲存在 Secret Manager（`LINE_PROXY_X_API_KEY` 或 `API_KEY`）中。
   - 變更時需：
     - 同步更新 Service B 的驗證邏輯。
     - 更新 Service A 掛載的 secret 版本。

其餘 ID token 相關的過期與刷新，均由 Cloud Run + `google-auth` 自動處理，無須類似 Postman 的手動更新作業。

---

### 6. LINE Developers 設定

1. **Messaging API Channel**：
   - Webhook URL：
     - `https://care-rag-line-proxy-441535054378.asia-east1.run.app/api/v1/webhook/line/query`
   - Use webhook：**Enabled**（Verify 要成功）。
2. **LINE Official Account features**：
   - Auto-reply messages：**Disabled**
   - Greeting messages：**Disabled**
     - 避免官方招呼訊息蓋掉我們的 RAG 回覆。
3. 注意：
   - 每次在 LINE Developers Console 重新 `Reissue` Channel access token 後：
     - 必須同步更新本機 `.env` 與 Secret Manager 的 `LINE_CHANNEL_ACCESS_TOKEN` 版本。

---

### 7. 驗證步驟（本機 + 手機）

#### 6.1 健康檢查與簽章測試（本機）

- 健康檢查：

```powershell
Invoke-WebRequest `
  -Uri "https://care-rag-line-proxy-441535054378.asia-east1.run.app/api/v1/health/" `
  -Method GET
```

- 使用 Python 一行產生簽章並送測試 webhook（會走完整 A→B 流程與 Reply 嘗試）：

```powershell
python -c "import json,hmac,hashlib,base64,urllib.request; secret='YOUR_LINE_CHANNEL_SECRET'; body={'events':[{'type':'message','replyToken':'00000000000000000000000000000000','timestamp':1234567890,'source':{'type':'user','userId':'U123'},'message':{'type':'text','id':'1','text':'查詢掛號紀錄'}}]}; raw=json.dumps(body,separators=(',',':'),ensure_ascii=False).encode('utf-8'); sig=base64.b64encode(hmac.new(secret.encode('utf-8'),raw,hashlib.sha256).digest()).decode('utf-8'); url='https://care-rag-line-proxy-441535054378.asia-east1.run.app/api/v1/webhook/line/query'; req=urllib.request.Request(url,data=raw,headers={'Content-Type':'application/json','X-Line-Signature':sig},method='POST'); import sys; 
try:
  resp=urllib.request.urlopen(req,timeout=30); print('HTTP',resp.status); print(resp.read().decode('utf-8'))
except Exception as e:
  import urllib.error; 
  if hasattr(e,'code'):
    print('HTTP',e.code); print(e.read().decode('utf-8'))
  else:
    print('ERR',type(e).__name__,str(e))"
```

> 測試用 `replyToken="0000..."` 並不會真的被 LINE 接受，預期 Reply API 回 `400 Invalid reply token`；此時主要確認 A→B 與 Reply 呼叫路徑正常。

#### 6.2 手機 E2E 測試

1. 手機加入 LINE 官方帳號並開啟聊天室。
2. 傳送訊息（例如：「查詢掛號紀錄」）。
3. 預期：
   - 聊天室收到由 RAG 生成的回答（來自 `answer` 欄位）。
   - LINE 官方的 Auto-reply/Greeting 已關閉，不會出現固定招呼文案。
4. 若無回覆或異常：
   - 使用：

```powershell
gcloud run services logs read care-rag-line-proxy `
  --project gen-lang-client-0567547134 `
  --region asia-east1 `
  --limit 80
```

   - 檢查：
     - `LINE webhook processed event_id=... query_status=... reply_token_present=... answer_present=...`
     - `reply_status` / `reply_detail` 是否為 401/403/400，以對應 token/權限問題。

---

此文件作為 LINE@ 整合與 Cloud Run 部署的 SOP，若未來調整 Service A/B 的路由、SA、或 LINE 設定，請同步更新本文件與 `dev_readme.md` 的更新歷史。 

