# 將 gcloud 取 Token 轉 Python 的實作計畫

更新時間：2026-03-27 13:51  
作者：Care RAG API 文件維護  
摘要：Cloud Run IAM 以 Python（方案 B：Impersonated Credentials + ID token）取代 CLI；含 ADC／WIF（CI/Prod）、雙 SA 排錯指令清單與驗證矩陣。與 Cursor 計畫檔同步時，以本 repo 路徑為準。

相關文件：[get-id-token-for-postman.md](get-id-token-for-postman.md)、[cloud-run-troubleshooting-summary.md](cloud-run-troubleshooting-summary.md)

---

## 目標

把以下 CLI 能力等價轉為 Python：以指定服務帳號 impersonation，產生 audience 指向 Cloud Run URL 的 ID token，供 `Authorization: Bearer <token>` 使用。

## 已決策

- 採用方案B：Python 使用 Google Auth API 做「Impersonated Credentials + ID Token」。
- 方案A（subprocess gcloud）保留為除錯 fallback，不作為主流程。

## 方案比較（保留紀錄）

- 方案A（維持現狀 + 最快）：Python 內呼叫 `gcloud` 子程序取得 token。
  - 優點：與目前 CLI 行為完全一致、最快驗證。
  - 風險：依賴本機 gcloud、環境耦合高。
- 方案B（建議）：Python 使用 Google Auth API 做「Impersonated Credentials + ID Token」。
  - 優點：無需 shell 依賴、可部署於 CI/服務端、可測試性較佳。
  - 風險：需要正確 IAM 權限與較完整錯誤處理。

## 方案B 詳細設計（主流程）

### 1) 前置條件與權限

- 目標 SA：`441535054378-compute@developer.gserviceaccount.com`。
- 呼叫者身分（本機 ADC 對應帳號）需具備：
  - 對目標 SA 的 `roles/iam.serviceAccountTokenCreator`（允許 impersonation 產 token）。
  - Cloud Run 服務可呼叫權限（建議授予目標 SA `roles/run.invoker`）。
- 本機需有 ADC（`gcloud auth application-default login`）或執行環境原生工作負載身分。

### 1.1) 權限由他人管理時（你不是專案管理員）

- 核心觀念：你本機登入的是「使用者身分」，真正呼叫 Cloud Run 的是「被 impersonate 的 SA」。
- 因此需要兩段授權由管理員完成：
  - 授權你（使用者帳號）可對目標 SA 做 token 代簽：`roles/iam.serviceAccountTokenCreator`（綁在 SA 上）。
  - 授權目標 SA 可呼叫 Cloud Run：`roles/run.invoker`（綁在 Cloud Run service 或 project）。
- 你自己只需完成：
  - `gcloud auth application-default login`（建立本機 ADC）。
  - Python 端使用 ADC + impersonation 取得 ID token。
- 身分驗證責任切分：
  - Google 會驗證「你是否可 impersonate SA」。
  - Cloud Run 會驗證「該 SA 的 ID token 是否對應正確 audience 且具 invoker 權限」。

### 1.2) 提供管理員的最小授權清單（可貼給對方）

- 對象：
  - User principal：`<your_user>@<company.com>`
  - Target SA：`441535054378-compute@developer.gserviceaccount.com`
  - Cloud Run service：`care-rag-api-441535054378`（依實際名稱為準）
- 需完成：
  - 將 `roles/iam.serviceAccountTokenCreator` 授予 user principal（resource = Target SA）。
  - 將 `roles/run.invoker` 授予 Target SA（resource = Cloud Run service）。
- 驗證完成標準：
  - 你可成功取得 ID token（Python refresh 成功，非 permission denied）。
  - 呼叫 `/api/v1/health/` 非 `invalid_token`。
  - 呼叫 `/api/v1/query` 不再被 Google Frontend 401 擋下。

### 1.3) 是否可免 `gcloud login` 的決策（新增）

- 結論：
  - 在本機開發情境，通常仍需某種初始身分來源（ADC login、WIF、或金鑰），無法「只給 SA 權限就自動可用」。
  - 在 GCP 執行環境或 CI OIDC，可不依賴 `gcloud login` 互動登入。
