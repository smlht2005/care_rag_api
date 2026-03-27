# Care RAG API Cloud Run IAM — Postman 使用說明

更新時間：2026-03-27 09:10

## 檔案

| 檔案 | 用途 |
|------|------|
| `Care_RAG_API_CloudRun_IAM.postman_collection.json` | Collection（Health、Query） |
| `Care_RAG_API_CloudRun_IAM.postman_environment.json` | Environment（`baseUrl`、`bearerToken`、`xApiKey`） |

## 匯入步驟

1. Postman → **Import** → 選上述兩個 JSON 檔（可一次選兩個）。
2. 右上角 **Environment** 下拉選 **`Care RAG API - Cloud Run IAM`**。
3. 點選環境右側 **眼睛圖示** → **Edit**，在 **`bearerToken`** 貼上 ID token（見下方「取得 token」）。
4. 確認 `baseUrl`、`xApiKey` 與你的部署一致後，執行 **Health (IAM only)** 再執行 **Query (IAM + X-API-Key)**。

## 取得 `bearerToken`（Windows CMD）

Cloud Run 為 **IAM only**，必須帶 Google **ID token**。以下以 service account impersonation 為例（與專案實測一致）：

```bat
set URL=https://care-rag-api-441535054378.asia-east1.run.app
set SA=441535054378-compute@developer.gserviceaccount.com
for /f "delims=" %T in ('gcloud auth print-identity-token --audiences=%URL% --impersonate-service-account=%SA%') do set TOKEN=%T
echo %TOKEN%
```

- 將 `echo` 印出的**整串**（以 `eyJ` 開頭）複製到 Postman 環境變數 **`bearerToken`**（不要含 `Bearer ` 前綴，Collection 已寫 `Bearer {{bearerToken}}`）。
- Token 會過期，約 1 小時內需重新執行上述指令再貼一次。

## 取得 `bearerToken`（Python）

### 建議：Python 一行（Windows 相容，使用 `shutil.which`）

**根因**：`subprocess.check_output(['gcloud', ...])` 在 Windows 上常出現 **`FileNotFoundError: WinError 2`**，因為 `CreateProcess` 找不到名為 `gcloud` 的執行檔（實際常為 `gcloud.cmd`）。請先解析完整路徑再呼叫：

```bat
python -c "import subprocess,shutil; g=shutil.which('gcloud') or shutil.which('gcloud.cmd'); print(subprocess.check_output([g,'auth','print-identity-token','--audiences=https://care-rag-api-441535054378.asia-east1.run.app','--impersonate-service-account=441535054378-compute@developer.gserviceaccount.com'], text=True).strip())"
```

若 `g` 為 `None`，仍請改用 **CMD 的 `for /f` 方式**（本文件上一節）。

### 替代：一行（`shell=True`，與 CMD 手打 `gcloud` 相同）

```bat
python -c "import subprocess; print(subprocess.check_output('gcloud auth print-identity-token --audiences=https://care-rag-api-441535054378.asia-east1.run.app --impersonate-service-account=441535054378-compute@developer.gserviceaccount.com', shell=True, text=True).strip())"
```

前提與 CMD 相同：已 `gcloud auth login`，且具備 **TokenCreator**、該 SA 具 **run.invoker**。

## 權限前置（若 401/403）

- 你的 Google 帳號需能 **impersonate** 該 SA：`roles/iam.serviceAccountTokenCreator`。
- 該 SA 需能呼叫 Cloud Run：`roles/run.invoker`（綁在 `care-rag-api` 服務上）。

詳見 `docs/gcp_deployment/cloud-run-troubleshooting-summary.md`。

## 變數對照

| 變數 | 說明 |
|------|------|
| `baseUrl` | Cloud Run 服務根 URL（無尾斜線） |
| `bearerToken` | 僅 token 字串，不含 `Bearer ` |
| `xApiKey` | 應用層 `X-API-Key`，預設 `test-api-key`（與 `app/config.py` 一致時） |