- 三種身分來源比較：
  - ADC 使用者登入（`gcloud auth application-default login`）
    - 優點：最快上手、除錯便利、不需落地 SA 金鑰。
    - 缺點：依賴個人登入狀態，不利全自動化一致性。
  - SA 金鑰 JSON（不建議）
    - 優點：可完全不互動登入。
    - 缺點：高外洩風險、需輪替治理，常違反企業資安基準。
  - Workload Identity / Federation（建議用於 CI/Prod）
    - 優點：無長期金鑰、可審計、最符合雲原生安全實務。
    - 缺點：初始設定較複雜（pool/provider/綁定）。
- 環境建議：
  - Dev（本機）：優先 ADC login + impersonation。
  - CI/CD：優先 Workload Identity Federation + impersonation（若需跨 SA）。
  - Prod（GCP 服務內）：優先使用執行環境原生工作負載身分。

### 1.4) 雙 SA 逐步檢查指令清單（排錯優先）

先替換以下變數，再依序執行。建議先完成 1~4，再做 Python 呼叫，避免把 IAM 問題誤判成程式問題。

```bash
PROJECT_ID="gen-lang-client-0567547134"
PROJECT_NUMBER="441535054378"
POOL_ID="github-actions-pool"
PROVIDER_ID="github-oidc"
GITHUB_ORG="your-org"
GITHUB_REPO="care_rag_api"
WIF_SA_EMAIL="ci-wif@${PROJECT_ID}.iam.gserviceaccount.com"
INVOKER_SA_EMAIL="441535054378-compute@developer.gserviceaccount.com"
CLOUD_RUN_SERVICE="care-rag-api-441535054378"
CLOUD_RUN_REGION="asia-east1"
CLOUD_RUN_URL="https://care-rag-api-441535054378.asia-east1.run.app"
```

1) 檢查 Provider 是否存在、issuer 是否正確：

```bash
gcloud iam workload-identity-pools providers describe "${PROVIDER_ID}" \
  --project="${PROJECT_ID}" \
  --location=global \
  --workload-identity-pool="${POOL_ID}" \
  --format="yaml(name,oidc.issuerUri,attributeMapping,attributeCondition)"
```

- 預期：`issuerUri` 為 `https://token.actions.githubusercontent.com`，且 mapping/condition 符合設定。
- 失敗解讀：Provider 不存在或 issuer 錯，先修 Provider。

2) 檢查 `roles/iam.workloadIdentityUser` 是否綁到正確 principalSet：

```bash
gcloud iam service-accounts get-iam-policy "${WIF_SA_EMAIL}" \
  --project="${PROJECT_ID}" \
  --format="yaml(bindings)"
```

- 預期 member 包含：  
  `principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/attribute.repository/${GITHUB_ORG}/${GITHUB_REPO}`
- 失敗解讀：member 路徑 typo、專案號錯、repo 不符會導致 CI 無法換到 WIF_SA。

3) 檢查 `WIF_SA -> INVOKER_SA` 的 TokenCreator：

```bash
gcloud iam service-accounts get-iam-policy "${INVOKER_SA_EMAIL}" \
  --project="${PROJECT_ID}" \
  --format="yaml(bindings)"
```

- 預期：`roles/iam.serviceAccountTokenCreator` 內有 `serviceAccount:${WIF_SA_EMAIL}`。
- 失敗解讀：缺此綁定時，Python impersonation 會報 `iam.serviceAccounts.getAccessToken denied`。

4) 檢查 `INVOKER_SA` 是否具 Cloud Run Invoker（服務級）：

```bash
gcloud run services get-iam-policy "${CLOUD_RUN_SERVICE}" \
  --project="${PROJECT_ID}" \
  --region="${CLOUD_RUN_REGION}" \
  --format="yaml(bindings)"
```

- 預期：`roles/run.invoker` 內有 `serviceAccount:${INVOKER_SA_EMAIL}`。
- 失敗解讀：缺綁定時，就算 token 可簽，也會在 Cloud Run 邊界回 403。

5) 檢查 audience 與 URL 一致性（人工）：

- `target_audience` 必須完全等於 `${CLOUD_RUN_URL}`。
- 不可用 API path（如 `/api/v1/query`）當 audience。
- 不可多尾斜線、不可使用 HTTP。

### 2) Python 模組與介面定義

- 建議拆 2 個函式：
  - `build_cloud_run_id_token_provider(target_service_account: str, audience: str) -> Callable[[], str]`
  - `get_cloud_run_id_token(target_service_account: str, audience: str) -> str`
- 參數：
  - `target_service_account`：`...@developer.gserviceaccount.com`
  - `audience`：`https://care-rag-api-441535054378.asia-east1.run.app`
- 回傳：
  - 僅回傳 token 字串（不含 `Bearer` ）。
- 例外分類（至少）：
  - `ImpersonationPermissionError`：缺少 TokenCreator。
  - `InvalidAudienceError`：audience 非 URL 或與目標服務不一致。
  - `TokenFetchTransientError`：短暫性網路或 Google API 錯誤（可重試）。

### 3) Token 取得流程（程式邏輯）

- Step A：`google.auth.default()` 讀取 source credentials 與 project。
- Step B：建立 impersonated credentials（目標 principal 為目標 SA）。
- Step C：基於 impersonated credentials 建 `IDTokenCredentials`，指定 `target_audience=audience`。
- Step D：`refresh(Request())` 取得 access token 欄位中的 ID token。
- Step E：回傳 token 並做安全化日誌（只顯示前 20 碼與長度）。

### 3.1) 與你提問對應的驗證邏輯（permission by another）

- 若 Step D 報 `Permission iam.serviceAccounts.getAccessToken denied`：
  - 代表管理員尚未給你 `Service Account Token Creator`。
- 若 token 取得成功但 API 回 403：
  - 代表目標 SA 尚未有 `run.invoker`。
- 若 API 回 401 `invalid_token`：
  - 代表 token 類型/簽發者/`audience` 不符（常見是 audience 錯或混用 APIM token）。

### 4) 與 query client 串接規格

- `Authorization` 一律由 helper 產生：`Bearer <cloud_run_id_token>`。
- `X-API-Key` 保留給應用層驗證，不影響 Cloud Run IAM 邊界驗證順序。
- `target_url` 與 token 的 `audience` 強制同源（同一服務根 URL），避免環境變數誤配。
- 明確命名：`cloud_run_id_token` 與 `apim_access_token` 完全分離，杜絕混用。

### 5) 可靠性與安全

- 不記錄完整 token、不可寫入持久檔案。
- token 快取可選（依 `exp` 提前 60 秒刷新），避免每次呼叫都 refresh。
- 對 `429/5xx` 的 token 端錯誤採指數退避重試（最多 2-3 次）。
- 針對 401 回應解析：
  - `invalid_token`（Google Frontend）=> token 類型/簽發者/受眾錯誤。
  - 非 Google Frontend JSON 401 => 應用層授權問題（進入 API 後）。

### 6) Workload Identity Federation（CI/Prod）— 實作重點（審查補強）

此節對應 1.3「WIF 優缺點」：**如何把 pool/provider/綁定落地**，讓 Python 仍走方案 B（external account → 可選 impersonate → `IDTokenCredentials`）。

#### 6.1 概念（一句話）

- 外部系統（例如 **GitHub Actions OIDC**、Azure AD、Okta）先簽發 **短期 OIDC JWT**。
- GCP 建立 **Workload Identity Pool + Provider**，信任該 issuer，並用 **attribute mapping** 把 claims 對應成可綁 IAM 的 principal。
- 將 **某個 GCP 服務帳號** 授權給該 principal（常見 `roles/iam.workloadIdentityUser`），則 CI 執行時可 **以聯合身分換成該 SA**，再依計畫 3) 產 Cloud Run **ID token**（必要時再 impersonate 另一個「僅 Invoker」的 SA）。

#### 6.2 GCP 端需建立的資源（順序建議）

1. **Workload Identity Pool**（專案、location 通常 `global`）。
2. **Workload Identity Provider**（OIDC）：
   - 設定 **issuer URL**（例：GitHub `https://token.actions.githubusercontent.com`）。
   - **Audience** 須與 CI 發 OIDC 時設定的 `aud` 一致（GitHub 常見為 `https://github.com/OWNER/REPO` 或由 Actions 產生的受控值，依官方文件為準）。
   - **Attribute mapping**：把 OIDC claims（如 `sub`、`repository`、`ref`）映射到 Google 可引用的屬性，供下一步綁定縮小範圍。
3. **IAM 綁定（關鍵）**：
   - 選定一個 **GCP 服務帳號** 作為 CI 在 GCP 的身分（下稱 `WIF_SA`）。
   - 對 `WIF_SA` 授予 **Workload Identity User** 給 **principalSet** 或 **principal**（用 attribute 限制到單一 repo/branch，避免過寬）。
   - 若仍需與現有 **Invoker SA**（如 `441535054378-compute@...`）分離：讓 `WIF_SA` 具備對目標 SA 的 `roles/iam.serviceAccountTokenCreator`，Python 內 **impersonate** 目標 SA 再取 ID token（與本機 ADC 路徑相同，僅 **source credentials 來源**改為 WIF）。

#### 6.3 CI 端（以 GitHub Actions 為例）

- 在 workflow 啟用 **OIDC**（`permissions: id-token: write`），由 Actions 提供 **短期 id-token**。
- **不要**把 GCP 長期金鑰放 Secrets；改以 **WIF 憑證 JSON** 或 **google-github-actions/auth** 等官方 Action 完成「OIDC → GCP ADC」。
- 成功後，執行環境內 `GOOGLE_APPLICATION_CREDENTIALS` 或 Action 注入的 credentials 即為 **external account** 類型。

#### 6.4 Python 實作如何接上（與 §3 對齊）

- **Step A'**（取代僅 ADC）：`google.auth.default()` 若讀到 **external account**（WIF 產生的憑證檔），即為合法 source credentials。
- **Step B～E**：與 §3 相同 — `impersonated_credentials`（若需）→ `IDTokenCredentials(target_audience=Cloud Run URL)` → `refresh` → Bearer。
- 產生本機/CI 用的憑證描述檔（管理員執行一次，產出 JSON 供 CI 使用）可用：
  `gcloud iam workload-identity-pools create-cred-config ...`
  參數需對應 pool、provider、**service account**（要冒充進 GCP 的那個 SA）。細節以當前 `gcloud` 文件為準。

#### 6.5 與「GCP 內 Prod」差異

- **Prod 服務已在 GCE/GKE/Cloud Run**：通常直接用 **附掛的 metadata SA**，無需 WIF；WIF 主要解 **GCP 外的 CI / 多雲**。
- **Prod 在別雲 VM**：才需要 WIF 或 VPN + 其他身分模式。

#### 6.6 常見失敗與除錯

| 現象 | 可能原因 |
|------|----------|
| `invalid_grant` / audience mismatch | Provider audience 與 CI OIDC 的 `aud` 不一致 |
| `Permission denied` on pool | Provider issuer / mapping 錯誤或 principal 綁定過嚴 |
| `workloadIdentityUser` 仍無法冒充 SA | 綁定 member 寫錯（principalSet 路徑）或漏綁 `WIF_SA` |
| Cloud Run 401 `invalid_token` | 與本機相同：Bearer 不是 Google ID token 或 audience 非服務 URL |

#### 6.7 實作驗收（WIF 專用）

- CI job 內 **無** `gcloud auth login`、**無** SA 金鑰檔，仍可 `refresh` 成功並呼叫 `/api/v1/health/` 200。
- 變更 repo 或 workflow 未授權時，**應無法**取得 GCP 憑證或無法冒充 SA（負向測試）。

## 驗證計畫（細化）

### 驗證矩陣

- Case 1：正確 SA + 正確 audience
  - `/api/v1/health/` 預期 200。
  - `/api/v1/query` 預期 200（或應用層可預期錯誤，但不應是 Google Frontend `invalid_token`）。
- Case 2：正確 SA + 錯誤 audience
  - 預期 401，且 `www-authenticate` 含 `invalid_token`。
- Case 3：無 TokenCreator 權限
  - 預期 token 取得階段失敗（Python 例外），不會進到 API 呼叫。
- Case 4：無 Run Invoker
  - 預期 403（Cloud Run IAM 拒絕）。

### 驗收標準（Definition of Done）

- Python 不依賴 subprocess gcloud 也可成功取得 ID token。
- `/api/v1/query` 不再出現 Google Frontend `invalid_token`（在正確權限前提下）。
- 錯誤分流可由日誌快速判定是 IAM、audience、或應用層問題。
- 文件具備最小操作步驟與常見錯誤對照。

## 你截圖程式需特別確認的點

- `target_url` 與 fetch token 的 `target_audience` 必須一致（建議直接都用同一個服務根 URL）。
- 保留 `X-API-Key` 可行，但 IAM 驗證先於應用層，先確保 Bearer 正確。
- 不要混用 APIM JWT 與 Cloud Run ID token 變數名稱（建議拆成 `cloud_run_id_token`）。

## 交付內容（下一步執行時）

- 一個可重用的 Python token helper。
- 一段最小可執行範例（取得 token + 呼叫 `/api/v1/query`）。
- 錯誤訊息對照說明（401/403/5xx）。
- 權限檢查清單（誰要有 TokenCreator、誰要有 Run Invoker）。
